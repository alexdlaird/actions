__copyright__ = "Copyright (c) 2026 Alex Laird"
__license__ = "MIT"

import os
import re
import subprocess
import sys
from typing import NoReturn, Optional, Tuple

# Release tags are the bare version; X.Y.Z+N tags are from releases that also stamped a build number
RELEASE_TAG_PATTERN = re.compile(r"^(\d+)\.(\d+)(?:\.(\d+))?(?:\+(\d+))?$")

VersionKey = Tuple[int, int, int, int]


def fail(message: str) -> NoReturn:
    print(f"::error::{message}")
    sys.exit(1)


def write_outputs(**outputs: str) -> None:
    with open(os.environ["GITHUB_OUTPUT"], "a") as f:
        for name, value in outputs.items():
            f.write(f"{name}={value}\n")


def parse_version(version: str) -> Optional[VersionKey]:
    match = RELEASE_TAG_PATTERN.match(version)
    if not match:
        return None

    major, minor, patch, build = match.groups()
    return int(major), int(minor), int(patch or 0), int(build or 0)


def version_key(version: str) -> VersionKey:
    key = parse_version(version)
    if key is None:
        fail(f"Not a version: {version}")
    return key


def last_release_tag() -> Optional[str]:
    tags = subprocess.run(["git", "tag", "--list"], check=True, capture_output=True, text=True).stdout.split()
    releases = [tag for tag in tags if parse_version(tag)]
    return max(releases, key=version_key) if releases else None


def main() -> None:
    bump_type = os.environ["BUMP_TYPE"]
    two_part = os.environ["VERSION_PARTS"] == "2"
    current = os.environ["CURRENT"]
    current_file_version = os.environ["CURRENT_FILE_VERSION"]

    if bump_type == "next":
        bump_type = "minor" if two_part else "patch"
    if bump_type == "patch" and two_part:
        fail("Two-part versions have no patch; bump minor or major.")

    last_tag = last_release_tag()
    if not last_tag:
        fail("No release tag to bump from. Set the first version in the version file by hand.")

    major, minor, patch, _ = version_key(last_tag)
    if bump_type == "major":
        new_file_version = f"{major + 1}.0.0"
    elif bump_type == "minor":
        new_file_version = f"{major}.{minor + 1}.0"
    elif bump_type == "patch":
        new_file_version = f"{major}.{minor}.{patch + 1}"
    else:
        fail(f"Invalid bump_type: {bump_type}")
    new = new_file_version.rsplit(".", 1)[0] if two_part else new_file_version

    if version_key(current_file_version) >= version_key(new_file_version):
        print(f"develop is already at {current} ({bump_type} from {last_tag} is {new}); nothing to bump")
        write_outputs(changed="false", version=current)
        return

    print(f"Bumping develop from {current} to {new} ({bump_type} from {last_tag})")
    write_outputs(changed="true", current=current, version=new, file_version=new_file_version)


if __name__ == "__main__":
    main()
