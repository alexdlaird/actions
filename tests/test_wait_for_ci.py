__copyright__ = "Copyright (c) 2026 Alex Laird"
__license__ = "MIT"

import json
import os
import tempfile

from tests.testcase import ActionTestCase

SHA = "abc123"

FAKE_GH = """#!/usr/bin/env python3
# Answers the gh calls wait-for-ci makes from JSON in FAKE_STATE
import json, os, sys

state = os.environ["FAKE_STATE"]
args = sys.argv[1:]
with open(os.path.join(state, "calls"), "a") as f:
    f.write(" ".join(args) + "\\n")


def load(name):
    with open(os.path.join(state, name)) as f:
        return json.load(f)


if args[:2] == ["run", "rerun"]:
    run = load("run.json")
    run.update(run_attempt=run["run_attempt"] + 1, status="completed", conclusion="success")
    with open(os.path.join(state, "run.json"), "w") as f:
        json.dump(run, f)
    sys.exit(0)

path = args[1]
if "/git/refs/heads/" in path:
    body = load("head.json")
elif "/runs?" in path:
    body = load("runs.json")
else:
    body = load("run.json")

sys.stdout.write(json.dumps(body))
"""


class TestWaitForCi(ActionTestCase):
    def given_github(self, branch_head, run):
        self.fake_state = tempfile.mkdtemp()
        with open(os.path.join(self.fake_state, "head.json"), "w") as f:
            json.dump({"object": {"sha": branch_head}}, f)
        with open(os.path.join(self.fake_state, "runs.json"), "w") as f:
            json.dump({"workflow_runs": [run] if run else []}, f)
        with open(os.path.join(self.fake_state, "run.json"), "w") as f:
            json.dump(run or {}, f)
        self.given_fake_command("gh", FAKE_GH)
        self.given_fake_command("sleep", "#!/usr/bin/env bash\nexit 0\n")

    def calls(self):
        with open(os.path.join(self.fake_state, "calls")) as f:
            return f.read()

    def wait_for_ci(self, branch="develop"):
        return self.run_action("wait-for-ci", GH_TOKEN="token", CI_SHA=SHA, CI_BRANCH=branch, REPO_SLUG="owner/repo",
                               CI_WORKFLOW="build.yml", CI_TIMEOUT_MINUTES="1", CI_POLL_SECONDS="0",
                               CI_SETTLE_SECONDS="0", FAKE_STATE=self.fake_state)

    def test_returns_the_successful_push_run(self):
        # GIVEN
        self.given_github(SHA, {"id": 7, "status": "completed", "conclusion": "success", "run_attempt": 1})

        # WHEN
        result = self.wait_for_ci()

        # THEN
        self.assert_succeeds(result)
        self.assertEqual("7", self.outputs()["run_id"])
        self.assertIn("event=push&branch=develop", self.calls(), "only push runs on the branch count")

    def test_waits_on_another_branch(self):
        # GIVEN
        self.given_github(SHA, {"id": 7, "status": "completed", "conclusion": "success", "run_attempt": 1})

        # WHEN
        result = self.wait_for_ci(branch="main")

        # THEN
        self.assert_succeeds(result)
        self.assertIn("refs/heads/main", self.calls())
        self.assertIn("event=push&branch=main", self.calls())

    def test_reruns_failed_jobs_then_waits(self):
        # GIVEN
        self.given_github(SHA, {"id": 7, "status": "completed", "conclusion": "failure", "run_attempt": 1})

        # WHEN
        result = self.wait_for_ci()

        # THEN
        self.assert_succeeds(result)
        self.assertIn("run rerun 7 --failed --repo owner/repo", self.calls())
        self.assertEqual("7", self.outputs()["run_id"], "same run, next attempt")

    def test_fails_when_the_rerun_fails_again(self):
        # GIVEN
        self.given_github(SHA, {"id": 7, "status": "completed", "conclusion": "failure", "run_attempt": 1})
        self.given_fake_command("gh", FAKE_GH.replace('conclusion="success"', 'conclusion="failure"'))

        # WHEN
        result = self.wait_for_ci()

        # THEN
        self.assert_fails(result)

    def test_fails_when_the_branch_moved(self):
        # GIVEN
        self.given_github("def456", {"id": 7, "status": "completed", "conclusion": "success", "run_attempt": 1})

        # WHEN
        result = self.wait_for_ci()

        # THEN
        self.assert_fails(result)

    def test_reports_github_errors(self):
        # GIVEN
        self.given_github(SHA, {"id": 7, "status": "completed", "conclusion": "success", "run_attempt": 1})
        failing_runs_lookup = 'elif "/runs?" in path:\n    sys.stderr.write("HTTP 404: Not Found\\n")\n    sys.exit(1)'
        self.given_fake_command("gh", FAKE_GH.replace('elif "/runs?" in path:\n    body = load("runs.json")',
                                                      failing_runs_lookup))

        # WHEN
        result = self.wait_for_ci()

        # THEN
        self.assert_fails(result)
        self.assertIn("::error::gh api repos/owner/repo/actions/workflows/build.yml/runs", result.stdout)
        self.assertIn("HTTP 404: Not Found", result.stdout)
        self.assertNotIn("Traceback", result.stderr)

    def test_fails_without_a_push_run(self):
        # GIVEN
        self.given_github(SHA, None)

        # WHEN
        result = self.wait_for_ci()

        # THEN
        self.assert_fails(result)
