__copyright__ = "Copyright (c) 2026 Alex Laird"
__license__ = "MIT"

import os

from tests.testcase import ActionTestCase


class TestSentryRelease(ActionTestCase):
    def setUp(self):
        super().setUp()
        self.calls = os.path.join(self.fake_bin, "calls.log")
        self.given_fake_command("pip", f'#!/usr/bin/env bash\necho "pip $*" >> "{self.calls}"\n')
        self.given_sentry_cli()

    def given_sentry_cli(self, failing_subcommand=""):
        self.given_fake_command("sentry-cli", f"""#!/usr/bin/env bash
echo "sentry-cli $* [$SENTRY_PROPERTIES] [$SENTRY_AUTH_TOKEN]" >> "{self.calls}"
if [ -n "{failing_subcommand}" ] && [ "$2" = "{failing_subcommand}" ]; then exit 1; fi
""")

    def sentry_release(self, **overrides):
        env = dict(VERSION="2.8.1", SENTRY_PROPERTIES="sentry.properties", SENTRY_AUTH_TOKEN="token",
                   SENTRY_CLI_VERSION="3.6.2")
        env.update(overrides)
        return self.run_action("sentry-release", **env)

    def recorded_calls(self):
        if not os.path.exists(self.calls):
            return []
        with open(self.calls) as f:
            return f.read().splitlines()

    def test_creates_associates_commits_and_finalizes_the_release(self):
        # GIVEN
        self.given_file("sentry.properties", "defaults.org=org\ndefaults.project=project\n")

        # WHEN
        result = self.sentry_release()

        # THEN
        self.assert_succeeds(result)
        self.assertEqual([
            "pip install --quiet sentry-cli==3.6.2",
            "sentry-cli releases new 2.8.1 [sentry.properties] [token]",
            "sentry-cli releases set-commits --auto 2.8.1 [sentry.properties] [token]",
            "sentry-cli releases finalize 2.8.1 [sentry.properties] [token]",
        ], self.recorded_calls())

    def test_reads_the_properties_from_a_subdirectory(self):
        # GIVEN
        os.makedirs(self.path("sentry"))
        self.given_file(os.path.join("sentry", "sentry.properties"), "defaults.org=org\n")

        # WHEN
        result = self.sentry_release(SENTRY_PROPERTIES="sentry/sentry.properties")

        # THEN
        self.assert_succeeds(result)
        self.assertIn("sentry-cli releases new 2.8.1 [sentry/sentry.properties] [token]", self.recorded_calls())

    def test_fails_without_the_properties_file(self):
        # WHEN
        result = self.sentry_release()

        # THEN
        self.assert_fails(result)
        self.assertIn("sentry.properties not found", result.stdout)
        self.assertEqual([], self.recorded_calls(), "nothing is installed or created without a Sentry project")

    def test_stops_when_a_step_fails(self):
        # GIVEN
        self.given_file("sentry.properties", "defaults.org=org\n")
        self.given_sentry_cli(failing_subcommand="set-commits")

        # WHEN
        result = self.sentry_release()

        # THEN
        self.assert_fails(result)
        self.assertFalse(any("finalize" in call for call in self.recorded_calls()),
                         "a release whose commits weren't associated isn't finalized")
