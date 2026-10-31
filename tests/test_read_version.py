__copyright__ = "Copyright (c) 2026 Alex Laird"
__license__ = "MIT"

from tests.testcase import ActionTestCase

PYTHON_PATTERN = 's/^__version__ = ".*"/__version__ = "${VERSION}"/'
PUBSPEC_PATTERN = "s/^version: .*/version: ${VERSION}/"


class TestReadVersion(ActionTestCase):
    def read_version(self, version_file, pattern, parts="3", ref=""):
        return self.run_action("read-version", VERSION_FILE=version_file, VERSION_PATTERN=pattern,
                               VERSION_PARTS=parts, REF=ref)

    def test_three_part_version(self):
        # GIVEN
        self.given_file("version.py", 'import os\n__version__ = "9.1.0"\n')

        # WHEN
        result = self.read_version("version.py", PYTHON_PATTERN)

        # THEN
        self.assert_succeeds(result)
        self.assertEqual("9.1.0", self.outputs()["version"])
        self.assertEqual("9.1.0", self.outputs()["file_version"])

    def test_pubspec_build_number_is_ignored(self):
        # GIVEN
        self.given_file("pubspec.yaml", "name: app\nversion: 1.4.4+1\n")

        # WHEN
        result = self.read_version("pubspec.yaml", PUBSPEC_PATTERN)

        # THEN
        self.assert_succeeds(result)
        self.assertEqual("1.4.4", self.outputs()["version"])

    def test_gradle_version(self):
        # GIVEN
        self.given_file("build.gradle", 'plugins {\n    id "java"\n}\n\nversion = "4.0.2"\n')

        # WHEN
        result = self.read_version("build.gradle", 's/^version = ".*"/version = "${VERSION}"/')

        # THEN
        self.assert_succeeds(result)
        self.assertEqual("4.0.2", self.outputs()["version"])

    def test_unanchored_manifest_version(self):
        # GIVEN
        self.given_file("manifest.json", '{\n  "domain": "hearth",\n  "requirements": ["pyhearth==1.1.0"],\n'
                                         '  "version": "1.1.1"\n}\n')

        # WHEN
        result = self.read_version("manifest.json", 's/"version": ".*"/"version": "${VERSION}"/')

        # THEN
        self.assert_succeeds(result)
        self.assertEqual("1.1.1", self.outputs()["version"], "a pinned dependency is not the version")

    def test_bare_version_file(self):
        # GIVEN
        self.given_file("VERSION", "1.0.0\n")

        # WHEN
        result = self.read_version("VERSION", "s/^[0-9.]*$/${VERSION}/")

        # THEN
        self.assert_succeeds(result)
        self.assertEqual("1.0.0", self.outputs()["version"])

    def test_two_part_version_drops_the_zero_patch(self):
        # GIVEN
        self.given_file("pubspec.yaml", "version: 1.2.0\n")

        # WHEN
        result = self.read_version("pubspec.yaml", PUBSPEC_PATTERN, parts="2")

        # THEN
        self.assert_succeeds(result)
        self.assertEqual("1.2", self.outputs()["version"])
        self.assertEqual("1.2.0", self.outputs()["file_version"])

    def test_two_part_version_rejects_a_patch(self):
        # GIVEN
        self.given_file("pubspec.yaml", "version: 1.2.3\n")

        # WHEN
        result = self.read_version("pubspec.yaml", PUBSPEC_PATTERN, parts="2")

        # THEN
        self.assert_fails(result)

    def test_reads_from_a_commit(self):
        # GIVEN
        self.given_file("version.py", '__version__ = "1.0.0"\n')
        self.git("add", "version.py")
        commit = self.given_commit("one")
        self.given_file("version.py", '__version__ = "2.0.0"\n')

        # WHEN
        result = self.read_version("version.py", PYTHON_PATTERN, ref=commit)

        # THEN
        self.assert_succeeds(result)
        self.assertEqual("1.0.0", self.outputs()["version"])

    def test_fails_without_a_version(self):
        # GIVEN
        self.given_file("version.py", "nothing here\n")

        # WHEN
        result = self.read_version("version.py", PYTHON_PATTERN)

        # THEN
        self.assert_fails(result)
