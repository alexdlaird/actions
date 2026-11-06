__copyright__ = "Copyright (c) 2026 Alex Laird"
__license__ = "MIT"

import json
import os
import tempfile

from tests.testcase import ActionTestCase

FAKE_GH = """#!/usr/bin/env python3
import json, os, subprocess, sys

state = os.environ["FAKE_STATE"]
args = sys.argv[1:]
with open(os.path.join(state, "calls"), "a") as f:
    f.write(" ".join(args) + "\\n")

with open(os.path.join(state, "github.json")) as f:
    github = json.load(f)

path = args[1]
if path.endswith("/tags"):
    body = [{"name": name} for name in github["tags"]]
elif "/git/ref/tags/" in path:
    version = path.rsplit("/", 1)[1]
    if version not in github["refs"]:
        sys.stderr.write("HTTP 404: Not Found")
        sys.exit(1)
    body = {"object": github["refs"][version]}
elif "/git/tags/" in path:
    body = github["tag_objects"][path.rsplit("/", 1)[1]]
else:
    sys.exit(1)

if "--jq" in args:
    expression = args[args.index("--jq") + 1]
    sys.stdout.write(subprocess.run(["jq", "-r", expression], input=json.dumps(body), capture_output=True,
                                    text=True, check=True).stdout)
else:
    sys.stdout.write(json.dumps(body))
"""


class TestResolveRelease(ActionTestCase):
    def given_github(self, tags=(), annotated=None, lightweight=None):
        self.fake_state = tempfile.mkdtemp()
        refs = {version: {"type": "commit", "sha": commit} for version, commit in (lightweight or {}).items()}
        tag_objects = {}
        for version, (commit, message) in (annotated or {}).items():
            tag_sha = f"tag-{version}"
            refs[version] = {"type": "tag", "sha": tag_sha}
            tag_objects[tag_sha] = {"object": {"sha": commit}, "message": message}
        with open(os.path.join(self.fake_state, "github.json"), "w") as f:
            json.dump({"tags": list(tags), "refs": refs, "tag_objects": tag_objects}, f)
        self.given_fake_command("gh", FAKE_GH)

    def resolve(self, version="", ref="", build_run_id="", read_tag="true", require_build_run="false"):
        return self.run_action("resolve-release", GH_TOKEN="token", REPO_SLUG="owner/repo", VERSION=version, REF=ref,
                               BUILD_RUN_ID=build_run_id, READ_TAG=read_tag, REQUIRE_BUILD_RUN=require_build_run,
                               VERSION_REGEX=r"^[0-9]+\.[0-9]+\.[0-9]+$", FAKE_STATE=self.fake_state)

    def calls(self):
        path = os.path.join(self.fake_state, "calls")
        if not os.path.exists(path):
            return []
        with open(path) as f:
            return f.read().splitlines()

    def test_reads_a_versions_commit_and_build_run_from_its_tag(self):
        # GIVEN
        self.given_github(annotated={"1.4.10": ("abc1234", "Release 1.4.10\n\nBuild-Run: 42079059778")})

        # WHEN
        result = self.resolve(version="1.4.10", require_build_run="true")

        # THEN
        self.assert_succeeds(result)
        self.assertEqual({"version": "1.4.10", "ref": "abc1234", "build_run_id": "42079059778"}, self.outputs())

    def test_resolves_the_newest_version_tag_when_no_version_is_given(self):
        # GIVEN
        self.given_github(tags=["v1", "3.15.1", "3.15.0"],
                          annotated={"3.15.1": ("def5678", "Release 3.15.1\n\nBuild-Run: 7")})

        # WHEN
        result = self.resolve()

        # THEN
        self.assert_succeeds(result)
        self.assertEqual({"version": "3.15.1", "ref": "def5678", "build_run_id": "7"}, self.outputs())

    def test_a_given_commit_and_build_run_skip_the_tag(self):
        # GIVEN
        self.given_github()

        # WHEN
        result = self.resolve(version="1.4.11", ref="fff0000", build_run_id="99", require_build_run="true")

        # THEN
        self.assert_succeeds(result)
        self.assertEqual({"version": "1.4.11", "ref": "fff0000", "build_run_id": "99"}, self.outputs())
        self.assertEqual([], self.calls())

    def test_resolves_only_the_version_when_not_reading_the_tag(self):
        # GIVEN
        self.given_github()

        # WHEN
        result = self.resolve(version="2.0.0", read_tag="false")

        # THEN
        self.assert_succeeds(result)
        self.assertEqual({"version": "2.0.0", "ref": "", "build_run_id": ""}, self.outputs())
        self.assertEqual([], self.calls())

    def test_a_given_commit_alone_skips_the_tag_when_no_build_run_is_required(self):
        # GIVEN
        self.given_github()

        # WHEN
        result = self.resolve(version="0.9.0", ref="aaa1111")

        # THEN
        self.assert_succeeds(result)
        self.assertEqual({"version": "0.9.0", "ref": "aaa1111", "build_run_id": ""}, self.outputs())

    def test_a_tag_without_a_build_run_is_fine_when_none_is_required(self):
        # GIVEN
        self.given_github(annotated={"0.9.0": ("bbb2222", "Release 0.9.0")})

        # WHEN
        result = self.resolve(version="0.9.0")

        # THEN
        self.assert_succeeds(result)
        self.assertEqual({"version": "0.9.0", "ref": "bbb2222", "build_run_id": ""}, self.outputs())

    def test_a_lightweight_tag_resolves_to_its_commit(self):
        # GIVEN
        self.given_github(lightweight={"1.2.0": "ccc3333"})

        # WHEN
        result = self.resolve(version="1.2.0")

        # THEN
        self.assert_succeeds(result)
        self.assertEqual({"version": "1.2.0", "ref": "ccc3333", "build_run_id": ""}, self.outputs())

    def test_fails_when_a_build_run_is_required_and_the_tag_is_lightweight(self):
        # GIVEN
        self.given_github(lightweight={"1.2.0": "ccc3333"})

        # WHEN
        result = self.resolve(version="1.2.0", require_build_run="true")

        # THEN
        self.assert_fails(result)

    def test_fails_when_a_build_run_is_required_and_the_tag_names_none(self):
        # GIVEN
        self.given_github(annotated={"1.4.10": ("abc1234", "Release 1.4.10")})

        # WHEN
        result = self.resolve(version="1.4.10", require_build_run="true")

        # THEN
        self.assert_fails(result)
        self.assertIn("::error::Tag 1.4.10 names no Build-Run", result.stdout)

    def test_fails_when_no_tag_matches(self):
        # GIVEN
        self.given_github(tags=["v1", "nightly"])

        # WHEN
        result = self.resolve()

        # THEN
        self.assert_fails(result)
        self.assertIn("::error::No version tags matching", result.stdout)

    def test_fails_when_the_versions_tag_does_not_exist(self):
        # GIVEN
        self.given_github()

        # WHEN
        result = self.resolve(version="9.9.9")

        # THEN
        self.assert_fails(result)
