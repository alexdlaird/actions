# Changelog

All notable changes to this project will be documented in this file.

This project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased](https://github.com/alexdlaird/shipshape/compare/1.4.1...HEAD)

### Fixed

- `ios-deploy-lock`: a job cancelled while waiting for the lock no longer takes it as an orphan and leaves it held until it goes stale; the lock names the job it was taken for, so a holder that ended is always broken.

## [1.4.1](https://github.com/alexdlaird/shipshape/compare/1.4.0...1.4.1) - 2026-11-06

### Fixed

- Stability and bug fixes.

## [1.4.0](https://github.com/alexdlaird/shipshape/compare/1.3.0...1.4.0) - 2026-11-05

### Added

- `resolve-release`, to resolve a released version (the newest tag when none is given) and, from its tag, the commit and the `Build-Run` its release recorded, so a deploy finds what to ship.

## [1.3.0](https://github.com/alexdlaird/shipshape/compare/1.2.1...1.3.0) - 2026-11-05

### Added

- `sentry-release`, to create the Sentry release for a version, associate the commits it adds, and finalize it, so a release can create it before its deploy reports to Sentry.

## [1.2.1](https://github.com/alexdlaird/shipshape/compare/1.2.0...1.2.1) - 2026-11-04

### Fixed

- `wait-for-ci` waits up to `push-wait-seconds` (5 minutes) for the push run to register before starting a fresh one. GitHub can register a push run minutes late, and starting one after a minute built the commit twice.

## [1.2.0](https://github.com/alexdlaird/shipshape/compare/1.1.1...1.2.0) - 2026-11-04

### Added

- `dispatch-inputs` on `wait-for-ci`, which now starts a fresh run of the workflow on the branch when the commit has no push run, instead of failing. It still ignores dispatch runs it didn't start, whose inputs may skip work.

## [1.1.1](https://github.com/alexdlaird/shipshape/compare/1.1.0...1.1.1) - 2026-11-03

### Fixed

- `ios-deploy-lock` holds the lock for the whole job. It took the step's own shell for the holder, which exits when the step does, so the next deploy broke the lock at once and two could run together on the Mac.

## [1.1.0](https://github.com/alexdlaird/shipshape/compare/1.0.1...1.1.0) - 2026-10-31

### Added

- `run-workflow`, to run a workflow and wait for that run, so a release can hand off to a separate deploy.

## [1.0.1](https://github.com/alexdlaird/shipshape/compare/1.0.0...1.0.1) - 2026-10-31

### Fixed

- `wait-for-ci` fails with GitHub's error (like a token without Actions access) instead of a traceback.

## [1.0.0](https://github.com/alexdlaird/shipshape/releases/tag/1.0.0) - 2026-10-31

- First release of `shipshape`.
