# actions

[![Version](https://img.shields.io/github/v/release/alexdlaird/actions)](https://github.com/alexdlaird/actions/releases)
[![Build](https://img.shields.io/github/actions/workflow/status/alexdlaird/actions/build.yml)](https://github.com/alexdlaird/actions/actions/workflows/build.yml)
[![GitHub License](https://img.shields.io/github/license/alexdlaird/actions)](https://github.com/alexdlaird/actions/blob/main/LICENSE)

`actions` is a set of composite GitHub Actions for releasing software the same way across many repos, and for
building iOS apps on self-hosted Macs. Each action is a small, tested script behind an `action.yml`, so a workflow
stays wiring while the logic can be read, linted, and tested on its own.

They back the shared release workflows in [`alexdlaird/.github`](https://github.com/alexdlaird/.github): a release
squashes `develop` into `main`, ships the artifacts CI already built and tested for that exact commit, then bumps
`develop` to the next version.

## Installation

Reference an action by its folder, pinned to a major version:

```yaml
- uses: alexdlaird/actions/read-version@v1
```

`v1` moves to each `1.x.y` release, so fixes arrive without changing callers. Pin a full version, like `@1.0.0`, to
opt out.

## Basic Usage

### Read and Bump a Version

[`read-version`](https://github.com/alexdlaird/actions/blob/main/read-version/action.yml) reads the version with the
same `sed` expression that writes it, so one setting describes a repo's version file however it's formatted.
[`next-version`](https://github.com/alexdlaird/actions/blob/main/next-version/action.yml) then works out the next one
from the last release tag.

```yaml
- name: Read current version
  id: current
  uses: alexdlaird/actions/read-version@v1
  with:
    version-file: pubspec.yaml
    version-pattern: 's/^version: .*/version: ${VERSION}/'

- name: Compute next version
  id: next
  uses: alexdlaird/actions/next-version@v1
  with:
    bump-type: next
    current: ${{ steps.current.outputs.version }}
    current-file-version: ${{ steps.current.outputs.file-version }}
```

`next` is a patch, or a minor for two-part `X.Y` versions (set `version-parts: 2`). A version already set higher, like
a minor chosen ahead of a release, is never lowered.

### Gate a Release on Its Tested Commit

```yaml
- name: Pre-validate version is unreleased
  uses: alexdlaird/actions/check-unreleased@v1
  with:
    version: ${{ steps.current.outputs.version }}

- name: Verify main gets develop's tested code
  uses: alexdlaird/actions/verify-tree@v1
  with:
    tested-sha: ${{ env.DEVELOP_SHA }}

- name: Wait for the develop push run to succeed
  id: ci
  uses: alexdlaird/actions/wait-for-ci@v1
  with:
    token: ${{ steps.app-token.outputs.token }}
    sha: ${{ env.DEVELOP_SHA }}
    repo-slug: ${{ github.repository }}
```

[`wait-for-ci`](https://github.com/alexdlaird/actions/blob/main/wait-for-ci/action.yml) outputs the `run-id` that
tested the commit, whose artifacts are what the release ships.

### Release Notes and the Changelog

[`prepare-release`](https://github.com/alexdlaird/actions/blob/main/prepare-release/action.yml) moves a
`CHANGELOG.md`'s `[Unreleased]` entries under the dated version and returns them as release notes, checking along the
way that a minor or major has entries and that breaking changes ship in a major. Without a changelog
(`changelog: false`), the notes are the released commits' subjects.

```yaml
- name: Prepare release notes
  id: notes
  uses: alexdlaird/actions/prepare-release@v1
  with:
    version: ${{ steps.current.outputs.version }}
    repo-slug: ${{ github.repository }}
```

[`security-versions`](https://github.com/alexdlaird/actions/blob/main/security-versions/action.yml) points a
`SECURITY.md`'s supported-versions table at a new minor.

### iOS on a Self-Hosted Mac

```yaml
- name: Wait for the Mac's iOS deploy lock
  uses: alexdlaird/actions/ios-deploy-lock@v1
  with:
    mode: acquire

- name: Select latest stable Xcode
  uses: alexdlaird/actions/select-xcode@v1

- name: Install pods
  uses: alexdlaird/actions/pod-install@v1

# ... build and upload ...

- name: Release the Mac's iOS deploy lock
  if: always()
  uses: alexdlaird/actions/ios-deploy-lock@v1
  with:
    mode: release
```

The lock lets deploys from many repos take turns on one Mac, since they share its keychain and provisioning profiles.
[`pod-install`](https://github.com/alexdlaird/actions/blob/main/pod-install/action.yml) forces CocoaPods' CDN client
onto HTTP/1.1 and retries transient CDN errors.

## Documentation

Each action's inputs and outputs are documented in its `action.yml`.

| Action | Does |
|---|---|
| [`read-version`](https://github.com/alexdlaird/actions/blob/main/read-version/action.yml) | Read a version (`X.Y.Z`, or `X.Y` written as `X.Y.0`) from its file |
| [`next-version`](https://github.com/alexdlaird/actions/blob/main/next-version/action.yml) | Compute the next version from the last release tag |
| [`check-unreleased`](https://github.com/alexdlaird/actions/blob/main/check-unreleased/action.yml) | Fail if a version is already tagged |
| [`verify-tree`](https://github.com/alexdlaird/actions/blob/main/verify-tree/action.yml) | Fail unless the code about to ship is the tested commit's |
| [`wait-for-ci`](https://github.com/alexdlaird/actions/blob/main/wait-for-ci/action.yml) | Wait for a commit's CI push run, re-running failed jobs once |
| [`prepare-release`](https://github.com/alexdlaird/actions/blob/main/prepare-release/action.yml) | Release notes, from `CHANGELOG.md` or commit subjects |
| [`security-versions`](https://github.com/alexdlaird/actions/blob/main/security-versions/action.yml) | Point `SECURITY.md` at a new minor |
| [`ios-deploy-lock`](https://github.com/alexdlaird/actions/blob/main/ios-deploy-lock/action.yml) | Take turns deploying iOS apps on a shared Mac |
| [`pod-install`](https://github.com/alexdlaird/actions/blob/main/pod-install/action.yml) | `pod install` that survives CocoaPods' CDN |
| [`select-xcode`](https://github.com/alexdlaird/actions/blob/main/select-xcode/action.yml) | Select the newest stable Xcode |

## Contributing

If you would like to get involved, be sure to review
the [Contribution Guide](https://github.com/alexdlaird/actions/blob/main/CONTRIBUTING.md).

Want to contribute financially? If you've found these actions
useful, [sponsorship](https://github.com/sponsors/alexdlaird)
would also be greatly appreciated!
