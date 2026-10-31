__copyright__ = "Copyright (c) 2026 Alex Laird"
__license__ = "MIT"

import os
import tempfile

from tests.testcase import ActionTestCase


class TestVerifyTree(ActionTestCase):
    def setUp(self):
        super().setUp()
        self.given_file("app.txt", "code\n")
        self.given_file("CHANGELOG.md", "# Changelog\n")
        self.git("add", "app.txt", "CHANGELOG.md")
        self.tested_sha = self.given_commit("tested")

    def verify_tree(self, commit="", changelog="false"):
        return self.run_action("verify-tree", TESTED_SHA=self.tested_sha, COMMIT=commit, CHANGELOG=changelog)

    def commit_on_top(self, message):
        self.git("add", "-A")
        return self.given_commit(message)

    def test_passes_when_the_working_tree_is_the_tested_code(self):
        # WHEN
        result = self.verify_tree()

        # THEN
        self.assert_succeeds(result)

    def test_fails_when_a_tracked_file_differs(self):
        # GIVEN
        self.given_file("app.txt", "changed\n")

        # WHEN
        result = self.verify_tree()

        # THEN
        self.assert_fails(result)

    def test_fails_when_an_untracked_file_appears(self):
        # GIVEN
        self.given_file("generated.txt", "new\n")

        # WHEN
        result = self.verify_tree()

        # THEN
        self.assert_fails(result)

    def test_changelog_may_differ_only_in_changelog_mode(self):
        # GIVEN
        self.given_file("CHANGELOG.md", "# Changelog\n\n## [1.0.0] - today\n")

        # WHEN
        without_changelog = self.verify_tree(changelog="false")
        with_changelog = self.verify_tree(changelog="true")

        # THEN
        self.assert_fails(without_changelog)
        self.assert_succeeds(with_changelog)

    def test_passes_for_a_commit_with_the_tested_tree(self):
        # GIVEN
        release = self.commit_on_top("Release 1.0.0")

        # WHEN
        result = self.verify_tree(commit=release)

        # THEN
        self.assert_succeeds(result)

    def test_fails_for_a_commit_with_other_code(self):
        # GIVEN
        self.given_file("app.txt", "changed\n")
        release = self.commit_on_top("Release 1.0.0")

        # WHEN
        result = self.verify_tree(commit=release)

        # THEN
        self.assert_fails(result)

    def test_changelog_only_commit_passes_in_changelog_mode(self):
        # GIVEN
        self.given_file("CHANGELOG.md", "# Changelog\n\n## [1.0.0] - today\n")
        release = self.commit_on_top("Release 1.0.0")

        # WHEN
        without_changelog = self.verify_tree(commit=release, changelog="false")
        with_changelog = self.verify_tree(commit=release, changelog="true")

        # THEN
        self.assert_fails(without_changelog)
        self.assert_succeeds(with_changelog)

    def test_fetches_a_commit_pushed_elsewhere(self):
        # GIVEN
        origin = os.path.join(tempfile.mkdtemp(), "origin.git")
        self.git("init", "-q", "--bare", "-b", "main", origin)
        self.git("remote", "add", "origin", origin)
        self.git("push", "-q", "origin", "HEAD:main")
        pusher = os.path.join(tempfile.mkdtemp(), "pusher")
        self.git("clone", "-q", origin, pusher)
        self.git("-c", "user.name=Bot", "-c", "user.email=bot@example.com", "commit", "-q", "--allow-empty", "-m",
                 "Release 1.0.0", cwd=pusher)
        self.git("push", "-q", "origin", "HEAD:main", cwd=pusher)
        release = self.git("rev-parse", "HEAD", cwd=pusher)

        # WHEN
        result = self.verify_tree(commit=release)

        # THEN
        self.assert_succeeds(result)
