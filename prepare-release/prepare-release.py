__copyright__ = "Copyright (c) 2026 Alex Laird"
__license__ = "MIT"

import datetime
import os
import re
import subprocess
import uuid
from typing import List, Optional, Tuple

from shipshape import fail

CHANGELOG_FILE = "CHANGELOG.md"
UNRELEASED_PATTERN = re.compile(r"^## \[Unreleased\]")
RELEASE_HEADER_PATTERN = re.compile(r"^## \[\d")
RELEASE_VERSION_PATTERN = re.compile(r"^## \[(\d+\.\d+(?:\.\d+)?)\]")
VERSION_HEADER_PATTERN = re.compile(r"^## \[\d+\.\d+(?:\.\d+)?\]", re.MULTILINE)
BREAKING_PATTERN = re.compile(r"^### Breaking", re.MULTILINE)


def write_release_outputs(release_notes: str, **outputs: str) -> None:
    delimiter = f"ghadelimiter_{uuid.uuid4()}"
    with open(os.environ["GITHUB_OUTPUT"], "a") as f:
        for name, value in outputs.items():
            f.write(f"{name}={value}\n")
        f.write(f"release_notes<<{delimiter}\n{release_notes}\n{delimiter}\n")


def commit_notes(base: str, tested_sha: str) -> str:
    """
    Get the released commits' subjects as release notes, leaving out version bumps.
    """
    log = subprocess.run(["git", "log", "--pretty=format:- %s", f"{base}..{tested_sha}"], check=True,
                         capture_output=True, text=True).stdout
    subjects = [line for line in log.splitlines() if not line.startswith("- Bump version to ")]
    return "\n".join(subjects) or "- (no commits found)"


def parts(version: str) -> Tuple[int, int, int]:
    major, minor, *patch = (int(part) for part in version.split("."))
    return major, minor, patch[0] if patch else 0


def bump_type(old_version: Optional[str], new_version: str) -> str:
    """
    Determine how the new version differs from the CHANGELOG's last release. A first release counts as a minor, so it
    needs entries.
    """
    if old_version is None:
        return "minor"
    old_major, old_minor, old_patch = parts(old_version)
    new_major, new_minor, new_patch = parts(new_version)
    if new_major > old_major and new_minor == 0 and new_patch == 0:
        return "major"
    if new_major == old_major and new_minor > old_minor and new_patch == 0:
        return "minor"
    if new_major == old_major and new_minor == old_minor and new_patch > old_patch:
        return "patch"
    fail(f"Version {new_version} does not follow {old_version} (the CHANGELOG's last release). Set the version "
         f"to the next patch, minor, or major.")


def trim_blank_lines(text: str) -> str:
    lines = text.split("\n")
    while lines and not lines[0].strip():
        lines.pop(0)
    while lines and not lines[-1].strip():
        lines.pop()
    return "\n".join(lines)


def release_changelog(new_version: str, two_part: bool, repo_slug: str) -> Tuple[Optional[str], str]:
    """
    Move the [Unreleased] entries under the dated new version, returning the previous version and the notes.
    """
    if not os.path.exists(CHANGELOG_FILE):
        fail("CHANGELOG.md not found")
    with open(CHANGELOG_FILE) as f:
        lines: List[str] = f.read().split("\n")

    unreleased = next((i for i, line in enumerate(lines) if UNRELEASED_PATTERN.match(line)), None)
    if unreleased is None:
        fail("No \"## [Unreleased]\" section found in CHANGELOG.md")
    previous = next((i for i in range(unreleased + 1, len(lines)) if RELEASE_HEADER_PATTERN.match(lines[i])),
                    len(lines))
    old_version = None
    if previous < len(lines):
        match = RELEASE_VERSION_PATTERN.match(lines[previous])
        if not match:
            fail(f"Could not parse previous version from: {lines[previous]}")
        old_version = match.group(1)

    if two_part and new_version.count(".") != 1:
        fail(f"Two-part versions are X.Y, not {new_version}")
    release_type = bump_type(old_version, new_version)

    content = "\n".join(lines[unreleased + 1:previous]).rstrip("\n")
    # A patch may go out with nothing listed (its notes say so); a minor or major release must say what's in it
    if not content.strip():
        if release_type != "patch":
            fail(f"No content found under [Unreleased] section. A {release_type} release needs changelog entries; "
                 f"add them before releasing.")
        print("No changelog entries under [Unreleased]; releasing the patch as stability and bug fixes")
        content = "\n### Fixed\n\n- Stability and bug fixes."
    if VERSION_HEADER_PATTERN.search(content):
        fail("Found a version header under [Unreleased]. Put entries directly under [Unreleased], without a "
             "version or date header, since the release adds it.")
    if BREAKING_PATTERN.search(content) and release_type != "major":
        fail(f"Changelog contains a \"### Breaking\" section, but the bump type is \"{release_type}\". Use \"major\" "
             f"for breaking changes.")

    today = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d")
    print(f"Previous version: {old_version or '(first release)'}")
    print(f"New version: {new_version} ({release_type} bump)")
    print(f"Release date: {today}")

    version_link = f"https://github.com/{repo_slug}/compare/{old_version}...{new_version}" if old_version \
        else f"https://github.com/{repo_slug}/releases/tag/{new_version}"
    released = lines[:unreleased] + [
        f"## [Unreleased](https://github.com/{repo_slug}/compare/{new_version}...HEAD)",
        "",
        f"## [{new_version}]({version_link}) - {today}",
        content,
        "",
    ] + lines[previous:]
    with open(CHANGELOG_FILE, "w") as f:
        f.write("\n".join(released))

    return old_version, trim_blank_lines(content)


def main() -> None:
    if os.environ["CHANGELOG"] != "true":
        write_release_outputs(commit_notes(os.environ.get("BASE", "main"), os.environ["TESTED_SHA"]))
        return

    new_version = os.environ["VERSION"]
    repo_slug = os.environ["REPO_SLUG"]
    if not new_version or not repo_slug:
        fail("A changelog release needs \"version\" and \"repo-slug\"")

    old_version, release_notes = release_changelog(new_version, os.environ["VERSION_PARTS"] == "2", repo_slug)
    write_release_outputs(release_notes, new_version=new_version, old_version=old_version or "")


if __name__ == "__main__":
    main()
