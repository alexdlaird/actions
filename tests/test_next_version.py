__copyright__ = "Copyright (c) 2026 Alex Laird"
__license__ = "MIT"

from tests.testcase import ActionTestCase


class TestNextVersion(ActionTestCase):
    def next_version(self, bump_type, parts, current, current_file_version):
        return self.run_action("next-version", BUMP_TYPE=bump_type, VERSION_PARTS=parts, CURRENT=current,
                               CURRENT_FILE_VERSION=current_file_version)

    def test_next_bumps_the_patch_after_a_release(self):
        # GIVEN
        self.given_tags("9.1.0")

        # WHEN
        result = self.next_version("next", "3", "9.1.0", "9.1.0")

        # THEN
        self.assert_succeeds(result)
        self.assertEqual("true", self.outputs()["changed"])
        self.assertEqual("9.1.0", self.outputs()["current"])
        self.assertEqual("9.1.1", self.outputs()["version"])
        self.assertEqual("9.1.1", self.outputs()["file_version"])

    def test_next_bumps_the_minor_for_two_part_versions(self):
        # GIVEN
        self.given_tags("1.0")

        # WHEN
        result = self.next_version("next", "2", "1.0", "1.0.0")

        # THEN
        self.assert_succeeds(result)
        self.assertEqual("1.1", self.outputs()["version"])
        self.assertEqual("1.1.0", self.outputs()["file_version"])

    def test_major_resets_minor_and_patch(self):
        # GIVEN
        self.given_tags("4.2.7")

        # WHEN
        result = self.next_version("major", "3", "4.2.8", "4.2.8")

        # THEN
        self.assert_succeeds(result)
        self.assertEqual("5.0.0", self.outputs()["version"])

    def test_minor_after_the_automatic_patch_bump(self):
        # GIVEN
        self.given_tags("3.13.0")

        # WHEN
        result = self.next_version("minor", "3", "3.13.1", "3.13.1")

        # THEN
        self.assert_succeeds(result)
        self.assertEqual("3.14.0", self.outputs()["version"], "minor counts from the last tag, not develop")

    def test_never_lowers_a_version_already_set(self):
        # GIVEN
        self.given_tags("3.13.0")

        # WHEN
        result = self.next_version("next", "3", "3.14.0", "3.14.0")

        # THEN
        self.assert_succeeds(result)
        self.assertEqual("false", self.outputs()["changed"], "a minor already set outranks the automatic patch")
        self.assertEqual("3.14.0", self.outputs()["version"])

    def test_build_number_tags_count_as_releases(self):
        # GIVEN
        self.given_tags("3.12.0+439", "3.13.0+440")

        # WHEN
        result = self.next_version("next", "3", "3.13.0", "3.13.0")

        # THEN
        self.assert_succeeds(result)
        self.assertEqual("3.13.1", self.outputs()["version"])

    def test_versions_sort_numerically(self):
        # GIVEN
        self.given_tags("2.7.9", "2.7.28")

        # WHEN
        result = self.next_version("next", "3", "2.7.28", "2.7.28")

        # THEN
        self.assert_succeeds(result)
        self.assertEqual("2.7.29", self.outputs()["version"], "2.7.28 is newer than 2.7.9")

    def test_other_tags_are_ignored(self):
        # GIVEN
        self.given_tags("1.4.4", "mobile/v9.9.9", "v1", "ios/build-357")

        # WHEN
        result = self.next_version("next", "3", "1.4.4", "1.4.4")

        # THEN
        self.assert_succeeds(result)
        self.assertEqual("1.4.5", self.outputs()["version"])

    def test_two_part_versions_have_no_patch(self):
        # GIVEN
        self.given_tags("1.0")

        # WHEN
        result = self.next_version("patch", "2", "1.0", "1.0.0")

        # THEN
        self.assert_fails(result)

    def test_rejects_an_unknown_bump_type(self):
        # GIVEN
        self.given_tags("1.0.0")

        # WHEN
        result = self.next_version("huge", "3", "1.0.0", "1.0.0")

        # THEN
        self.assert_fails(result)

    def test_fails_without_a_release_tag(self):
        # GIVEN
        self.given_tags("mobile/v1.4.4")

        # WHEN
        result = self.next_version("next", "3", "1.4.5", "1.4.5")

        # THEN
        self.assert_fails(result)
