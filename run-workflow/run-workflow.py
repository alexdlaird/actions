__copyright__ = "Copyright (c) 2026 Alex Laird"
__license__ = "MIT"

import json
import os
import subprocess
import sys
import time
from typing import Dict, NoReturn


def fail(message: str) -> NoReturn:
    print(f"::error::{message}")
    sys.exit(1)


def gh(*args: str, stdin: str = "") -> str:
    result = subprocess.run(["gh", *args], input=stdin, capture_output=True, text=True)
    if result.returncode != 0:
        fail(f"gh {' '.join(args)} failed: {(result.stderr or result.stdout).strip()}")
    return result.stdout


def parse_inputs(text: str) -> Dict[str, str]:
    """
    The workflow's inputs, one ``name=value`` per line.
    """
    inputs = {}
    for line in text.splitlines():
        if not line.strip():
            continue
        if "=" not in line:
            fail(f"Input '{line}' isn't name=value")
        name, value = line.split("=", 1)
        inputs[name.strip()] = value.strip()
    return inputs


def main() -> None:
    repo_slug = os.environ["REPO_SLUG"]
    workflow = os.environ["WORKFLOW"]
    ref = os.environ["REF"]
    timeout_minutes = int(os.environ["TIMEOUT_MINUTES"])
    poll_seconds = int(os.environ["POLL_SECONDS"])
    deadline = time.time() + timeout_minutes * 60

    # The dispatch returns the run it created, so the run waited on is never another one started around the same time
    body = {"ref": ref, "inputs": parse_inputs(os.environ.get("INPUTS", "")), "return_run_details": True}
    started = json.loads(gh("api", "-X", "POST", f"repos/{repo_slug}/actions/workflows/{workflow}/dispatches",
                            "--input", "-", stdin=json.dumps(body)) or "{}")
    run_id = started.get("workflow_run_id")
    if not run_id:
        fail(f"GitHub started {workflow} but returned no run to follow")
    run_url = started.get("html_url", f"https://github.com/{repo_slug}/actions/runs/{run_id}")

    with open(os.environ["GITHUB_OUTPUT"], "a") as f:
        f.write(f"run_id={run_id}\nrun_url={run_url}\n")
    print(f"Started {workflow}: {run_url}")

    while time.time() < deadline:
        run = json.loads(gh("api", f"repos/{repo_slug}/actions/runs/{run_id}"))
        if run["status"] == "completed":
            if run.get("conclusion") == "success":
                print(f"{workflow} run {run_id} succeeded")
                return
            fail(f"{workflow} run {run_id} concluded '{run.get('conclusion') or ''}': {run_url}")
        print(f"{workflow} run {run_id} status={run['status']} ({int(deadline - time.time())}s remaining)")
        time.sleep(poll_seconds)

    fail(f"Timed out waiting for {workflow} run {run_id} after {timeout_minutes} minutes: {run_url}")


if __name__ == "__main__":
    main()
