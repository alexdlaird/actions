# Changelog

All notable changes to this project will be documented in this file.

This project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased](https://github.com/alexdlaird/shipshape/compare/1.1.0...HEAD)

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
