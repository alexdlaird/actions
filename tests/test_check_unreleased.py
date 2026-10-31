__copyright__ = "Copyright (c) 2026 Alex Laird"
__license__ = "MIT"

from tests.testcase import ActionTestCase


class TestCheckUnreleased(ActionTestCase):
    def check_unreleased(self, version):
        return self.run_action("check-unreleased", VERSION=version)

    def test_passes_for_a_new_version(self):
        # GIVEN
        self.given_tags("3.13.0")

        # WHEN
        result = self.check_unreleased("3.13.1")

        # THEN
        self.assert_succeeds(result)

    def test_fails_for_a_released_version(self):
        # GIVEN
        self.given_tags("3.13.1")

        # WHEN
        result = self.check_unreleased("3.13.1")

        # THEN
        self.assert_fails(result)

    def test_fails_for_a_version_released_with_a_build_number(self):
        # GIVEN
        self.given_tags("3.13.0+440")

        # WHEN
        result = self.check_unreleased("3.13.0")

        # THEN
        self.assert_fails(result)

    def test_a_longer_patch_is_a_different_version(self):
        # GIVEN
        self.given_tags("3.13.10")

        # WHEN
        result = self.check_unreleased("3.13.1")

        # THEN
        self.assert_succeeds(result)

    def test_two_part_versions(self):
        # GIVEN
        self.given_tags("1.0")

        # WHEN
        released = self.check_unreleased("1.0")
        unreleased = self.check_unreleased("1.1")

        # THEN
        self.assert_fails(released)
        self.assert_succeeds(unreleased)
