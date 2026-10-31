__copyright__ = "Copyright (c) 2026 Alex Laird"
__license__ = "MIT"

import json
import os
import subprocess
import sys
import time
from typing import NoReturn, Optional

# Waits for a run to register, or for a re-run to start, take this many settle intervals at most
SETTLE_ATTEMPTS = 12


def fail(message: str) -> NoReturn:
    print(f"::error::{message}")
    sys.exit(1)


def gh(*args: str) -> str:
    result = subprocess.run(["gh", *args], capture_output=True, text=True)
    if result.returncode != 0:
        fail(f"gh {' '.join(args)} failed: {(result.stderr or result.stdout).strip()}")
    return result.stdout


def gh_api(path: str) -> dict:
    return json.loads(gh("api", path))


def latest_push_run(repo_slug: str, workflow: str, sha: str, branch: str) -> Optional[dict]:
    # Only the push run builds the release candidates (a dispatch or PR run for the same SHA may not)
    runs = gh_api(f"repos/{repo_slug}/actions/workflows/{workflow}/runs?head_sha={sha}&event=push&branch={branch}")
    return max(runs["workflow_runs"], key=lambda run: run["id"], default=None)


def main() -> None:
    repo_slug = os.environ["REPO_SLUG"]
    workflow = os.environ["CI_WORKFLOW"]
    sha = os.environ["CI_SHA"]
    branch = os.environ.get("CI_BRANCH", "develop")
    timeout_minutes = int(os.environ["CI_TIMEOUT_MINUTES"])
    poll_seconds = int(os.environ.get("CI_POLL_SECONDS", "30"))
    settle_seconds = int(os.environ.get("CI_SETTLE_SECONDS", "5"))
    deadline = time.time() + timeout_minutes * 60

    current = gh_api(f"repos/{repo_slug}/git/refs/heads/{branch}")["object"]["sha"]
    if current != sha:
        fail(f"{branch} HEAD moved during release (was {sha}, now {current}). Re-run.")

    latest = None
    for _ in range(SETTLE_ATTEMPTS):
        latest = latest_push_run(repo_slug, workflow, sha, branch)
        if latest:
            break
        time.sleep(settle_seconds)
    if not latest:
        fail(f"No {workflow} push run for {sha}. Push to {branch} to build it, then re-run.")

    run_id = latest["id"]
    with open(os.environ["GITHUB_OUTPUT"], "a") as f:
        f.write(f"run_id={run_id}\n")

    if latest["status"] == "completed" and latest.get("conclusion") != "success":
        print(f"{workflow} run {run_id} concluded '{latest.get('conclusion')}'; re-running its failed jobs")
        gh("run", "rerun", str(run_id), "--failed", "--repo", repo_slug)
        for _ in range(SETTLE_ATTEMPTS):
            time.sleep(settle_seconds)
            if gh_api(f"repos/{repo_slug}/actions/runs/{run_id}")["run_attempt"] > latest["run_attempt"]:
                break
    else:
        print(f"Tracking {workflow} run {run_id} (status={latest['status']})")

    while time.time() < deadline:
        run = gh_api(f"repos/{repo_slug}/actions/runs/{run_id}")
        if run["status"] == "completed":
            if run.get("conclusion") == "success":
                print(f"{workflow} run {run_id} succeeded on {branch} HEAD")
                return
            fail(f"{workflow} run {run_id} concluded '{run.get('conclusion') or ''}'")
        print(f"{workflow} run {run_id} status={run['status']} ({int(deadline - time.time())}s remaining)")
        time.sleep(poll_seconds)

    fail(f"Timed out waiting for {workflow} run {run_id} after {timeout_minutes} minutes")


if __name__ == "__main__":
    main()
