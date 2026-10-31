__copyright__ = "Copyright (c) 2026 Alex Laird"
__license__ = "MIT"

import os

from tests.testcase import ActionTestCase


class TestSecurityVersions(ActionTestCase):
    def given_security_table(self, supported, older):
        self.given_file("SECURITY.md", f"""# Security Policy

## Supported Versions

| Version | Supported          |
| ------- | ------------------ |
| {supported}     | :white_check_mark: |
| < {older}   | :x:                |

## Reporting
""")

    def security_versions(self, version):
        return self.run_action("security-versions", NEW_VERSION=version)

    def test_points_the_table_at_a_new_minor(self):
        # GIVEN
        self.given_security_table("9.1.x", "9.1")

        # WHEN
        result = self.security_versions("9.2.0")

        # THEN
        self.assert_succeeds(result)
        security = self.read("SECURITY.md")
        self.assertIn("| 9.2.x   | :white_check_mark: |", security)
        self.assertIn("| < 9.2   | :x:                |", security)
        self.assertNotIn("9.1.x", security)
        self.assertIn("## Reporting", security)

    def test_leaves_a_listed_minor_alone(self):
        # GIVEN
        self.given_security_table("9.1.x", "9.1")
        before = self.read("SECURITY.md")

        # WHEN
        result = self.security_versions("9.1.4")

        # THEN
        self.assert_succeeds(result)
        self.assertEqual(before, self.read("SECURITY.md"))

    def test_skips_a_repo_without_security_md(self):
        # WHEN
        result = self.security_versions("9.2.0")

        # THEN
        self.assert_succeeds(result)
        self.assertFalse(os.path.exists(self.path("SECURITY.md")))

    def test_skips_a_table_that_lists_versions_another_way(self):
        # GIVEN
        self.given_file("SECURITY.md", "| Version | Supported |\n"
                                       "| ------- | --------- |\n"
                                       "| latest | :white_check_mark: |\n")
        before = self.read("SECURITY.md")

        # WHEN
        result = self.security_versions("9.2.0")

        # THEN
        self.assert_succeeds(result)
        self.assertEqual(before, self.read("SECURITY.md"))
