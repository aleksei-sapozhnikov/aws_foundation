"""Install pinned OpenTofu and TFLint releases into the ignored .local directory."""

from __future__ import annotations

import hashlib
import platform
import re
import shutil
import subprocess
import sys
import tempfile
import urllib.request
import warnings
import zipfile
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path

WORKSPACE = Path(__file__).resolve().parents[2]
RUNTIME = WORKSPACE / ".local" / "qa-runtime"


@dataclass(frozen=True)
class Tool:
    """Describe an official release and its checksum manifest."""

    name: str
    version: str
    repository: str
    checksums: str
    asset_prefix: str
    version_prefix: str
    unsupported_platform: tuple[str, str] | None = None


TOFU = Tool(
    name="tofu",
    version="1.13.1",
    repository="opentofu/opentofu",
    checksums="tofu_1.13.1_SHA256SUMS",
    asset_prefix="tofu_1.13.1",
    version_prefix="OpenTofu v",
)
TFLINT = Tool(
    name="tflint",
    version="0.65.0",
    repository="terraform-linters/tflint",
    checksums="checksums.txt",
    asset_prefix="tflint",
    version_prefix="TFLint version ",
    unsupported_platform=("windows", "arm64"),
)


def host_platform() -> tuple[str, str]:
    """Map the host to official release asset names."""
    system = {"win32": "windows", "linux": "linux", "darwin": "darwin"}.get(
        sys.platform
    )
    architecture = {
        "amd64": "amd64",
        "x86_64": "amd64",
        "aarch64": "arm64",
        "arm64": "arm64",
    }.get(platform.machine().lower())
    if system is None or architecture is None:
        raise ValueError(f"Unsupported platform: {sys.platform}/{platform.machine()}")
    return system, architecture


def matches_version(binary: Path, tool: Tool) -> bool:
    """Check the version of a cached executable before reusing it."""
    try:
        result = subprocess.run(
            [str(binary), "--version"],
            check=False,
            capture_output=True,
            text=True,
            timeout=15,
        )
    except (OSError, subprocess.TimeoutExpired):
        return False
    return result.returncode == 0 and re.search(
        re.escape(tool.version_prefix + tool.version) + r"(?:\s|$)",
        result.stdout,
    ) is not None


@contextmanager
def open_release_url(url: str, timeout: int):
    """Use normal TLS verification and skip only malformed Windows store warnings."""
    with warnings.catch_warnings():
        if sys.platform == "win32":
            # Python already skips malformed CA entries; HTTPS verification remains on.
            warnings.filterwarnings(
                "ignore",
                message=r"^Bad certificate in Windows certificate store:",
                category=UserWarning,
                module=r"^ssl$",
            )
        with urllib.request.urlopen(url, timeout=timeout) as response:
            yield response


def download_tool(tool: Tool, target: Path, system: str, arch: str) -> None:
    """Download an official ZIP, verify SHA-256 and extract the executable."""
    asset = f"{tool.asset_prefix}_{system}_{arch}.zip"
    base = f"https://github.com/{tool.repository}/releases/download/v{tool.version}/"

    with open_release_url(base + tool.checksums, timeout=30) as response:
        manifest = response.read().decode("utf-8")
    checksum = next(
        (
            columns[0]
            for line in manifest.splitlines()
            if len(columns := line.split()) == 2
            and columns[1].lstrip("*") == asset
        ),
        None,
    )
    if checksum is None or re.fullmatch(r"[a-fA-F0-9]{64}", checksum) is None:
        raise ValueError(f"Missing SHA-256 for {asset}")

    target.parent.mkdir(parents=True, exist_ok=True)
    print(f"Downloading {tool.name} {tool.version} to {target.parent}", flush=True)
    with tempfile.TemporaryDirectory(prefix="download-", dir=target.parent) as tmp:
        archive_path = Path(tmp) / asset
        with (
            open_release_url(base + asset, timeout=90) as response,
            archive_path.open("wb") as output,
        ):
            shutil.copyfileobj(response, output)
        digest = hashlib.sha256(archive_path.read_bytes()).hexdigest()
        if digest.lower() != checksum.lower():
            raise ValueError(f"SHA-256 mismatch for {asset}")

        executable = Path(tmp) / target.name
        with (
            zipfile.ZipFile(archive_path) as archive,
            archive.open(target.name) as source,
            executable.open("wb") as output,
        ):
            shutil.copyfileobj(source, output)
        if system != "windows":
            executable.chmod(0o755)
        executable.replace(target)


def resolve(tool: Tool) -> str | None:
    """Return a pinned, locally installed binary, bootstrapping if necessary."""
    try:
        system, arch = host_platform()
        if tool.unsupported_platform == (system, arch):
            raise ValueError(f"Unsupported release platform: {system}/{arch}")
        target = (
            RUNTIME / tool.name / tool.version / f"{system}_{arch}"
            / (tool.name + (".exe" if system == "windows" else ""))
        )
        if not matches_version(target, tool):
            download_tool(tool, target, system, arch)
        if not matches_version(target, tool):
            raise ValueError(f"Installed {tool.name} version is not {tool.version}")
        return str(target)
    except (OSError, ValueError, zipfile.BadZipFile) as error:
        print(f"Unable to prepare {tool.name} {tool.version}: {error}", flush=True)
        return None
