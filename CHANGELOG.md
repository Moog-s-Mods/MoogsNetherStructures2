# Changelog

---

## 3.0.0-alpha.2 — 2026-06-03

### Fixed
- Piglin item format on 1.21+ targets - was using legacy tag compound (pre-1.20.5 shape), now uses components map per the target MC version
- Accept MSL alpha versions in dependency constraint. Previously MNS required MSL `>=3.0.0` which rejected `3.0.0-alpha.X` per semver pre-release ordering, causing a Fabric Loader incompatibility error at startup. Constraint relaxed to `>=3.0.0-alpha.1`.

### Changed
- mc 26.2 support

---

## [3.0.0] - 2026-06-22

### Added
- **Mega Fortress** - A massive new nether fortress made up of 207 pieces and packed with loot, mobs and traps. This is our best structure yet across all Moogs structure mods! The mega fortress is made up of various towers with dungeons hidden beneath the lava. Bridges stretch out in all directions with stairs and towers leading to a second floor suspended from the roof with chains.
- **Dragon Arena** - A dragon skeleton sitting in lava lakes. Here you will find the most challenging mobs from the 3 new arenas and therefore, the best loot.
- **Large Arena** - A combat focused arena that is mostly buried beneath the surface. Here you will find plenty of spawners, vaults and trial spawners.
- **Small Arena** - While the easiest of the 3 arenas, don't take it lightly. There are still powerful mobs here protecting loot that's worth the visit.

Good luck!

### Changed
- Now requires Moog's Structure Lib **v3.0.0** or newer.
- Polished several `mega_fortress` upper, forks, staircases, and spawner NBT pieces (re-saves with content tweaks); plain black banners in fortress corners and the east crossing now use the fortress pattern; `mega_crossing_center_1` got a stray observer fix + dispenser load on the floor; chain pillars lengthened so they reach the nether roof.
- Minecraft 26.2 support (validator + pack format range extended to 1.21–26.2).
- `pack.mcmeta` now declares `supported_formats: [48, 107]` so MC 1.21.9+ accepts the pack range without complaint.

### Fixed
- Piglin item format on 1.21+ targets — was using the legacy tag-compound (pre-1.20.5 shape); now uses the components map per the target MC version.
- MSL alpha versions accepted in the dependency constraint (`>=3.0.0-alpha.1`); previously the `>=3.0.0` constraint rejected MSL pre-releases per semver pre-release ordering, causing a Fabric Loader incompatibility at startup.

![collage (36)-min](https://pub-24a4e0e7ea8544a5b6f73c3a23512589.r2.dev/images/406afce8fbaa486584f5ee0567f876c3.png)
![collage (37)-min](https://pub-24a4e0e7ea8544a5b6f73c3a23512589.r2.dev/images/0c5cae1f11754bee9070818529c13564.png)
![collage (38)-min](https://pub-24a4e0e7ea8544a5b6f73c3a23512589.r2.dev/images/6fbdb09b7f374a5a94aa7465f75daf81.png)
![collage (35)-min](https://pub-24a4e0e7ea8544a5b6f73c3a23512589.r2.dev/images/f48ba0457ad64a54b4b455975212f55e.png)
![collage (34)-min](https://pub-24a4e0e7ea8544a5b6f73c3a23512589.r2.dev/images/32415571d8a4419d8752aa788b3567f8.png)
![collage (33)-min](https://pub-24a4e0e7ea8544a5b6f73c3a23512589.r2.dev/images/5602760798df44fd8d39a8eb63a431c7.png)

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
