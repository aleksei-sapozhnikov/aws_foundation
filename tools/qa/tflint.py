"""Lint both OpenTofu roots with the repository-wide TFLint policy."""

from __future__ import annotations

import argparse
import os
import subprocess
import tempfile
from pathlib import Path

from infra_common import RUNTIME, TFLINT, WORKSPACE, resolve

ROOTS = (WORKSPACE / "foundation", WORKSPACE / "administration" / "aws_account")


def execute(command: list[str], directory: Path, env: dict[str, str]) -> int:
    """Run TFLint and return its exit status."""
    print(f"==> {directory.relative_to(WORKSPACE)}: {' '.join(command)}", flush=True)
    try:
        return subprocess.run(command, cwd=directory, env=env, check=False).returncode
    except OSError as error:
        print(f"Unable to run TFLint: {error}", flush=True)
        return 1


def main() -> int:
    """Initialize plugins and lint both infrastructure roots."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--lint", action="store_true", required=True)
    parser.parse_args()

    tflint = resolve(TFLINT)
    if tflint is None:
        return 1

    runtime = RUNTIME / "tflint"
    plugins = runtime / "plugins"
    plugins.mkdir(parents=True, exist_ok=True)
    env = os.environ.copy()
    env["TF_IN_AUTOMATION"] = "true"
    env["TFLINT_DISABLE_VERSION_CHECK"] = "1"
    env["TFLINT_PLUGIN_DIR"] = str(plugins)
    config = WORKSPACE / ".tflint.hcl"

    with tempfile.TemporaryDirectory(prefix="tflint-data-", dir=runtime) as data:
        env["TF_DATA_DIR"] = data
        result = execute([tflint, "--init", f"--config={config}"], WORKSPACE, env)
        if result != 0:
            return result
        for directory in ROOTS:
            result = execute(
                [
                    tflint, "--recursive", f"--config={config}", "--format=compact",
                    "--minimum-failure-severity=notice", "--no-color",
                ],
                directory,
                env,
            )
            if result != 0:
                return result

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
