"""Format or validate both OpenTofu roots without accessing remote backends."""

from __future__ import annotations

import argparse
import os
import subprocess
import tempfile
from pathlib import Path

from infra_common import RUNTIME, TOFU, WORKSPACE, resolve

ROOTS = (WORKSPACE / "foundation", WORKSPACE / "administration" / "aws_account")


def execute(command: list[str], directory: Path, env: dict[str, str]) -> int:
    """Run one command and return its exit status."""
    print(f"==> {directory.relative_to(WORKSPACE)}: {' '.join(command)}", flush=True)
    try:
        return subprocess.run(command, cwd=directory, env=env, check=False).returncode
    except OSError as error:
        print(f"Unable to run OpenTofu: {error}", flush=True)
        return 1


def main() -> int:
    """Format, check formatting, or validate both infrastructure roots."""
    parser = argparse.ArgumentParser(description=__doc__)
    modes = parser.add_mutually_exclusive_group(required=True)
    modes.add_argument("--format", action="store_const", const="format", dest="mode")
    modes.add_argument("--check-only", action="store_const", const="check", dest="mode")
    modes.add_argument("--validate", action="store_const", const="validate", dest="mode")
    mode = parser.parse_args().mode

    tofu = resolve(TOFU)
    if tofu is None:
        return 1

    for directory in ROOTS:
        env = os.environ.copy()
        env["TF_IN_AUTOMATION"] = "true"
        if mode != "validate":
            command = [tofu, "fmt", "-recursive"]
            if mode == "check":
                command.append("-check")
            result = execute(command, directory, env)
        else:
            runtime = RUNTIME / "tofu" / "data"
            cache = RUNTIME / "tofu" / "providers"
            runtime.mkdir(parents=True, exist_ok=True)
            cache.mkdir(parents=True, exist_ok=True)
            env["TF_PLUGIN_CACHE_DIR"] = str(cache)
            with tempfile.TemporaryDirectory(prefix="tofu-data-", dir=runtime) as data:
                env["TF_DATA_DIR"] = data
                result = execute(
                    [
                        tofu, "init", "-backend=false", "-lockfile=readonly",
                        "-input=false", "-no-color",
                    ],
                    directory,
                    env,
                )
                if result == 0:
                    result = execute([tofu, "validate", "-no-color"], directory, env)
        if result != 0:
            return result

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
