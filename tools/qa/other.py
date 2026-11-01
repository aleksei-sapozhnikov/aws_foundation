"""Check and normalize whitespace, line endings, conflicts, JSON and YAML."""

from __future__ import annotations

import argparse
import importlib
import json
import re
import subprocess
import sys
from pathlib import Path

from infra_common import RUNTIME, WORKSPACE

CONFLICT = re.compile(r"(?m)^(<<<<<<< .+|=======|>>>>>>> .+)$")
LARGE_FILE_LIMIT = 500 * 1024
YAML_VERSION = "6.0.3"


def repository_files() -> list[Path]:
    """Find tracked and non-ignored untracked files, omitting symlinks."""
    result = subprocess.run(
        ["git", "ls-files", "-z", "--cached", "--others", "--exclude-standard"],
        cwd=WORKSPACE,
        capture_output=True,
        check=True,
    )
    paths = []
    for raw in result.stdout.split(b"\0"):
        if not raw:
            continue
        path = WORKSPACE / raw.decode("utf-8", errors="surrogateescape")
        if path.is_file() and not path.is_symlink():
            paths.append(path)
    return sorted(set(paths))


def normalize(text: str) -> str:
    """Use LF, remove trailing whitespace, and ensure one final newline."""
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = "".join(
        line.rstrip("\n").rstrip(" \t") + ("\n" if line.endswith("\n") else "")
        for line in text.splitlines(keepends=True)
    )
    stripped = text.rstrip("\n")
    return stripped + "\n" if stripped else ""


def issues(text: str) -> list[str]:
    """Report text-formatting issues without changing the file."""
    errors = []
    if "\r" in text:
        errors.append("non-LF line endings")
    for line_number, line in enumerate(text.splitlines(), start=1):
        if line.endswith((" ", "\t")):
            errors.append(f"{line_number}: trailing whitespace")
    if text and not text.endswith("\n"):
        errors.append("missing final newline")
    elif text.endswith("\n\n"):
        errors.append("more than one final newline")
    if CONFLICT.search(text):
        errors.append("unresolved merge conflict markers")
    return errors


def yaml_parser():
    """Install the pinned PyYAML dependency into ignored local tools if needed."""
    target = RUNTIME / "python"
    target.mkdir(parents=True, exist_ok=True)
    sys.path.insert(0, str(target))
    try:
        import yaml
        if yaml.__version__ == YAML_VERSION:
            return yaml
    except ImportError:
        pass

    result = subprocess.run(
        [
            sys.executable, "-m", "pip", "install",
            "--disable-pip-version-check", "--no-input", "--upgrade",
            "--target", str(target), f"PyYAML=={YAML_VERSION}",
        ],
        check=False,
    )
    if result.returncode != 0:
        raise RuntimeError("Unable to install pinned PyYAML")
    # Clear cached module lookup results after installing into a local directory.
    importlib.invalidate_caches()
    # Reload after installation (or upgrading an older local version).
    for name in list(sys.modules):
        if name == "yaml" or name.startswith("yaml."):
            del sys.modules[name]
    import yaml
    if yaml.__version__ != YAML_VERSION:
        raise RuntimeError("Installed PyYAML version does not match")
    return yaml


def main() -> int:
    """Check files, or fix only whitespace and newline issues."""
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--check-only", action="store_true")
    mode.add_argument("--format", action="store_true")
    args = parser.parse_args()

    try:
        files = repository_files()
    except (OSError, subprocess.CalledProcessError) as error:
        print(f"Unable to list Git files: {error}")
        return 1

    invalid = False
    yaml_files = []
    for path in files:
        relative = path.relative_to(WORKSPACE)
        try:
            raw = path.read_bytes()
        except OSError as error:
            print(f"{relative}: {error}")
            invalid = True
            continue
        if len(raw) > LARGE_FILE_LIMIT:
            print(f"{relative}: file exceeds 500 KiB")
            invalid = True
        if b"\0" in raw:
            continue
        try:
            text = raw.decode("utf-8")
        except UnicodeDecodeError:
            continue

        if args.format:
            fixed = normalize(text)
            if fixed != text:
                path.write_bytes(fixed.encode("utf-8"))
                text = fixed
                print(f"{relative}: normalized whitespace and line endings")
        for error in issues(text):
            print(f"{relative}: {error}")
            invalid = True

        if path.suffix.lower() == ".json":
            try:
                json.loads(text)
            except json.JSONDecodeError as error:
                print(f"{relative}: invalid JSON: {error}")
                invalid = True
        elif path.suffix.lower() in {".yaml", ".yml"}:
            yaml_files.append((relative, text))

    if yaml_files:
        try:
            yaml = yaml_parser()
        except (OSError, RuntimeError) as error:
            print(f"YAML validation unavailable: {error}")
            return 1
        for relative, text in yaml_files:
            try:
                list(yaml.safe_load_all(text))
            except yaml.YAMLError as error:
                print(f"{relative}: invalid YAML: {error}")
                invalid = True

    return 1 if invalid else 0


if __name__ == "__main__":
    raise SystemExit(main())
