# Changelog

---

## 3.0.0-alpha.2 — 2026-06-03

### Fixed
- Accept MSL alpha versions in dependency constraint. Previously MNS required MSL `>=3.0.0` which rejected `3.0.0-alpha.X` per semver pre-release ordering, causing a Fabric Loader incompatibility error at startup. Constraint relaxed to `>=3.0.0-alpha.1`.

---

## [3.0.0] - 2026-06-22

### Added
- **Mega Fortress** - A massive new nether fortress made up of 138 pieces and packed with loot, mobs and traps. This is our best structure yet across all Moogs structure mods! The mega fortress is made up of various towers with dungeons hidden beneath the lava. Bridges stretch out in all directions with stairs and towers leading to a second floor suspended from the roof with chains.
- **Dragon Arena** - A dragon skeleton sitting in lava lakes. Here you will find the most challenging mobs from the 3 new arenas and therefore, the best loot.
- **Large Arena** - A combat focused arena that is mostly buried beneath the surface. Here you will find plenty of spawners, vaults and trial spawners.
- **Small Arena** - While the easiest of the 3 arenas, don't take it lightly. There are still powerful mobs here protecting loot that's worth the visit.

Good luck!

### Changed
- Now requires Moog's Structure Lib **v3.0.0** or newer.
- Polished `mega_fortress` upper and staircase NBT pieces (re-saves with content tweaks); chain pillars lengthened so they reach the nether roof.

### Fixed
- MSL alpha versions accepted in the dependency constraint (`>=3.0.0-alpha.1`); previously the `>=3.0.0` constraint rejected MSL pre-releases per semver pre-release ordering, causing a Fabric Loader incompatibility at startup.

![collage (36)-min](https://pub-24a4e0e7ea8544a5b6f73c3a23512589.r2.dev/images/406afce8fbaa486584f5ee0567f876c3.png)
![collage (37)-min](https://pub-24a4e0e7ea8544a5b6f73c3a23512589.r2.dev/images/0c5cae1f11754bee9070818529c13564.png)
![collage (38)-min](https://pub-24a4e0e7ea8544a5b6f73c3a23512589.r2.dev/images/6fbdb09b7f374a5a94aa7465f75daf81.png)
![collage (35)-min](https://pub-24a4e0e7ea8544a5b6f73c3a23512589.r2.dev/images/f48ba0457ad64a54b4b455975212f55e.png)
![collage (34)-min](https://pub-24a4e0e7ea8544a5b6f73c3a23512589.r2.dev/images/32415571d8a4419d8752aa788b3567f8.png)
![collage (33)-min](https://pub-24a4e0e7ea8544a5b6f73c3a23512589.r2.dev/images/5602760798df44fd8d39a8eb63a431c7.png)

---

## [2.0.4] - 2026-05-06

### Added
- Empty barrels in nether structures now contain loot
- Structures now spawn in modded nether biomes on Fabric and NeoForge.
- Added direct support for Better Nether and Incendium biomes.

### Changed
- Improved terrain blending for larger structures.

### Fixed
- Fixed very small nether brick ruins not generating correctly due to a misconfigured template pool.
- Replaced 1.21 blocks that don't exist in 1.20: copper trapdoors → iron trapdoors, crafter → crafting table, waxed oxidized copper bulb → shroomlight.

---

## [2.0.3] - 2024-01-12

### Added
- Added new structures.
  ![alt text](https://i.imgur.com/WRHKrER.jpeg)

  **Bridges:**
  - bridge_1
  - bridge_2
  - bridge_3
  - bridge_4
  - bridge_5
  - bridge_6

---
