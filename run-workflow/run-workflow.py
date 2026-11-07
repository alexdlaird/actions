__copyright__ = "Copyright (c) 2026 Alex Laird"
__license__ = "MIT"

import json
import os
import time

from shipshape import fail, gh, gh_unless_not_found, parse_inputs, write_outputs


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

    write_outputs(run_id=str(run_id), run_url=run_url)
    print(f"Started {workflow}: {run_url}")

    # A run GitHub has just started can answer 404 for a moment before it's served
    visible_by = time.time() + float(os.environ.get("RUN_VISIBLE_SECONDS", "120"))
    while time.time() < deadline:
        found = gh_unless_not_found("api", f"repos/{repo_slug}/actions/runs/{run_id}")
        if found is None:
            if time.time() >= visible_by:
                fail(f"GitHub started {workflow} run {run_id} but still can't find it: {run_url}")
            print(f"{workflow} run {run_id} isn't visible yet")
            time.sleep(min(poll_seconds, 5))
            continue
        run = json.loads(found)
        if run["status"] == "completed":
            if run.get("conclusion") == "success":
                print(f"{workflow} run {run_id} succeeded")
                return
            fail(f"{workflow} run {run_id} concluded \"{run.get('conclusion') or ''}\": {run_url}")
        print(f"{workflow} run {run_id} status={run['status']} ({int(deadline - time.time())}s remaining)")
        time.sleep(poll_seconds)

    fail(f"Timed out waiting for {workflow} run {run_id} after {timeout_minutes} minutes: {run_url}")


if __name__ == "__main__":
    main()
