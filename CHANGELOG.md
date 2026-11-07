# Changelog

All notable changes to this project will be documented in this file.

This project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased](https://github.com/alexdlaird/shipshape/compare/1.4.4...HEAD)

## [1.4.4](https://github.com/alexdlaird/shipshape/compare/1.4.3...1.4.4) - 2026-11-07

### Changed

- `select-xcode` selects Xcode for the current job only, and no longer needs `sudo`.

## [1.4.3](https://github.com/alexdlaird/shipshape/compare/1.4.2...1.4.3) - 2026-11-07

### Fixed

- Stability and bug fixes.

## [1.4.2](https://github.com/alexdlaird/shipshape/compare/1.4.1...1.4.2) - 2026-11-07

### Fixed

- Stability and bug fixes.

## [1.4.1](https://github.com/alexdlaird/shipshape/compare/1.4.0...1.4.1) - 2026-11-06

### Fixed

- Stability and bug fixes.

## [1.4.0](https://github.com/alexdlaird/shipshape/compare/1.3.0...1.4.0) - 2026-11-05

### Added

- `resolve-release`, to find a released version's commit and `Build-Run`.

## [1.3.0](https://github.com/alexdlaird/shipshape/compare/1.2.1...1.3.0) - 2026-11-05

### Added

- `sentry-release`, to create and finalize a version's Sentry release.

## [1.2.1](https://github.com/alexdlaird/shipshape/compare/1.2.0...1.2.1) - 2026-11-04

### Added

- `push-wait-seconds` on `wait-for-ci`, how long to wait for a push run before starting one.

## [1.2.0](https://github.com/alexdlaird/shipshape/compare/1.1.1...1.2.0) - 2026-11-04

### Added

- `dispatch-inputs` on `wait-for-ci`, to start a run when the commit has none.

## [1.1.1](https://github.com/alexdlaird/shipshape/compare/1.1.0...1.1.1) - 2026-11-03

### Fixed

- Stability and bug fixes.

## [1.1.0](https://github.com/alexdlaird/shipshape/compare/1.0.1...1.1.0) - 2026-10-31

### Added

- `run-workflow`, to run a workflow and wait for it.

## [1.0.1](https://github.com/alexdlaird/shipshape/compare/1.0.0...1.0.1) - 2026-10-31

### Fixed

- Stability and bug fixes.

## [1.0.0](https://github.com/alexdlaird/shipshape/releases/tag/1.0.0) - 2026-10-31

- First release of `shipshape`.
