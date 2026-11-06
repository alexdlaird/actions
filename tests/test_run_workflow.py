__copyright__ = "Copyright (c) 2026 Alex Laird"
__license__ = "MIT"

import json
import os
import tempfile

from tests.testcase import ActionTestCase

FAKE_GH = """#!/usr/bin/env python3
import json, os, sys

state = os.environ["FAKE_STATE"]
args = sys.argv[1:]
with open(os.path.join(state, "calls"), "a") as f:
    f.write(" ".join(args) + "\\n")

if "-X" in args and "POST" in args:
    with open(os.path.join(state, "dispatch_body.json"), "w") as f:
        f.write(sys.stdin.read())
    if os.environ.get("DISPATCH_ERROR"):
        sys.stderr.write(os.environ["DISPATCH_ERROR"] + "\\n")
        sys.exit(1)
    sys.stdout.write(os.environ.get("DISPATCH_RESPONSE", ""))
else:
    with open(os.path.join(state, "run.json")) as f:
        sys.stdout.write(f.read())
"""

STARTED = json.dumps({"workflow_run_id": 42, "run_url": "https://api.github.com/repos/owner/repo/actions/runs/42",
                      "html_url": "https://github.com/owner/repo/actions/runs/42"})


class TestRunWorkflow(ActionTestCase):
    def given_github(self, run, dispatch_response=STARTED, dispatch_error=""):
        self.fake_state = tempfile.mkdtemp()
        with open(os.path.join(self.fake_state, "run.json"), "w") as f:
            json.dump(run, f)
        self.dispatch_response = dispatch_response
        self.dispatch_error = dispatch_error
        self.given_fake_command("gh", FAKE_GH)

    def dispatch_body(self):
        with open(os.path.join(self.fake_state, "dispatch_body.json")) as f:
            return json.load(f)

    def calls(self):
        with open(os.path.join(self.fake_state, "calls")) as f:
            return f.read()

    def run_workflow(self, inputs=""):
        return self.run_action("run-workflow", GH_TOKEN="token", WORKFLOW="deploy.yml", REF="develop", INPUTS=inputs,
                               REPO_SLUG="owner/repo", TIMEOUT_MINUTES="1", POLL_SECONDS="0",
                               FAKE_STATE=self.fake_state, DISPATCH_RESPONSE=self.dispatch_response,
                               DISPATCH_ERROR=self.dispatch_error)

    def test_waits_for_the_run_it_started(self):
        # GIVEN
        self.given_github({"status": "completed", "conclusion": "success"})

        # WHEN
        result = self.run_workflow()

        # THEN
        self.assert_succeeds(result)
        self.assertEqual("42", self.outputs()["run_id"])
        self.assertEqual("https://github.com/owner/repo/actions/runs/42", self.outputs()["run_url"])
        self.assertIn("api repos/owner/repo/actions/runs/42", self.calls())

    def test_dispatches_with_its_inputs_and_asks_for_the_run(self):
        # GIVEN
        self.given_github({"status": "completed", "conclusion": "success"})

        # WHEN
        result = self.run_workflow("version=1.4.5\nsubmit_to_store=false\n\nbuild_run_id== 7")

        # THEN
        self.assert_succeeds(result)
        self.assertIn("api -X POST repos/owner/repo/actions/workflows/deploy.yml/dispatches", self.calls())
        self.assertEqual({"ref": "develop",
                          "inputs": {"version": "1.4.5", "submit_to_store": "false", "build_run_id": "= 7"},
                          "return_run_details": True}, self.dispatch_body())

    def test_fails_when_the_run_fails(self):
        # GIVEN
        self.given_github({"status": "completed", "conclusion": "failure"})

        # WHEN
        result = self.run_workflow()

        # THEN
        self.assert_fails(result)
        self.assertIn('concluded "failure"', result.stdout)

    def test_reports_a_rejected_dispatch(self):
        # GIVEN
        self.given_github({}, dispatch_error="HTTP 422: Unexpected inputs provided")

        # WHEN
        result = self.run_workflow("unknown=1")

        # THEN
        self.assert_fails(result)
        self.assertIn("HTTP 422: Unexpected inputs provided", result.stdout)

    def test_fails_without_a_run_to_follow(self):
        # GIVEN
        self.given_github({}, dispatch_response="")

        # WHEN
        result = self.run_workflow()

        # THEN
        self.assert_fails(result)
        self.assertIn("returned no run to follow", result.stdout)

    def test_rejects_an_input_without_a_value(self):
        # GIVEN
        self.given_github({"status": "completed", "conclusion": "success"})

        # WHEN
        result = self.run_workflow("version")

        # THEN
        self.assert_fails(result)
