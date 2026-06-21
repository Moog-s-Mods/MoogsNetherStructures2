# Changelog

---

## 3.0.0-alpha.2 — 2026-06-03

### Fixed
- Piglin item format on 1.21+ targets - was using legacy tag compound (pre-1.20.5 shape), now uses components map per the target MC version
- Accept MSL alpha versions in dependency constraint. Previously MNS required MSL `>=3.0.0` which rejected `3.0.0-alpha.X` per semver pre-release ordering, causing a Fabric Loader incompatibility error at startup. Constraint relaxed to `>=3.0.0-alpha.1`.

### Changed
- mc 26.2 support

---

## [3.0.0] - 2026-05-27

Adds the Mega Fortress and requires Moog's Structure Lib 3.0.0 or newer.

### Added
- **Mega Fortress** - a large new nether structure assembled from a jigsaw layout: roofed and roofless corridors, crossings from small up to mega, forks, corners, staircases, a raised upper level, dedicated spawner rooms, and matching dead-end caps.
- **Fortress garrison** - themed inhabitants including fortress guards, archers, black guards, blaze sentinels, champions, and a warden of the keep.

### Changed
- Now requires Moog's Structure Lib **3.0.0** or newer.
- **Structure density** - merged 5 groups of variant structures into shared weighted sets, reducing overall nether structure density.

---

## [2.1.0] - 2026-05-22

### Fixed
- Versioned structures now have a defined path for Minecraft 26.1–26.1.2, so the game stops logging "no version mapping matched" warnings and no longer falls back to an older structure template.

---

## [2.0.4] - 2026-05-06

### Added
- Empty barrels in nether structures now contain loot

### Fixed
- Fixed very small nether brick ruins not generating correctly due to a misconfigured template pool
- Fixed chain blocks breaking in the giant skull, large house, smoking shrine, and train on 1.21.9+ (chain was renamed to iron_chain in that update)
- Updated piglins and piglin brutes in the medium houses to use the new 1.21 item format

---

## [2.0.31] - 2026-02-01

### Changed
- Updated for 1.21.11

---
