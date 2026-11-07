__copyright__ = "Copyright (c) 2026 Alex Laird"
__license__ = "MIT"

import os
import tempfile

from tests.testcase import ActionTestCase

FAKE_XCODEBUILD = """#!/usr/bin/env bash
echo "Xcode from ${DEVELOPER_DIR}"
"""

FAKE_SUDO = """#!/usr/bin/env bash
echo "sudo $*" >&2
exit 1
"""


class TestSelectXcode(ActionTestCase):
    def setUp(self):
        super().setUp()
        self.apps_dir = tempfile.mkdtemp()
        self.github_env = os.path.join(tempfile.mkdtemp(), "env")
        open(self.github_env, "w").close()
        self.given_fake_command("xcodebuild", FAKE_XCODEBUILD)
        self.given_fake_command("sudo", FAKE_SUDO)

    def given_xcodes(self, *names):
        for name in names:
            os.makedirs(os.path.join(self.apps_dir, name, "Contents", "Developer"))

    def select(self):
        return self.run_action("select-xcode", XCODE_APPS_DIR=self.apps_dir, GITHUB_ENV=self.github_env)

    def test_selects_the_newest_stable_xcode_for_the_rest_of_the_job(self):
        # GIVEN
        self.given_xcodes("Xcode_26.4.app", "Xcode_27.0.app", "Xcode_27.1_beta.app",
                          "Xcode_27.1_Release_Candidate.app")

        # WHEN
        result = self.select()

        # THEN
        self.assert_succeeds(result)
        developer_dir = os.path.join(self.apps_dir, "Xcode_27.0.app", "Contents", "Developer")
        with open(self.github_env) as f:
            self.assertEqual(f"DEVELOPER_DIR={developer_dir}\n", f.read())
        self.assertIn(f"Xcode from {developer_dir}", result.stdout, "the version shown is the selected Xcode's")

    def test_never_needs_root(self):
        # GIVEN
        self.given_xcodes("Xcode.app")

        # WHEN
        result = self.select()

        # THEN
        self.assert_succeeds(result)
        self.assertNotIn("sudo", result.stderr, "a self-hosted runner's user has no sudo")

    def test_fails_without_a_stable_xcode(self):
        # GIVEN
        self.given_xcodes("Xcode_27.1_beta.app")

        # WHEN
        result = self.select()

        # THEN
        self.assert_fails(result)
        self.assertIn("No stable Xcode found", result.stdout)
