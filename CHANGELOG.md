# Changelog

All notable changes to this project will be documented in this file.

This project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased](https://github.com/alexdlaird/shipshape/compare/1.3.0...HEAD)

## [1.3.0](https://github.com/alexdlaird/shipshape/compare/1.2.1...1.3.0) - 2026-11-05

### Added

- `sentry-release` creates the Sentry release for a version, associates the commits it adds, and finalizes it, so a
  release can create it before its deploy reports to Sentry.

## [1.2.1](https://github.com/alexdlaird/shipshape/compare/1.2.0...1.2.1) - 2026-11-04

### Fixed

- `wait-for-ci` waits up to `push-wait-seconds` (5 minutes) for the push run to register before starting a fresh one.
  GitHub can register a push run minutes late, and starting one after a minute built the commit twice.

## [1.2.0](https://github.com/alexdlaird/shipshape/compare/1.1.1...1.2.0) - 2026-11-04

### Added

- `wait-for-ci` starts a fresh run of the workflow on the branch when the commit has no push run, instead of failing,
  and takes `dispatch-inputs` for it. It still ignores dispatch runs it didn't start, whose inputs may skip work.

## [1.1.1](https://github.com/alexdlaird/shipshape/compare/1.1.0...1.1.1) - 2026-11-03

### Fixed

- `ios-deploy-lock` holds the lock for the whole job. It took the step's own shell for the holder, which exits when the
  step does, so the next deploy broke the lock at once and two could run together on the Mac.

## [1.1.0](https://github.com/alexdlaird/shipshape/compare/1.0.1...1.1.0) - 2026-10-31

### Added

- `run-workflow`, which runs a workflow and waits for that run, so a release can hand off to a separate deploy.

## [1.0.1](https://github.com/alexdlaird/shipshape/compare/1.0.0...1.0.1) - 2026-10-31

### Fixed

- `wait-for-ci` fails with GitHub's error (like a token without Actions access) instead of a traceback.

## [1.0.0](https://github.com/alexdlaird/shipshape/releases/tag/1.0.0) - 2026-10-31

- First release of `shipshape`.
