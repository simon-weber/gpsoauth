# Changelog

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html) as of 1.0.0.

## [Unreleased]

## [1.0.0] - 2021-04-06

Thanks to [@KapJI](https://github.com/KapJI) for their contributions to this release!

### Breaking

- Set minimum supported Python version to 3.8 ([#31](https://github.com/simon-weber/gpsoauth/pull/31))

### Added

- PEP 585 type hints ([#33](https://github.com/simon-weber/gpsoauth/pull/33))
- Misc tooling/release improvements

### Changed

- Use a modified copy of DEFAULT_CIPHERS to prevent problems when other libraries modify it ([#35](https://github.com/simon-weber/gpsoauth/pull/35))
