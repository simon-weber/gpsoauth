# Changelog

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html) as of 1.0.0.

## [1.1.1] - 2024-06-09

### Changed

- Load default certs to fix SSL failures ([#67](https://github.com/simon-weber/gpsoauth/pull/67))

## [1.1.0] - 2024-04-10

### Added

- Add support for manual token exchange to handle stubborn BadAuthentication situations ([#41](https://github.com/simon-weber/gpsoauth/pull/41))

## [1.0.4] - 2023-11-28

### Changed

- Set Accept-Encoding: identity to prevent NeedsBrowser in some cases ([#61](https://github.com/simon-weber/gpsoauth/pull/61))

## [1.0.3] - 2023-09-24

### Changed

- Fix compatibility with urllib3 < 2 ([#51](https://github.com/simon-weber/gpsoauth/pull/51))

## [1.0.2] - 2022-05-31

### Changed

- Fix compatibility with urllib3 < 1.26 ([#43](https://github.com/simon-weber/gpsoauth/pull/43))

## [1.0.1] - 2022-05-31

### Changed

- Update master token flow to prevent NeedsBrowser responses. Thanks [@CyberAltra](https://github.com/CyberAltra)!

## [1.0.0] - 2021-04-06

Thanks to [@KapJI](https://github.com/KapJI) for their contributions to this release!

### Breaking

- Set minimum supported Python version to 3.8 ([#31](https://github.com/simon-weber/gpsoauth/pull/31))

### Added

- PEP 585 type hints ([#33](https://github.com/simon-weber/gpsoauth/pull/33))
- Misc tooling/release improvements

### Changed

- Use a modified copy of DEFAULT_CIPHERS to prevent problems when other libraries modify it ([#35](https://github.com/simon-weber/gpsoauth/pull/35))
