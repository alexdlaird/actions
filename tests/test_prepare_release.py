__copyright__ = "Copyright (c) 2026 Alex Laird"
__license__ = "MIT"

import datetime

from tests.testcase import ActionTestCase


class TestPrepareRelease(ActionTestCase):
    def given_changelog(self, unreleased):
        self.given_file("CHANGELOG.md", f"""# Changelog

## [Unreleased](https://github.com/owner/repo/compare/9.1.0...HEAD)
{unreleased}
## [9.1.0](https://github.com/owner/repo/compare/9.0.0...9.1.0) - 2026-10-26

### Added

- Something earlier.
""")

    def given_develop_commits(self, *subjects):
        self.given_commit()
        self.git("switch", "-q", "-c", "develop")
        for subject in subjects:
            self.given_commit(subject)
        self.tested_sha = self.git("rev-parse", "HEAD")
        self.git("switch", "-q", "main")

    def prepare_release(self, version, parts="3"):
        return self.run_action("prepare-release", NEW_VERSION=version, VERSION_PARTS=parts, REPO_SLUG="owner/repo",
                               CHANGELOG="true", TESTED_SHA="")

    def commit_notes(self):
        return self.run_action("prepare-release", NEW_VERSION="", VERSION_PARTS="3", REPO_SLUG="", CHANGELOG="false",
                               TESTED_SHA=self.tested_sha)

    def test_dates_the_unreleased_entries_under_the_version(self):
        # GIVEN
        self.given_changelog("\n### Fixed\n\n- A fix.\n")

        # WHEN
        result = self.prepare_release("9.1.1")

        # THEN
        self.assert_succeeds(result)
        changelog = self.read("CHANGELOG.md")
        today = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d")
        self.assertIn("## [Unreleased](https://github.com/owner/repo/compare/9.1.1...HEAD)", changelog)
        self.assertIn(f"## [9.1.1](https://github.com/owner/repo/compare/9.1.0...9.1.1) - {today}", changelog)
        self.assertLess(changelog.index("- A fix."), changelog.index("## [9.1.0]"))
        self.assertIn("- Something earlier.", changelog)
        self.assertEqual("9.1.1", self.outputs()["new_version"])
        self.assertEqual("9.1.0", self.outputs()["old_version"])
        self.assertEqual("### Fixed\n\n- A fix.", self.outputs()["release_notes"])

    def test_unreleased_as_the_first_line(self):
        # GIVEN
        self.given_file("CHANGELOG.md", """## [Unreleased](https://github.com/owner/repo/compare/1.0...HEAD)

### Added

- A feature.

## [1.0](https://github.com/owner/repo/compare/0.9...1.0) - 2026-10-01
""")

        # WHEN
        result = self.prepare_release("1.1", parts="2")

        # THEN
        self.assert_succeeds(result)
        self.assertTrue(self.read("CHANGELOG.md").startswith(
            "## [Unreleased](https://github.com/owner/repo/compare/1.1...HEAD)"))
        self.assertIn("## [1.1](https://github.com/owner/repo/compare/1.0...1.1)", self.read("CHANGELOG.md"))

    def test_empty_patch_ships_as_bug_fixes(self):
        # GIVEN
        self.given_changelog("")

        # WHEN
        result = self.prepare_release("9.1.1")

        # THEN
        self.assert_succeeds(result)
        self.assertIn("- Stability and bug fixes.", self.read("CHANGELOG.md"))

    def test_minor_needs_entries(self):
        # GIVEN
        self.given_changelog("")

        # WHEN
        result = self.prepare_release("9.2.0")

        # THEN
        self.assert_fails(result)

    def test_breaking_changes_need_a_major(self):
        # GIVEN
        self.given_changelog("\n### Breaking\n\n- Removed a thing.\n")

        # WHEN
        result = self.prepare_release("9.2.0")

        # THEN
        self.assert_fails(result)

    def test_breaking_changes_ship_in_a_major(self):
        # GIVEN
        self.given_changelog("\n### Breaking\n\n- Removed a thing.\n")

        # WHEN
        result = self.prepare_release("10.0.0")

        # THEN
        self.assert_succeeds(result)
        self.assertIn("## [10.0.0]", self.read("CHANGELOG.md"))

    def test_version_must_follow_the_last_release(self):
        # GIVEN
        self.given_changelog("\n### Fixed\n\n- A fix.\n")

        # WHEN
        result = self.prepare_release("9.0.5")

        # THEN
        self.assert_fails(result)

    def test_rejects_a_version_header_under_unreleased(self):
        # GIVEN
        self.given_changelog("\n## [9.1.1] - 2026-10-30\n\n### Fixed\n\n- A fix.\n")

        # WHEN
        result = self.prepare_release("9.1.1")

        # THEN
        self.assert_fails(result)

    def test_first_release(self):
        # GIVEN
        self.given_file("CHANGELOG.md", "# Changelog\n\n"
                                        "## [Unreleased](https://github.com/owner/repo/commits/develop)\n\n"
                                        "### Added\n\n- Everything.\n")

        # WHEN
        result = self.prepare_release("1.0.0")

        # THEN
        self.assert_succeeds(result)
        changelog = self.read("CHANGELOG.md")
        self.assertIn("## [Unreleased](https://github.com/owner/repo/compare/1.0.0...HEAD)", changelog)
        self.assertIn("## [1.0.0](https://github.com/owner/repo/releases/tag/1.0.0) - ", changelog)
        self.assertTrue(changelog.rstrip().endswith("- Everything."))
        self.assertEqual("", self.outputs()["old_version"])
        self.assertEqual("### Added\n\n- Everything.", self.outputs()["release_notes"])

    def test_first_release_needs_entries(self):
        # GIVEN
        self.given_file("CHANGELOG.md", "# Changelog\n\n"
                                        "## [Unreleased](https://github.com/owner/repo/commits/develop)\n")

        # WHEN
        result = self.prepare_release("1.0.0")

        # THEN
        self.assert_fails(result)

    def test_changelog_mode_needs_a_version(self):
        # GIVEN
        self.given_changelog("\n### Fixed\n\n- A fix.\n")

        # WHEN
        result = self.prepare_release("")

        # THEN
        self.assert_fails(result)

    def test_fails_without_a_changelog(self):
        # WHEN
        result = self.prepare_release("9.1.1")

        # THEN
        self.assert_fails(result)

    def test_without_changelog_lists_the_released_commits_without_bumps(self):
        # GIVEN
        self.given_develop_commits("Add sharing", "Bump version to 1.0.1", "Fix sign-in")

        # WHEN
        result = self.commit_notes()

        # THEN
        self.assert_succeeds(result)
        self.assertEqual("- Fix sign-in\n- Add sharing", self.outputs()["release_notes"])

    def test_without_changelog_leaves_files_alone(self):
        # GIVEN
        self.given_develop_commits("Add sharing")
        self.given_file("CHANGELOG.md", "## [Unreleased]\n")

        # WHEN
        result = self.commit_notes()

        # THEN
        self.assert_succeeds(result)
        self.assertEqual("## [Unreleased]\n", self.read("CHANGELOG.md"))

    def test_without_changelog_says_so_when_there_is_nothing_to_list(self):
        # GIVEN
        self.given_develop_commits("Bump version to 1.0.1")

        # WHEN
        result = self.commit_notes()

        # THEN
        self.assert_succeeds(result)
        self.assertEqual("- (no commits found)", self.outputs()["release_notes"])
