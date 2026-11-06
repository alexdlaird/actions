__copyright__ = "Copyright (c) 2026 Alex Laird"
__license__ = "MIT"

import json
import os
import time
from typing import Any, Dict, Optional

from shipshape import fail, gh, parse_inputs, write_outputs

# A wait for a re-run to start takes this many settle intervals at most
SETTLE_ATTEMPTS = 12


def gh_api(path: str) -> Dict[str, Any]:
    return json.loads(gh("api", path))


def latest_push_run(repo_slug: str, workflow: str, sha: str, branch: str) -> Optional[Dict[str, Any]]:
    # Only the push run builds the release candidates (a dispatch or PR run for the same SHA may not)
    runs = gh_api(f"repos/{repo_slug}/actions/workflows/{workflow}/runs?head_sha={sha}&event=push&branch={branch}")
    return max(runs["workflow_runs"], key=lambda run: run["id"], default=None)


def dispatch_run(repo_slug: str, workflow: str, sha: str, branch: str, inputs: Dict[str, str]) -> Dict[str, Any]:
    """
    Start a fresh run of ``workflow`` on ``branch`` and return it, failing if it isn't building ``sha``.
    """
    body = {"ref": branch, "inputs": inputs, "return_run_details": True}
    started = json.loads(gh("api", "-X", "POST", f"repos/{repo_slug}/actions/workflows/{workflow}/dispatches",
                            "--input", "-", stdin=json.dumps(body)) or "{}")
    run_id = started.get("workflow_run_id")
    if not run_id:
        fail(f"GitHub started {workflow} but returned no run to follow")

    run = gh_api(f"repos/{repo_slug}/actions/runs/{run_id}")
    if run["head_sha"] != sha:
        fail(f"{branch} HEAD moved during release (was {sha}, run {run_id} built {run['head_sha']}). Re-run.")
    return run


def main() -> None:
    repo_slug = os.environ["REPO_SLUG"]
    workflow = os.environ["WORKFLOW"]
    sha = os.environ["SHA"]
    branch = os.environ.get("BRANCH", "develop")
    timeout_minutes = int(os.environ["TIMEOUT_MINUTES"])
    poll_seconds = int(os.environ.get("POLL_SECONDS", "30"))
    settle_seconds = int(os.environ.get("SETTLE_SECONDS", "5"))
    push_wait_seconds = int(os.environ.get("PUSH_WAIT_SECONDS", "300"))
    dispatch_inputs = parse_inputs(os.environ.get("DISPATCH_INPUTS", ""))
    deadline = time.time() + timeout_minutes * 60

    current = gh_api(f"repos/{repo_slug}/git/refs/heads/{branch}")["object"]["sha"]
    if current != sha:
        fail(f"{branch} HEAD moved during release (was {sha}, now {current}). Re-run.")

    latest = latest_push_run(repo_slug, workflow, sha, branch)
    push_deadline = time.time() + push_wait_seconds
    while not latest and time.time() < push_deadline:
        time.sleep(settle_seconds)
        latest = latest_push_run(repo_slug, workflow, sha, branch)

    if not latest:
        latest = dispatch_run(repo_slug, workflow, sha, branch, dispatch_inputs)
        print(f"No {workflow} push run for {sha}; started run {latest['id']} on {branch}")

    run_id = latest["id"]
    write_outputs(run_id=str(run_id))

    if latest["status"] == "completed" and latest.get("conclusion") != "success":
        print(f"{workflow} run {run_id} concluded \"{latest.get('conclusion')}\"; re-running its failed jobs")
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
            fail(f"{workflow} run {run_id} concluded \"{run.get('conclusion') or ''}\"")
        print(f"{workflow} run {run_id} status={run['status']} ({int(deadline - time.time())}s remaining)")
        time.sleep(poll_seconds)

    fail(f"Timed out waiting for {workflow} run {run_id} after {timeout_minutes} minutes")


if __name__ == "__main__":
    main()
