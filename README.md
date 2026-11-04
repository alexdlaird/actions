# shipshape

[![Version](https://img.shields.io/github/v/release/alexdlaird/shipshape)](https://github.com/alexdlaird/shipshape/releases)
[![Build](https://img.shields.io/github/actions/workflow/status/alexdlaird/shipshape/build.yml)](https://github.com/alexdlaird/shipshape/actions/workflows/build.yml)
[![GitHub License](https://img.shields.io/github/license/alexdlaird/shipshape)](https://github.com/alexdlaird/shipshape/blob/main/LICENSE)

**shipshape** is a library of small, composable GitHub Actions for shipping exactly what you tested. Version lives in
your repo, a release goes out only from the commit CI already built and tested, and release notes come straight from
your changelog, with the same process in every repo you maintain. Use the whole set or just the piece your workflow is
missing.

Alongside them are a few helpers for building iOS apps on self-hosted Macs, where several repos often share one
machine.

## Installation

Reference an action by its folder, pinned to a major version:

```yaml
- uses: alexdlaird/shipshape/read-version@v1
```

`v1` moves to each `1.x.y` release, so fixes arrive without changing callers. Pin a full version, like `@1.0.0`, to
opt out.

## Basic Usage

### Read and Bump a Version

[`read-version`](https://github.com/alexdlaird/shipshape/blob/main/read-version/action.yml) reads the version with the
same `sed` expression that writes it, so one setting describes a repo's version file however it's formatted.
[`next-version`](https://github.com/alexdlaird/shipshape/blob/main/next-version/action.yml) then works out the next one
from the last release tag.

```yaml
- name: Read current version
  id: current
  uses: alexdlaird/shipshape/read-version@v1
  with:
    version-file: pubspec.yaml
    version-pattern: 's/^version: .*/version: ${VERSION}/'

- name: Compute next version
  id: next
  uses: alexdlaird/shipshape/next-version@v1
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
  uses: alexdlaird/shipshape/check-unreleased@v1
  with:
    version: ${{ steps.current.outputs.version }}

- name: Verify the code about to ship is the tested commit's
  uses: alexdlaird/shipshape/verify-tree@v1
  with:
    tested-sha: ${{ github.sha }}

- name: Wait for the push run to succeed
  id: ci
  uses: alexdlaird/shipshape/wait-for-ci@v1
  with:
    token: ${{ steps.app-token.outputs.token }}
    sha: ${{ github.sha }}
    branch: develop
    repo-slug: ${{ github.repository }}
```

[`wait-for-ci`](https://github.com/alexdlaird/shipshape/blob/main/wait-for-ci/action.yml) outputs the `run-id` that
tested the commit, whose artifacts are what the release ships. If no push run registers within `push-wait-seconds`
(5 minutes), it starts a fresh one on the branch (with `dispatch-inputs`, one `name=value` per line) and waits on
that instead.

### Deploy as Its Own Run

[`run-workflow`](https://github.com/alexdlaird/shipshape/blob/main/run-workflow/action.yml) starts a workflow and waits
for that exact run, so a release can hand off to a `deploy.yml` that keeps its own history, and still fail if the
deploy does.

```yaml
- name: Deploy
  uses: alexdlaird/shipshape/run-workflow@v1
  with:
    workflow: deploy.yml
    ref: develop
    token: ${{ github.token }}
    inputs: |
      version=${{ needs.prereq.outputs.version }}
```

### Release Notes and the Changelog

[`prepare-release`](https://github.com/alexdlaird/shipshape/blob/main/prepare-release/action.yml) moves a
`CHANGELOG.md`'s `[Unreleased]` entries under the dated version and returns them as release notes, checking along the
way that a minor or major has entries and that breaking changes ship in a major. Without a changelog
(`changelog: false`), the notes are the released commits' subjects.

```yaml
- name: Prepare release notes
  id: notes
  uses: alexdlaird/shipshape/prepare-release@v1
  with:
    version: ${{ steps.current.outputs.version }}
    repo-slug: ${{ github.repository }}
```

[`security-versions`](https://github.com/alexdlaird/shipshape/blob/main/security-versions/action.yml) points a
`SECURITY.md`'s supported-versions table at a new minor.

### iOS on a Self-Hosted Mac

```yaml
- name: Wait for the Mac's iOS deploy lock
  uses: alexdlaird/shipshape/ios-deploy-lock@v1
  with:
    mode: acquire

- name: Select latest stable Xcode
  uses: alexdlaird/shipshape/select-xcode@v1

- name: Install pods
  uses: alexdlaird/shipshape/pod-install@v1

# ... build and upload ...

- name: Release the Mac's iOS deploy lock
  if: always()
  uses: alexdlaird/shipshape/ios-deploy-lock@v1
  with:
    mode: release
```

The lock lets deploys from many repos take turns on one Mac, since they share its keychain and provisioning profiles.
[`pod-install`](https://github.com/alexdlaird/shipshape/blob/main/pod-install/action.yml) forces CocoaPods' CDN client
onto HTTP/1.1 and retries transient CDN errors.

## Documentation

Each action's inputs and outputs are documented in its `action.yml`. For complete workflows built from them, see
the reusable release workflows in [`alexdlaird/.github`](https://github.com/alexdlaird/.github), and the projects that
release with them, like [`pyngrok`](https://github.com/alexdlaird/pyngrok/blob/main/.github/workflows/release.yml)
and [Helium](https://github.com/HeliumEdu/frontend/blob/main/.github/workflows/release.yml).

| Action | Does |
|---|---|
| [`read-version`](https://github.com/alexdlaird/shipshape/blob/main/read-version/action.yml) | Read a version (`X.Y.Z`, or `X.Y` written as `X.Y.0`) from its file |
| [`next-version`](https://github.com/alexdlaird/shipshape/blob/main/next-version/action.yml) | Compute the next version from the last release tag |
| [`check-unreleased`](https://github.com/alexdlaird/shipshape/blob/main/check-unreleased/action.yml) | Fail if a version is already tagged |
| [`verify-tree`](https://github.com/alexdlaird/shipshape/blob/main/verify-tree/action.yml) | Fail unless the code about to ship is the tested commit's |
| [`run-workflow`](https://github.com/alexdlaird/shipshape/blob/main/run-workflow/action.yml) | Run a workflow and wait for that run, failing if it fails |
| [`wait-for-ci`](https://github.com/alexdlaird/shipshape/blob/main/wait-for-ci/action.yml) | Wait for a commit's CI push run, re-running failed jobs once or starting one if missing |
| [`prepare-release`](https://github.com/alexdlaird/shipshape/blob/main/prepare-release/action.yml) | Release notes, from `CHANGELOG.md` or commit subjects |
| [`security-versions`](https://github.com/alexdlaird/shipshape/blob/main/security-versions/action.yml) | Point `SECURITY.md` at a new minor |
| [`ios-deploy-lock`](https://github.com/alexdlaird/shipshape/blob/main/ios-deploy-lock/action.yml) | Take turns deploying iOS apps on a shared Mac |
| [`pod-install`](https://github.com/alexdlaird/shipshape/blob/main/pod-install/action.yml) | `pod install` that survives CocoaPods' CDN |
| [`select-xcode`](https://github.com/alexdlaird/shipshape/blob/main/select-xcode/action.yml) | Select the newest stable Xcode |

## Contributing

If you would like to get involved, be sure to review
the [Contribution Guide](https://github.com/alexdlaird/shipshape/blob/main/CONTRIBUTING.md).

Want to contribute financially? If you've found `shipshape`
useful, [sponsorship](https://github.com/sponsors/alexdlaird)
would also be greatly appreciated!
