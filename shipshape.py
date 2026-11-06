__copyright__ = "Copyright (c) 2026 Alex Laird"
__license__ = "MIT"
__muppets__ = "no strings attached"

import os
import subprocess
import sys
from typing import Dict, NoReturn


def fail(message: str) -> NoReturn:
    """
    Report the given message as a GitHub Actions error, then exit with a failure.

    :param message: The error to report.
    """
    print(f"::error::{message}")
    sys.exit(1)


def write_outputs(**outputs: str) -> None:
    """
    Append the given outputs to ``GITHUB_OUTPUT``, one ``name=value`` per line.

    :param outputs: The outputs to write, by name.
    """
    with open(os.environ["GITHUB_OUTPUT"], "a") as f:
        for name, value in outputs.items():
            f.write(f"{name}={value}\n")


def gh(*args: str, stdin: str = "") -> str:
    """
    Run a ``gh`` command and return its output, failing with ``gh``'s error if the command fails.

    :param args: The arguments to pass to ``gh``.
    :param stdin: The input to pass to the command.
    :return: The command's output.
    """
    result = subprocess.run(["gh", *args], input=stdin, capture_output=True, text=True)
    if result.returncode != 0:
        fail(f"gh {' '.join(args)} failed: {(result.stderr or result.stdout).strip()}")
    return result.stdout


def parse_inputs(text: str) -> Dict[str, str]:
    """
    Parse a workflow's inputs, one ``name=value`` per line.

    :param text: The inputs, one per line.
    :return: The inputs, by name.
    """
    inputs = {}
    for line in text.splitlines():
        if not line.strip():
            continue
        if "=" not in line:
            fail(f"Input \"{line}\" isn't name=value")
        name, value = line.split("=", 1)
        inputs[name.strip()] = value.strip()
    return inputs
