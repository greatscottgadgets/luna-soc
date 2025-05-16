# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

<!--
## [Unreleased]
-->

## [0.2.5] - 2025-04-03
### Fixed
* Facedancer ftdi-echo example stopped working in the 0.2.4 release.

## [0.2.4] - 2025-04-03
### Fixed
* Concurrent transactions could lock `OutFIFOInterface`. (Tx @thejh!)
* Concurrent transactions could lock `InFIFOInterface`.


## [0.2.3] - 2025-02-26
### Fixed
- Only set ep_control epno register if it's a setup packet.
### Removed
* Dropped support for Python 3.8
### Security
* Bump jinja2 from 3.1.4 to 3.1.5


## [0.2.2] - 2024-12-19
### Added
- Support for yowasp when yosys is unavailable.


## [0.2.1] - 2024-11-25
### Fixed
- Fix ambiguous documentation and implementation for usb2.interfaces.eptri.OutFIFOInterface priming behaviour.
### Changed
- Non-control endpoints for eptri OutFIFOInterface are no longer unprimed after receiving a data packet.


## [0.2.0] - 2024-07-05
### Changed
- Replaced `WishboneSPIFlashReader` with `SPIFlashPeripheral`


## [0.1.0] - 2024-06-12
### Added
- Initial release


[Unreleased]: https://github.com/greatscottgadgets/luna-soc/compare/0.2.5...HEAD
[0.2.5]: https://github.com/greatscottgadgets/luna-soc/compare/0.2.4...0.2.5
[0.2.4]: https://github.com/greatscottgadgets/luna-soc/compare/0.2.3...0.2.4
[0.2.3]: https://github.com/greatscottgadgets/luna-soc/compare/0.2.2...0.2.3
[0.2.2]: https://github.com/greatscottgadgets/luna-soc/compare/0.2.1...0.2.2
[0.2.1]: https://github.com/greatscottgadgets/luna-soc/compare/0.2.0...0.2.1
[0.2.0]: https://github.com/greatscottgadgets/luna-soc/compare/0.1.0...0.2.0
[0.1.0]: https://github.com/greatscottgadgets/luna-soc/releases/tag/0.1.0
