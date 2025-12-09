# How to Add New Structures to Moog's Nether Structures

Welcome! This guide will walk you through everything you need to know to add your own custom structures to Moog's Nether Structures (MNS). Whether you're new to Minecraft modding or just new to this project, we'll explain each step in clear, friendly language.

---

## Table of Contents

1. [Overview: How It All Works](#overview-how-it-all-works)
2. [What You'll Need](#what-youll-need)
3. [File Breakdown: What Each File Does](#file-breakdown-what-each-file-does)
4. [Step-by-Step: Adding a New Structure](#step-by-step-adding-a-new-structure)
5. [Understanding the Details](#understanding-the-details)
6. [Practical Examples](#practical-examples)
7. [Tools & Resources](#tools--resources)
8. [Getting Structure NBT Files](#getting-structure-nbt-files)
9. [Submitting Your Contribution via GitHub](#submitting-your-contribution-via-github)
10. [Summary](#summary)

---

## Overview: How It All Works

### What Are Minecraft Structures?

In Minecraft, **structures** are pre-built formations like villages, temples, or fortresses that generate naturally in the world. They're stored as `.nbt` files (Named Binary Tag files), which contain all the blocks, entities, and other data needed to place the structure in the game.

### The Two Projects Working Together

Moog's Nether Structures consists of two separate but interconnected projects:

#### 1. **MoogsNetherStructures2** (The Datapack Project)
This is where all the **content** lives:
- Structure NBT files (the actual buildings)
- Configuration files (where and how structures spawn)
- Loot tables (what's in the chests)
- Biome tags (which biomes can have which structures)

Think of this as the "content pack" - it contains everything players see and interact with.

#### 2. **MoogsStructureLib** (The Library Project)
This is the **engine** that makes everything work:
- Java code that handles structure placement
- Special structure types designed for the Nether
- Advanced placement algorithms
- Height calculation and terrain adaptation logic

Think of this as the "framework" - it provides the tools that make the content work properly.

### How They Connect

When you add a new structure, you'll only work with the **MoogsNetherStructures2** project. The structure files you create will reference the library's features using the special namespace `moogs_structures:`. The library handles all the complex generation logic automatically!

---

## What You'll Need

### Software & Tools
- **Visual Studio Code (VSCode)** - For editing files and managing Git
- **Minecraft Java Edition** - For creating and testing structures
- **GitHub account** - Free to create at https://github.com

### Knowledge
- **Basic JSON understanding** (we'll explain as we go!)
- **How to create structure files** (see [Getting Structure NBT Files](#getting-structure-nbt-files))

### Files You'll Be Working With
When adding a new structure, you'll typically create **4 types of files**:
1. An NBT structure file (the building itself)
2. A structure definition JSON
3. A structure set JSON  
4. A template pool JSON
5. (Optional) A biome tag JSON
6. (Optional) A loot table JSON

Don't worry if this sounds like a lot - we'll go through each one!

---

## File Breakdown: What Each File Does

Let's understand what each file type does and where it lives in the project.

### 1. Structure NBT Files
**Location:** `src/main/resources/data/mns/structure/`

**What they are:** These are the actual structure files created in Minecraft using structure blocks. They contain all the blocks, entities, and other data.

**Example:** `shrine.nbt`, `copper_tower.nbt`

**How to create them:** See the [Getting Structure NBT Files](#getting-structure-nbt-files) section.

---

### 2. Structure Definition JSON
**Location:** `src/main/resources/data/mns/worldgen/structure/`

**What it does:** This file tells the game **how** your structure should spawn. It defines:
- Which biomes it can spawn in
- How it adapts to terrain
- Height placement rules
- Whether it can spawn in liquids

**Example file:** `shrine.json`

```json
{
  "type": "moogs_structures:moogs_structures_generic_nether_jigsaw_structure",
  "start_pool": "mns:shrine_start_pool",
  "size": 1,
  "biomes": "#mns:has_structure/nether_biomes",
  "land_search_direction": "HIGHEST_LAND",
  "cannot_spawn_in_liquid": true,

  "step": "surface_structures",
  "terrain_adaptation": "beard_thin",
  "start_height": {
    "absolute": 0
  },
  "spawn_overrides": {}
}
```

#### Key Fields Explained:

- **`type`**: Always use `"moogs_structures:moogs_structures_generic_nether_jigsaw_structure"` for Nether structures. This tells the game to use the special Nether structure handler from the library.

- **`start_pool`**: Points to your template pool (explained next). Format: `"mns:your_structure_name_start_pool"`

- **`size`**: How many "jigsaw pieces" deep the structure can generate. 
  - `1` = Simple, single-piece structure
  - `2-5` = Multi-piece structures that can add attachments
  - Higher numbers = More complex, potentially larger structures
  - **Performance impact:** Higher values can slow generation

- **`biomes`**: Which biomes this structure can spawn in. The `#` means it's a tag reference.
  - `"#mns:has_structure/nether_biomes"` = All nether biomes
  - `"#mns:has_structure/crimson_biomes"` = Only crimson forest
  - `"#mns:has_structure/warped_biomes"` = Only warped forest
  - `"#mns:has_structure/soul_biomes"` = Soul sand valley
  - `"#mns:has_structure/nether_wastes_biomes"` = Nether wastes

- **`land_search_direction`**: Determines how the game searches for a valid spawn location
  - `"HIGHEST_LAND"` = Searches **from the top downward** to find the highest solid surface with air above it
    - Perfect for: Towers, shrines, buildings, monuments - anything that should sit ON TOP of terrain
    - Behavior: Starts near the Nether ceiling and scans downward until it finds solid ground
    - Result: Structure spawns on peaks, plateaus, and the highest available surface
  - `"LOWEST_LAND"` = Searches **from the bottom upward** to find the lowest floor with air above it
    - Perfect for: Pools, pits, valley structures, underground features - anything that should sit IN LOW SPOTS
    - Behavior: Starts near the lava ocean level and scans upward until it finds a floor with open space above
    - Result: Structure spawns in depressions, valleys, and low-lying areas

- **`project_start_to_heightmap`**: How to measure height
  - `"WORLD_SURFACE_WG"` = Top of terrain (most common)
  - Other options exist but are rarely used

- **`cannot_spawn_in_liquid`**: 
  - `true` = Won't spawn if lava/water is in the way
  - `false` = Can spawn even in liquids
  - **Tip:** Usually `true` for Nether to avoid lava lakes

- **`terrain_height_radius_check`**: How many **chunks** around the spawn chunk to check for terrain flatness
  - `1` = Checks 1 chunk radius (3x3 chunks = 48x48 blocks) - moderately forgiving
  - `2` = Checks 2 chunk radius (5x5 chunks = 80x80 blocks) - needs flatter terrain
  - `5` = Checks 5 chunk radius (11x11 chunks = 176x176 blocks) - very strict flatness requirement
  - **Important:** This is in chunks (16 blocks each), not individual blocks!
  - **Effect on rarity:** Larger values = harder to find valid spots = much rarer structure
  - **Performance impact:** Larger values = more chunks to check = slower generation

- **`allowed_terrain_height_range`**: How much height variation is allowed in the checked area
  - `3` = Terrain can vary by 3 blocks (fairly flat)
  - `10` = Terrain can vary by 10 blocks (very hilly/uneven)
  - Lower values = structure spawns only on flat areas = rarer
  - Higher values = structure can spawn on uneven terrain = more common

- **`step`**: Generation step
  - `"surface_structures"` = Generates with other surface structures
  - Usually keep this as-is

- **`terrain_adaptation`**: How the structure blends into terrain (prevents floating gaps)
  - **What is a "beard"?** When terrain is uneven under a structure, the game adds extra blocks downward from the structure's floor to fill gaps - like a beard hanging down to meet the ground
  - `"beard_thin"` = **Recommended for most structures**
    - Adds a thin layer of blocks extending down from the structure floor
    - Fills small gaps between structure and terrain (typically 1-5 blocks)
    - Natural-looking, doesn't add excessive blocks
    - Example: A house on slightly uneven ground gets its floor extended down to touch terrain
  - `"beard_box"` = **For large flat structures**
    - Creates a solid box/pillar of blocks under the entire structure footprint
    - Fills all gaps completely, even large ones
    - More visible and can look artificial if terrain is very uneven
    - Good for: Large platforms, temples, fortresses that need stable foundations
  - `"bury"` = **For underground/half-buried structures**
    - Pushes the structure into the terrain, partially burying it
    - Lower parts of structure end up underground
    - Good for: Ruins, dungeons, buried temples
  - `"none"` = **No adaptation (use with caution!)**
    - Structure places exactly as built with no terrain modification
    - Will float if terrain drops below it
    - Will clip into terrain if terrain rises above it
    - Only use if you want floating structures or have perfect flat terrain

- **`start_height`**: Initial Y-level before terrain adjustments
  - **For Nether structures, use:** `{"absolute": 0}` (standard for all Nether structures in this mod)
  - This is the base Y-level before `land_search_direction` finds the actual placement height
  - The Nether structure handler ignores `project_start_to_heightmap` and uses `land_search_direction` instead
  - **Advanced options:** You can use other height providers like `uniform` for random heights, but `{"absolute": 0}` works for 99% of cases

- **`project_start_to_heightmap`**: Heightmap reference (inherited from vanilla but mostly ignored for Nether structures)
  - **For Nether structures:** Use `"WORLD_SURFACE_WG"` (standard)
  - The Nether structure type uses `land_search_direction` instead of this for placement
  - This field is used for terrain flatness checks, so keep it set to `"WORLD_SURFACE_WG"`
  - **Note:** Regular overworld structures use this for placement, but Nether structures have custom logic

- **`spawn_overrides`**: Controls which mobs can spawn inside your structure
  - **Empty `{}`** = Use biome's normal mob spawning (most common)
  - **Custom spawns** = Override biome spawning with specific mobs for your structure
  
  **When to use custom spawns:**
  - Add guardian mobs to a fortress (e.g., Wither Skeletons, Blazes)
  - Create ambient mobs for atmosphere (e.g., Bats, Parrots)
  - Prevent ALL mobs from spawning (like Ancient Cities do)
  - Make structures more dangerous or unique
  
  **Basic structure:**
  ```json
  "spawn_overrides": {
    "monster": {
      "bounding_box": "piece",
      "spawns": [
        {
          "type": "minecraft:wither_skeleton",
          "weight": 100,
          "minCount": 2,
          "maxCount": 4
        }
      ]
    }
  }
  ```
  
  **Key fields:**
  - **Category** (choose one or more):
    - `monster` = Hostile mobs (zombies, skeletons, etc.)
    - `creature` = Passive mobs (pigs, cows, etc.)
    - `ambient` = Ambient mobs (bats)
    - `water_creature` = Water animals (fish, dolphins)
    - `underground_water_creature` = Glow squids
    - `water_ambient` = Small water mobs (tropical fish)
    - `misc` = Miscellaneous (usually unused)
    - `axolotls` = Axolotls specifically
  
  - **`bounding_box`**: Where mobs can spawn
    - `"piece"` = Only inside individual structure pieces (recommended)
    - `"full"` = Anywhere in the full structure bounding box (can spawn outside walls!)
  
  - **`spawns`**: Array of mob types (can be empty `[]` to block spawns)
    - `type` = Entity ID (e.g., `"minecraft:blaze"`)
    - `weight` = Spawn chance (higher = more common, relative to other mobs)
    - `minCount` = Minimum mobs per spawn (≥ 1)
    - `maxCount` = Maximum mobs per spawn (≥ minCount)
  
  **Examples:**
  
  **Block all monster spawning (peaceful structure):**
  ```json
  "spawn_overrides": {
    "monster": {
      "bounding_box": "piece",
      "spawns": []
    }
  }
  ```
  
  **Add dangerous Nether mobs:**
  ```json
  "spawn_overrides": {
    "monster": {
      "bounding_box": "piece",
      "spawns": [
        {
          "type": "minecraft:blaze",
          "weight": 50,
          "minCount": 1,
          "maxCount": 2
        },
        {
          "type": "minecraft:wither_skeleton",
          "weight": 100,
          "minCount": 2,
          "maxCount": 4
        },
        {
          "type": "minecraft:piglin_brute",
          "weight": 30,
          "minCount": 1,
          "maxCount": 1
        }
      ]
    }
  }
  ```
  
  **Add ambient atmosphere:**
  ```json
  "spawn_overrides": {
    "ambient": {
      "bounding_box": "piece",
      "spawns": [
        {
          "type": "minecraft:bat",
          "weight": 100,
          "minCount": 1,
          "maxCount": 3
        }
      ]
    }
  }
  ```
  
  **Tips:**
  - Higher weight = more common (e.g., weight 100 spawns twice as often as weight 50)
  - Keep `minCount` and `maxCount` reasonable (1-4 for most mobs)
  - Use `"bounding_box": "piece"` to prevent spawns outside structure walls
  - Test thoroughly - too many mobs can make structures overwhelming!
  - Leave empty `{}` if you want normal biome spawning
  
  **🛠️ Tool to help:** Use [Misode's Structure Generator](https://misode.github.io/worldgen/structure/) to visually create spawn_overrides configurations. It provides a user-friendly interface for setting up mob spawns without writing JSON by hand!

---

### 3. Structure Set JSON
**Location:** `src/main/resources/data/mns/worldgen/structure_set/`

**What it does:** This file controls **how frequently** your structure spawns and the **spacing** between instances.

**Example file:** `shrine.json`

```json
{
  "structures": [
    {
      "structure": "mns:shrine",
      "weight": 1
    }
  ],
  "placement": {
    "type": "moogs_structures:advanced_random_spread",
    "salt": 776654657,
    "spacing": 24,
    "separation": 17
  }
}
```

#### Key Fields Explained:

- **`structures`**: Array of structures in this set
  - **`structure`**: Reference to your structure definition file
  - **`weight`**: Relative chance if multiple structures in set (usually `1`)

- **`placement`**: How structures are spaced in the world
  - **`type`**: Always use `"moogs_structures:advanced_random_spread"` for this mod
  - **`salt`**: Random seed for placement (make it unique! Use any large random number)
  - **`spacing`**: Maximum distance between structures (in chunks)
    - **⚠️ Important:** Internally multiplied by 1.65 for actual spacing!
    - Example: `spacing: 24` actually becomes ~40 chunks
  - **`separation`**: Minimum distance between structures (in chunks)
    - **⚠️ Important:** Also multiplied by 1.65 internally!
    - Example: `separation: 17` actually becomes ~28 chunks
  
  **Advanced Optional Fields:**
  
  - **`min_distance_from_world_origin`** (optional): Prevents structures from spawning near world spawn (0, 0)
    - Value in blocks from origin
    - Example: `"min_distance_from_world_origin": 1000` = no structures within 1000 blocks of spawn
    - Useful for: End-game structures, dangerous areas that shouldn't be near spawn
  
  - **`spread_type`** (optional): Distribution pattern (rarely needed)
    - `"LINEAR"` (default) - Standard distribution, use this
  
  - **`frequency`** (optional): Chance for structure to actually spawn (0.0 to 1.0)
    - `1.0` (default) - Always tries to spawn
    - `0.5` - 50% chance to spawn at valid locations
    - `0.1` - 10% chance (makes structures much rarer!)
    - Useful for: Creating ultra-rare structures without huge spacing values
  
  - **`frequency_reduction_method`** (optional): How frequency reduction is calculated
    - `"DEFAULT"` (standard) - Use this unless you have a specific reason
  
  - **`locate_offset`** (optional): Offset for the `/locate` command search
    - Rarely needed, defaults to `[0, 0, 0]`
  
  - **`exclusion_zone`** (optional, vanilla feature): Prevents spawning near other vanilla structure sets
    - Advanced feature - see vanilla structure documentation
  
  - **`super_exclusion_zone`** (optional, custom feature): Advanced control over structure conflicts
    - **`other_set`**: List of structure sets to check against
    - **`chunk_count`**: Minimum distance in chunks from other structures
    - **`allowed_chunk_count`**: Maximum distance that must have another structure nearby
    - Useful for: Ensuring structures don't spawn too close OR too far from each other

#### Understanding Spacing & Separation:

Think of it like this:
- **Spacing** = "Don't place another one more than X chunks away"
- **Separation** = "Don't place another one closer than Y chunks away"

**⚠️ CRITICAL: The 1.65x Multiplier**
- `advanced_random_spread` automatically multiplies both values by 1.65
- This is built into the placement algorithm
- **Calculate actual distances:** `your_value × 1.65 × 16 blocks per chunk`

**Examples (with actual distances after 1.65x multiplier):**
- `spacing: 24, separation: 17` = Common
  - Actual: 40-28 chunks = 640-448 blocks apart
- `spacing: 40, separation: 37` = Rare
  - Actual: 66-61 chunks = 1056-976 blocks apart
- `spacing: 10, separation: 5` = Very common
  - Actual: 17-8 chunks = 272-128 blocks apart
- `spacing: 60, separation: 55` = Very rare
  - Actual: 99-91 chunks = 1584-1456 blocks apart

**Important Rules:**
- Separation must be less than spacing (will error if not)
- Keep the multiplier in mind when setting values
- Structures will be ~65% further apart than your raw values suggest!

**Performance Note:** Very common structures (low spacing) can impact world generation performance.

---

#### Advanced Placement Examples:

**Example 1: End-game structure that spawns far from spawn**
```json
{
  "structures": [
    {
      "structure": "mns:boss_fortress",
      "weight": 1
    }
  ],
  "placement": {
    "type": "moogs_structures:advanced_random_spread",
    "salt": 123456789,
    "spacing": 80,
    "separation": 75,
    "min_distance_from_world_origin": 2000
  }
}
```
- Extremely rare (80/75 spacing)
- Won't spawn within 2000 blocks of spawn (0, 0)
- Perfect for dangerous end-game content

**Example 2: Ultra-rare legendary structure**
```json
{
  "structures": [
    {
      "structure": "mns:legendary_temple",
      "weight": 1
    }
  ],
  "placement": {
    "type": "moogs_structures:advanced_random_spread",
    "salt": 987654321,
    "spacing": 40,
    "separation": 35,
    "frequency": 0.25
  }
}
```
- Medium spacing (40/35)
- Only 25% chance to spawn at valid locations
- Result: Extremely rare without huge spacing values
- Good for special legendary structures

---

### 4. Template Pool JSON
**Location:** `src/main/resources/data/mns/worldgen/template_pool/`

**What it does:** This file links your structure definition to the actual NBT file and configures how it loads.

**Example file:** `shrine_start_pool.json`

```json
{
  "fallback": "minecraft:empty",
  "elements": [
    {
      "weight": 1,
      "element": {
        "location": "mns:shrine",
        "processors": "minecraft:empty",
        "projection": "rigid",
        "element_type": "minecraft:single_pool_element"
      }
    }
  ]
}
```

#### Key Fields Explained:

- **`fallback`**: What to use if this pool fails to load
  - Always use `"minecraft:empty"` (loads nothing instead of crashing)

- **`elements`**: Array of structure pieces that can be placed
  - **`weight`**: Chance of picking this element (higher = more likely)
  - Multiple elements let you have variations!

- **`element`**: The actual structure piece configuration
  - **`location`**: Path to your NBT file (without `.nbt` extension)
    - Format: `"mns:structure_name"` 
    - Points to: `data/mns/structure/structure_name.nbt`
  
  - **`processors`**: Processor list to apply (usually `"minecraft:empty"`)
    - Processors can randomize blocks, add decay, etc.
    - https://misode.github.io/worldgen/processor-list/
  
  - **`projection`**: How piece connects to others
    - `"rigid"` = Structure stays exactly as built (most common)
    - `"terrain_matching"` = Structure adapts to terrain height
  
  - **`element_type`**: Type of pool element
    - `"minecraft:single_pool_element"` = Single structure file
    - Other types exist for lists or features

#### Creating Variations

You can have multiple structures that randomly select:

```json
{
  "fallback": "minecraft:empty",
  "elements": [
    {
      "weight": 3,
      "element": {
        "location": "mns:house_variant_1",
        "processors": "minecraft:empty",
        "projection": "rigid",
        "element_type": "minecraft:single_pool_element"
      }
    },
    {
      "weight": 1,
      "element": {
        "location": "mns:house_variant_2",
        "processors": "minecraft:empty",
        "projection": "rigid",
        "element_type": "minecraft:single_pool_element"
      }
    }
  ]
}
```

This creates a 75% chance of variant 1, 25% chance of variant 2!

---

### 5. Multi-Part Structures (Advanced)

For structures with multiple connected pieces (like the lava_pool), you can use the jigsaw system.

**Example structure:** `lava_pool`

**Files needed:**
- `lava_pool.json` (structure definition)
- `lava_pool_start_pool.json` (main piece)
- `lava_pool/side_pool.json` (additional pieces)
- `lava_pool.nbt` (main structure file)
- `lava_pool_lower.nbt` (side structure file)

**Folder structure:**
```
template_pool/
  ├── lava_pool/
  │   ├── start_pool.json
  │   └── side_pool.json
```

**start_pool.json:**
```json
{
  "name": "mns:lava_pool/start_pool",
  "fallback": "minecraft:empty",
  "elements": [
    {
      "weight": 1,
      "element": {
        "location": "mns:lava_pool",
        "processors": "minecraft:empty",
        "projection": "rigid",
        "element_type": "minecraft:single_pool_element"
      }
    }
  ]
}
```

**side_pool.json:**
```json
{
  "fallback": "minecraft:empty",
  "elements": [
    {
      "weight": 1,
      "element": {
        "location": "mns:lava_pool_lower",
        "processors": "minecraft:empty",
        "projection": "rigid",
        "element_type": "minecraft:single_pool_element"
      }
    }
  ]
}
```

**How jigsaw structures work:**
1. In your main NBT file, place **jigsaw blocks**
2. Jigsaw blocks define connection points
3. When the structure generates, the game looks for matching jigsaw blocks in the side pools
4. The `size` field in the structure definition determines how many levels deep it can go

**📺 Tutorial:** For a detailed walkthrough on using jigsaw blocks, watch [this YouTube tutorial](https://www.youtube.com/watch?v=5a4DAkWW3JQ).

---

### 6. Biome Tag JSON (Optional)
**Location:** `src/main/resources/data/mns/tags/worldgen/biome/has_structure/`

**What it does:** Defines groups of biomes. Instead of creating a new tag, you'll usually use existing ones:
- `nether_biomes.json` - All nether biomes
- `crimson_biomes.json` - Crimson forest only
- `warped_biomes.json` - Warped forest only  
- `soul_biomes.json` - Soul sand valley
- `nether_wastes_biomes.json` - Nether wastes

**When to create a custom tag:** Only if you need a specific combination of biomes not covered above.

**Example:** `nether_biomes.json`
```json
{
  "replace": false,
  "_comment": " This biome tag can specify the biome directly. Or specify another biome tag by starting with # ",
  "values": [
    "#minecraft:is_nether"
  ]
}
```

#### Key Fields:
- **`replace`**: Whether to replace vanilla tags
  - Always use `false` (adds to existing tags instead of replacing)
- **`values`**: Array of biome IDs or tag references
  - Tag reference: `"#minecraft:is_nether"` (all nether biomes)
  - Direct biome: `"minecraft:crimson_forest"` (specific biome)

---

#### Using Modded Biome Tags for Better Compatibility

**Important:** To ensure your structures work with modded terrain and biomes, you can reference existing biome tags from various sources.

**Available Tag Namespaces:**

**1. `minecraft:` Tags (Vanilla)**
- Standard vanilla Minecraft biome tags
- View all available tags: https://github.com/misode/mcmeta/tree/data-json/data/minecraft/tags/worldgen/biome
- Example: `"#minecraft:is_nether"`, `"#minecraft:is_overworld"`

**2. `c:` Tags (Fabric & NeoForge Standard)**
- **Recommended for best mod compatibility!**
- Standardized tags used by both Fabric and NeoForge mods
- Works across different mod loaders

**Fabric API tags:**
- https://github.com/FabricMC/fabric/tree/1.21.5/fabric-convention-tags-v2/src/generated/resources/data/c/tags/worldgen/biome

**NeoForge tags:**
- https://github.com/neoforged/NeoForge/tree/1.21.x/src/generated/resources/data/c/tags/worldgen/biome

**Example usage:**
```json
{
  "replace": false,
  "values": [
    "#c:in_nether",
    "#c:climate_hot"
  ]
}
```

**3. `forge:` Tags (Legacy Forge 1.20.1 and below)**
- **For 1.20.X and below only** - Forge switched to `c:` tags in 1.21+
- https://github.com/MinecraftForge/MinecraftForge/tree/1.20.1/src/generated/resources/data/forge/tags/worldgen/biome

**Why use modded tags?**
- ✅ Your structures will work with modded biomes automatically
- ✅ Better compatibility with popular terrain mods (Terralith, Biomes O' Plenty, etc.)
- ✅ No need to manually add every modded biome
- ✅ Follows community standards for cross-mod compatibility

**Best Practice:**
Combine vanilla and modded tags for maximum compatibility:
```json
{
  "replace": false,
  "values": [
    "#minecraft:is_nether",
    "#c:in_nether"
  ]
}
```
This ensures your structure spawns in:
- All vanilla Nether biomes
- All modded Nether biomes that follow the `c:` convention

---

#### ⚠️ IMPORTANT: Using `"required": false` for Modded Content

When referencing modded biomes or modded biome tags, **you MUST use `"required": false`** to prevent errors when the mod isn't installed.

**Why this matters:**
- If a player doesn't have a mod installed, its biomes/tags won't exist
- Without `"required": false`, your structure will fail to load and cause errors
- With `"required": false`, Minecraft will simply skip missing biomes/tags

**Correct format for modded biomes:**
```json
{
  "replace": false,
  "values": [
    "#minecraft:is_nether",
    {
      "id": "#c:in_nether",
      "required": false
    },
    {
      "id": "byg:rainbow_beach",
      "required": false
    }
  ]
}
```

**Examples:**

**Modded biome tag:**
```json
{
  "id": "#c:is_water/overworld",
  "required": false
}
```

**Specific modded biome:**
```json
{
  "id": "byg:rainbow_beach",
  "required": false
}
```

**When to use `"required": false`:**
- ✅ Always for modded biome tags (`#c:`, `#byg:`, `#terralith:`, etc.)
- ✅ Always for specific modded biomes (`byg:rainbow_beach`, `terralith:skylands`, etc.)
- ❌ Not needed for vanilla tags (`#minecraft:is_nether` works without it)

**Complete example with mixed vanilla and modded biomes:**
```json
{
  "replace": false,
  "values": [
    "#minecraft:is_nether",
    {
      "id": "#c:in_nether",
      "required": false
    },
    {
      "id": "#c:climate_hot",
      "required": false
    },
    {
      "id": "byg:crimson_gardens",
      "required": false
    },
    {
      "id": "byg:embur_bog",
      "required": false
    }
  ]
}
```

This way, your structure will:
- ✅ Work in vanilla Nether biomes (always)
- ✅ Work in modded Nether biomes (when mods are installed)
- ✅ Not crash (when mods aren't installed)

---

### 7. Loot Table JSON (Optional)
**Location:** `src/main/resources/data/mns/loot_table/chests/`

**What it does:** Defines what items appear in chests within your structure.

**Example:** `treasure.json` (simplified)
```json
{
  "type": "minecraft:chest",
  "pools": [
    {
      "rolls": 3,
      "entries": [
        {
          "type": "minecraft:item",
          "weight": 15,
          "name": "minecraft:netherite_ingot",
          "functions": [
            {
              "function": "minecraft:set_count",
              "count": 1
            }
          ]
        },
        {
          "type": "minecraft:item",
          "weight": 10,
          "name": "minecraft:ancient_debris",
          "functions": [
            {
              "function": "minecraft:set_count",
              "count": 1
            }
          ]
        }
      ]
    }
  ]
}
```

#### Key Fields:
- **`type`**: Always `"minecraft:chest"` for chest loot
- **`pools`**: Array of item groups
  - **`rolls`**: How many items to pick from this pool
  - **`entries`**: Items that can be selected
    - **`weight`**: Relative chance (higher = more common)
    - **`name`**: Item ID
    - **`functions`**: Modify the item (count, damage, enchantments, etc.)

**Tip:** Use [Misode's Loot Table Generator](https://misode.github.io/loot-table/) to create these easily!

---

#### ⚖️ Balancing Loot Tables - IMPORTANT!

**Loot balance is critical to game design.** The rewards must match the structure's difficulty and rarity.

**The Golden Rule:**
- **Good enough** to make players want to explore your structures
- **Not so good** that it trivializes the game's difficulty and progression

**Balancing Guidelines:**

**For Common, Easy-to-Access Structures:**
- ✅ Basic resources (iron, gold, food)
- ✅ Minor enchanted items (low-level enchants, damaged)
- ✅ Utility items (blocks, torches, basic tools)
- ❌ **NO** diamonds, netherite, or high-value items
- ❌ **NO** powerful enchanted gear
- **Example:** A small shrine with a few gold ingots and some food

**For Medium Rarity, Moderate Danger:**
- ✅ Some valuable resources (few diamonds, gold blocks)
- ✅ Moderately enchanted gear (random enchants, medium damage)
- ✅ Useful consumables (potions, ender pearls)
- ⚠️ Limit quantities - don't flood the player with resources
- **Example:** A fortress with hostile mobs, containing 2-4 diamonds and an enchanted iron sword

**For Rare, Highly Dangerous Structures:**
- ✅ Valuable loot (diamonds, ancient debris, netherite scraps)
- ✅ Well-enchanted gear (good enchants, low damage)
- ✅ Rare items (enchanted golden apples, special materials)
- ✅ Higher quantities acceptable since they're hard to find
- **Example:** A boss fortress with multiple dangers, containing netherite and powerful gear

**Key Principles:**

1. **Accessibility = Lower Rewards**
   - If players can easily reach the loot without danger, keep it modest
   - Require combat, parkour, or puzzle-solving for better rewards

2. **Rarity = Better Rewards**
   - Common structures (low spacing) should have basic loot
   - Rare structures (high spacing) can have valuable loot
   - Players should feel rewarded for the time spent searching

3. **Risk = Reward**
   - More mobs = better loot
   - Dangerous mob types (Wither Skeletons, Blazes) = even better loot
   - Traps and hazards justify higher-value items

4. **Don't Break Progression**
   - Early-game accessible structures shouldn't give late-game items
   - Consider using `min_distance_from_world_origin` for powerful loot structures
   - Let players earn their progression naturally

5. **Make It Fun!**
   - Even basic structures should have *something* worthwhile
   - A small reward is better than none - keeps exploration engaging
   - Consider adding easter eggs or unique (but not overpowered) items

**Testing Your Balance:**
- ✅ Find the structure in a test world
- ✅ Compare loot to the effort required
- ✅ Ask: "Would I be excited to find this, but not break the game?"
- ✅ Consider where in player progression this structure typically spawns

---

#### Placing Chests with Loot Tables in Your Structure

**Important:** When building your structure, you need to place chests (or barrels) with the loot table already configured. This ensures the loot generates correctly when players find the structure.

**⚠️ CRITICAL WARNING:**
- **DO NOT open the chest after placing it with a loot table!**
- Opening the chest will overwrite the loot table data and generate random loot
- The chest must remain unopened until you export the structure

**How to get a chest with a loot table:**

Use this command to give yourself a pre-configured chest:

```
/give @s chest[container_loot={loot_table:"mns:chests/treasure"}] 1
```

**Replace the loot table path with your own:**
- `mns:chests/treasure` - For the treasure loot table
- `mns:chests/houses` - For the houses loot table
- `mns:chests/uncommon` - For the uncommon loot table
- `mns:chests/your_custom_loot` - For your own custom loot table

**For other containers:**

**Barrel with loot table:**
```
/give @s barrel[container_loot={loot_table:"mns:chests/treasure"}] 1
```

**Trapped chest with loot table:**
```
/give @s trapped_chest[container_loot={loot_table:"mns:chests/treasure"}] 1
```

**Step-by-step process:**

1. **Create your loot table** in `src/main/resources/data/mns/loot_table/chests/your_loot.json`

2. **Get the chest with the command:**
   ```
   /give @s chest[container_loot={loot_table:"mns:chests/your_loot"}] 1
   ```

3. **Place the chest in your structure** where you want loot to appear

4. **DO NOT OPEN IT!** Leave it closed

5. **Save the structure** using structure blocks

6. **Export the NBT file** - The chest will now have the loot table data saved

**Verification:**
After placing a chest with a loot table, you can verify it worked by using:
```
/data get block ~ ~ ~ LootTable
```
Stand next to the chest and run this command. It should show: `"mns:chests/your_loot"`

---

## Step-by-Step: Adding a New Structure

Let's walk through adding a new structure called "nether_tower" to the mod.

### Step 1: Set Up Your Development Environment

**Before creating your structure files, set up your workspace in VSCode:**

1. **Fork the repository on GitHub:**
   - Go to https://github.com/FinnSetchell/MoogsNetherStructures2
   - Click the **"Fork"** button in the top-right
   - This creates your own copy of the project

2. **Clone your fork in VSCode:**
   - Open VSCode
   - Press `Ctrl+Shift+P` (Command Palette)
   - Type: `Git: Clone`
   - Paste your fork URL: `https://github.com/YourUsername/MoogsNetherStructures2.git`
   - Choose where to save it and click "Open"

3. **Create a new branch for your structure:**
   - Press `Ctrl+Shift+G` to open Source Control
   - Click the branch name at the bottom-left (says "1.21-datapack")
   - Select "Create new branch..."
   - Name it: `add-nether-tower`

**Why do this first?** Setting up Git first means all your files are tracked from the start, making it easier to commit and share your work!

---

### Step 2: Create Your Structure NBT File

1. Create your structure in Minecraft using structure blocks
2. Export it as an NBT file
3. Name it `nether_tower.nbt`
4. Copy it to your cloned project: `src/main/resources/data/mns/structure/nether_tower.nbt`

(See [Getting Structure NBT Files](#getting-structure-nbt-files) for detailed instructions)

---

### Step 3: Create the Template Pool

**File:** `src/main/resources/data/mns/worldgen/template_pool/nether_tower_start_pool.json`

```json
{
  "fallback": "minecraft:empty",
  "elements": [
    {
      "weight": 1,
      "element": {
        "location": "mns:nether_tower",
        "processors": "minecraft:empty",
        "projection": "rigid",
        "element_type": "minecraft:single_pool_element"
      }
    }
  ]
}
```

**What we did:**
- Named the pool `nether_tower_start_pool` (by filename)
- Pointed to our NBT at `mns:nether_tower`
- Used standard settings

---

### Step 4: Create the Structure Definition

**File:** `src/main/resources/data/mns/worldgen/structure/nether_tower.json`

```json
{
  "type": "moogs_structures:moogs_structures_generic_nether_jigsaw_structure",
  "start_pool": "mns:nether_tower_start_pool",
  "size": 1,
  "biomes": "#mns:has_structure/nether_biomes",
  "land_search_direction": "HIGHEST_LAND",
  "cannot_spawn_in_liquid": true,
  "step": "surface_structures",
  "terrain_adaptation": "beard_thin",
  "start_height": {
    "absolute": 0
  },
  "spawn_overrides": {}
}
```

**What we did:**
- Used the Nether structure type from the library
- Referenced our template pool: `"mns:nether_tower_start_pool"`
- Set `land_search_direction` to `"HIGHEST_LAND"` (searches top-down to find the highest surface for the tower to sit on)
- Made it work in all nether biomes
- Set moderate terrain requirements (radius 2, range 4)

---

### Step 5: Create the Structure Set

**File:** `src/main/resources/data/mns/worldgen/structure_set/nether_tower.json`

```json
{
  "structures": [
    {
      "structure": "mns:nether_tower",
      "weight": 1
    }
  ],
  "placement": {
    "type": "moogs_structures:advanced_random_spread",
    "salt": 982736451,
    "spacing": 30,
    "separation": 22
  }
}
```

**What we did:**
- Referenced our structure: `"mns:nether_tower"`
- Generated a random salt: `982736451` (use any big number!)
- Set spacing to 30, separation to 22 (medium rarity)

---

### Step 6: (Optional) Create a Loot Table

**File:** `src/main/resources/data/mns/loot_table/chests/nether_tower.json`

```json
{
  "type": "minecraft:chest",
  "pools": [
    {
      "rolls": 3,
      "entries": [
        {
          "type": "minecraft:item",
          "weight": 10,
          "name": "minecraft:diamond"
        },
        {
          "type": "minecraft:item",
          "weight": 5,
          "name": "minecraft:netherite_ingot"
        },
        {
          "type": "minecraft:item",
          "weight": 15,
          "name": "minecraft:gold_ingot",
          "functions": [
            {
              "function": "minecraft:set_count",
              "count": {
                "type": "minecraft:uniform",
                "min": 3,
                "max": 8
              }
            }
          ]
        }
      ]
    }
  ]
}
```

**What we did:**
- Created a chest loot table
- Added 3 rolls per chest
- Added diamond (weight 10), netherite (weight 5), and gold ingots (weight 15)
- Gold ingots give 3-8 per drop

**To use this loot table in your structure:**
Use the `/give` command to get a chest with the loot table pre-configured:
```
/give @s chest[container_loot={loot_table:"mns:chests/nether_tower"}] 1
```
Then place it in your structure. **See [Placing Chests with Loot Tables](#placing-chests-with-loot-tables-in-your-structure) for complete instructions.**

---

### Step 7: Test Your Structure

1. Build the mod (see your build system instructions)
2. Launch Minecraft with the mod installed
3. Create a new world or explore the Nether
4. Use the locate command: `/locate structure mns:nether_tower`
5. Teleport to it: Click the coordinates in chat

---

### Step 8: Adjust as Needed

If your structure is:
- **Too common:** Increase spacing and separation values
- **Too rare:** Decrease spacing and separation values
- **Not spawning:** Check terrain requirements (increase `allowed_terrain_height_range` or decrease `terrain_height_radius_check`)
- **Spawning in weird places:** Adjust `land_search_direction` and terrain settings
- **Floating with gaps:** Change `terrain_adaptation` to `"beard_thin"` (adds blocks underneath to fill gaps)
- **Needs more support:** Use `terrain_adaptation: "beard_box"` (creates solid pillars)

---

### Step 9: Commit and Push Your Changes

Now that your structure is complete and tested, it's time to save and upload your work to GitHub!

1. **Open Source Control panel:**
   - Press `Ctrl+Shift+G`

2. **Stage your files:**
   - You'll see all your new files under "Changes"
   - Click the **+** button next to "Changes" to stage all files
   - Or click **+** next to individual files

3. **Write your commit message:**
   ```
   Add Nether Tower structure
   
   Adds a new rare tower structure that spawns in all Nether biomes with treasure loot.
   Spacing: 30/22 (medium rarity), spawns on highest land with terrain adaptation.
   ```

4. **Commit:**
   - Click the **✓ Commit** button (or press `Ctrl+Enter`)

5. **Push to GitHub:**
   - Click the **•••** menu in Source Control
   - Select "Push"
   - Or click "Publish Branch" if this is your first push
   - Wait for the upload to complete

6. **Create a Pull Request:**
   - See the [Submitting Your Contribution via GitHub](#submitting-your-contribution-via-github) section for detailed PR instructions

**Your structure is now ready for review!** The maintainers will review your PR and provide feedback.

---

## Understanding the Details

### Namespace Rules

When creating files, follow these namespace rules:

✅ **Use `moogs_structures:`** for:
- Structure type: `"moogs_structures:moogs_structures_generic_nether_jigsaw_structure"`
- Placement type: `"moogs_structures:advanced_random_spread"`

✅ **Use `mns:`** for:
- Your structures: `"mns:nether_tower"`
- Your pools: `"mns:nether_tower_start_pool"`
- Your NBT files: `"mns:nether_tower"`
- Your biome tags: `"#mns:has_structure/nether_biomes"`
- Your loot tables: `"mns:chests/nether_tower"`

✅ **Use `minecraft:`** for:
- Vanilla elements: `"minecraft:single_pool_element"`
- Vanilla processors: `"minecraft:empty"`
- Vanilla items: `"minecraft:diamond"`
- Vanilla functions: `"minecraft:set_count"`

---

## Practical Examples

### Example 1: Simple Surface Structure

A small shrine that spawns commonly on flat areas.

**Structure:** `small_shrine.nbt` (10x10x8 blocks)

**Template Pool:** `small_shrine_start_pool.json`
```json
{
  "fallback": "minecraft:empty",
  "elements": [
    {
      "weight": 1,
      "element": {
        "location": "mns:small_shrine",
        "processors": "minecraft:empty",
        "projection": "rigid",
        "element_type": "minecraft:single_pool_element"
      }
    }
  ]
}
```

**Structure Definition:** `small_shrine.json`
```json
{
  "type": "moogs_structures:moogs_structures_generic_nether_jigsaw_structure",
  "start_pool": "mns:small_shrine_start_pool",
  "size": 1,
  "biomes": "#mns:has_structure/nether_biomes",
  "land_search_direction": "HIGHEST_LAND",
  "cannot_spawn_in_liquid": true,

  "step": "surface_structures",
  "terrain_adaptation": "beard_thin",
  "start_height": {
    "absolute": 0
  },
  "spawn_overrides": {}
}
```

**Structure Set:** `small_shrine.json`
```json
{
  "structures": [
    {
      "structure": "mns:small_shrine",
      "weight": 1
    }
  ],
  "placement": {
    "type": "moogs_structures:advanced_random_spread",
    "salt": 445566778,
    "spacing": 18,
    "separation": 12
  }
}
```

**Why these settings?**
- Small terrain check (`radius_check: 1` = 3x3 chunks) suitable for a small structure
- Low height range (`3` blocks) to ensure relatively flat area
- Common spacing (`18, 12`) because it's decorative
- `HIGHEST_LAND` searches top-down to find the highest surface, placing the shrine on top of terrain

---

### Example 2: Rare Treasure Structure

A large fortress that spawns rarely and contains valuable loot.

**Structure:** `nether_fortress.nbt` (30x30x20 blocks)

**Template Pool:** `nether_fortress_start_pool.json`
```json
{
  "fallback": "minecraft:empty",
  "elements": [
    {
      "weight": 1,
      "element": {
        "location": "mns:nether_fortress",
        "processors": "minecraft:empty",
        "projection": "rigid",
        "element_type": "minecraft:single_pool_element"
      }
    }
  ]
}
```

**Structure Definition:** `nether_fortress.json`
```json
{
  "type": "moogs_structures:moogs_structures_generic_nether_jigsaw_structure",
  "start_pool": "mns:nether_fortress_start_pool",
  "size": 1,
  "biomes": "#mns:has_structure/nether_biomes",
  "land_search_direction": "HIGHEST_LAND",
  "cannot_spawn_in_liquid": true,
  "step": "surface_structures",
  "terrain_adaptation": "beard_box",
  "start_height": {
    "absolute": 0
  },
  "spawn_overrides": {}
}
```

**Structure Set:** `nether_fortress.json`
```json
{
  "structures": [
    {
      "structure": "mns:nether_fortress",
      "weight": 1
    }
  ],
  "placement": {
    "type": "moogs_structures:advanced_random_spread",
    "salt": 887766554,
    "spacing": 50,
    "separation": 45
  }
}
```

**Loot Table:** `nether_fortress.json`
```json
{
  "type": "minecraft:chest",
  "pools": [
    {
      "rolls": 5,
      "entries": [
        {
          "type": "minecraft:item",
          "weight": 10,
          "name": "minecraft:netherite_ingot"
        },
        {
          "type": "minecraft:item",
          "weight": 5,
          "name": "minecraft:ancient_debris",
          "functions": [
            {
              "function": "minecraft:set_count",
              "count": {
                "type": "minecraft:uniform",
                "min": 2,
                "max": 4
              }
            }
          ]
        },
        {
          "type": "minecraft:item",
          "weight": 15,
          "name": "minecraft:diamond",
          "functions": [
            {
              "function": "minecraft:set_count",
              "count": {
                "type": "minecraft:uniform",
                "min": 3,
                "max": 7
              }
            }
          ]
        },
        {
          "type": "minecraft:item",
          "weight": 2,
          "name": "minecraft:enchanted_golden_apple"
        }
      ]
    }
  ]
}
```

**Why these settings?**
- Large terrain check (`radius_check: 5` = 11x11 chunks) ensures a very flat area for the large fortress
- Moderate height range (`5` blocks) for reasonable flatness across that large area
- Rare spacing (`50, 45`) because it has valuable loot and should be special
- `beard_box` adaptation creates solid foundation pillars, perfect for a large fortress that needs stable footing
- 5 rolls in loot table for generous rewards

---

### Example 3: Structure with Variations

A house that has 3 different designs that randomly spawn.

**Structures:** 
- `house_variant_1.nbt`
- `house_variant_2.nbt`
- `house_variant_3.nbt`

**Template Pool:** `house_start_pool.json`
```json
{
  "fallback": "minecraft:empty",
  "elements": [
    {
      "weight": 5,
      "element": {
        "location": "mns:house_variant_1",
        "processors": "minecraft:empty",
        "projection": "rigid",
        "element_type": "minecraft:single_pool_element"
      }
    },
    {
      "weight": 3,
      "element": {
        "location": "mns:house_variant_2",
        "processors": "minecraft:empty",
        "projection": "rigid",
        "element_type": "minecraft:single_pool_element"
      }
    },
    {
      "weight": 1,
      "element": {
        "location": "mns:house_variant_3",
        "processors": "minecraft:empty",
        "projection": "rigid",
        "element_type": "minecraft:single_pool_element"
      }
    }
  ]
}
```

**Structure Definition:** `house.json`
```json
{
  "type": "moogs_structures:moogs_structures_generic_nether_jigsaw_structure",
  "start_pool": "mns:house_start_pool",
  "size": 1,
  "biomes": "#mns:has_structure/nether_biomes",
  "land_search_direction": "HIGHEST_LAND",
  "cannot_spawn_in_liquid": true,
  "step": "surface_structures",
  "terrain_adaptation": "beard_thin",
  "start_height": {
    "absolute": 0
  },
  "spawn_overrides": {}
}
```

**Structure Set:** `house.json`
```json
{
  "structures": [
    {
      "structure": "mns:house",
      "weight": 1
    }
  ],
  "placement": {
    "type": "moogs_structures:advanced_random_spread",
    "salt": 112233445,
    "spacing": 25,
    "separation": 18
  }
}
```

**Why these settings?**
- Three variants with different weights (5:3:1 ratio)
- Variant 1 spawns ~55% of the time
- Variant 2 spawns ~33% of the time
- Variant 3 spawns ~11% of the time (rare variant!)
- This adds variety to the world

---

### Example 4: Pool/Valley Structure

A lava pool that spawns in valleys.

**Template Pool:** `lava_pool_start_pool.json`
```json
{
  "name": "mns:lava_pool/start_pool",
  "fallback": "minecraft:empty",
  "elements": [
    {
      "weight": 1,
      "element": {
        "location": "mns:lava_pool",
        "processors": "minecraft:empty",
        "projection": "rigid",
        "element_type": "minecraft:single_pool_element"
      }
    }
  ]
}
```

**Structure Definition:** `lava_pool.json`
```json
{
  "type": "moogs_structures:moogs_structures_generic_nether_jigsaw_structure",
  "start_pool": "mns:lava_pool/start_pool",
  "size": 1,
  "biomes": "#mns:has_structure/nether_biomes",
  "land_search_direction": "LOWEST_LAND",
  "cannot_spawn_in_liquid": true,

  "step": "surface_structures",
  "terrain_adaptation": "beard_thin",
  "start_height": {
    "absolute": 0
  },
  "spawn_overrides": {}
}
```

**Structure Set:** `lava_pool.json`
```json
{
  "structures": [
    {
      "structure": "mns:lava_pool",
      "weight": 1
    }
  ],
  "placement": {
    "type": "moogs_structures:advanced_random_spread",
    "salt": 998877665,
    "spacing": 28,
    "separation": 20
  }
}
```

**Key difference:**
- `"land_search_direction": "LOWEST_LAND"` searches from bottom-up to find the lowest floor, making it spawn in valleys and depressions
- Starts searching from near the lava ocean level and scans upward
- Perfect for pools, pits, or buried structures that should sit in low spots!

---

## Tools & Resources

### Essential Tools

#### 1. **Misode's Data Pack Generators**
The best tools for creating Minecraft data pack files!

- **Loot Table Generator:** https://misode.github.io/loot-table/
  - Visual interface for creating loot tables
  - Supports all vanilla functions and conditions
  - Exports to perfect JSON

- **Structure Generator:** https://misode.github.io/worldgen/structure/
  - **Create spawn_overrides configurations** with a visual interface

#### 2. **NBT Viewer**
For working with `.nbt` files:
- **NBT Viewer Extension:** https://open-vsx.org/extension/misodee/vscode-nbt
  - View NBT files
  - Useful for debugging structure issues

#### 3. **Text Editors**
For editing JSON files:
- **Visual Studio Code:** https://code.visualstudio.com/
  - Free, powerful editor
  - JSON syntax highlighting

#### 4. **JSON Validators**
To check your JSON syntax:
- **JSONLint:** https://jsonlint.com/
  - Validates JSON formatting
  - Shows syntax errors clearly

---

### Helpful Resources

#### Official Documentation
- **Minecraft Wiki - Structures:** https://minecraft.wiki/w/Structure
- **Minecraft Wiki - Data Packs:** https://minecraft.wiki/w/Data_pack
- **Minecraft Wiki - Jigsaw Blocks:** https://minecraft.wiki/w/Jigsaw_Block

#### Community Resources
- **MoogsStructures Discord:** https://discord.gg/S5nffJbuvA
  - Get help from the community
  - Share your structures
  - Report issues

#### Video Tutorials
- **Jigsaw Block Tutorial:** https://www.youtube.com/watch?v=5a4DAkWW3JQ - Comprehensive guide on using jigsaw blocks for multi-part structures

---

## Getting Structure NBT Files

This section explains how to create the `.nbt` structure files that Minecraft uses to generate your structures in the world.

### What Are NBT Files?

NBT (Named Binary Tag) files are Minecraft's way of storing structure data. They contain:
- Every block in the structure and its position
- Block states (rotation, waterlogged, etc.)
- Entities (mobs, armor stands, etc.)
- Tile entities (chests, signs, etc.)
- Structure size and metadata

### Using Structure Blocks

Structure blocks are the standard Minecraft tool for saving structures.

#### Step 1: Build Your Structure
1. Create your structure in a Creative mode world
2. Make note of the size (length × width × height)
3. **Size limit:** Structure blocks support up to **48×48×48 blocks**
   - ⚠️ **For structures larger than 48×48×48:** You must break your structure into multiple pieces and connect them using jigsaw blocks (see [Creating Jigsaw Structures](#creating-jigsaw-structures))

---

#### Step 2: Prepare Your Structure (IMPORTANT!)

Before saving, you need to properly prepare your structure. This step is critical for making your structure work correctly!

**1. Add Loot Chests**

Place chests (or barrels) with loot tables using the `/give` command:
```
/give @s chest[container_loot={loot_table:"mns:chests/treasure"}] 1
```
- Place the chest in your structure
- **DO NOT OPEN IT!** Opening will overwrite the loot table
- See [Placing Chests with Loot Tables](#placing-chests-with-loot-tables-in-your-structure) for full instructions

**2. Add Persistent Mobs (Optional)**

If you want specific mobs to always spawn in your structure:
1. Spawn the mob you want
2. The mob will be saved with the structure

**Note:** Don't rely solely on spawned mobs for challenge - use `spawn_overrides` for ongoing mob spawning! Or use mob spawners.

**3. Use Structure Voids for Terrain Blending**

**What are structure voids?**
Structure voids are invisible blocks that get **replaced by whatever would naturally generate** at that location.

**Get structure void:**
```
/give @s structure_void
```

**Where to use structure voids:**
- ✅ **Floor/foundation:** Place structure voids where the ground should be
  - These will become netherrack, soul sand, or whatever the biome naturally has
  - Prevents floating gaps under your structure

---

#### Step 3: Place the Structure Block
1. Get a structure block: `/give @s structure_block`
2. Place it at one corner of your structure
3. Right-click to open the interface

#### Step 4: Configure the Structure Block
1. **Mode:** Set to "Save"
2. **Structure Name:** Enter a name like `nether_tower`
3. **Relative Position:** Set the offset from the structure block to the start of your structure
   - Usually `0 0 0` if placed at the corner
4. **Structure Size:** Enter your structure's dimensions
5. **Include entities:** Check if you have mobs/armor stands to save (important for spawned mobs!)

#### Step 5: Save the Structure
1. Click "Save" button
2. The structure is now saved to your world's structures folder

#### Step 6: Export the NBT File
1. Open your world save folder:
   - Windows: `%AppData%\.minecraft\saves\[WorldName]\generated\minecraft\structures\`
   - Curseforge Launcher:  `C:\Users\[user]\curseforge\minecraft\Instances\[instance]\saves\[WorldName]\generated\minecraft\structures\`
2. Find your structure file: `nether_tower.nbt`
3. Copy it to your project:
   - `MoogsNetherStructures2/src/main/resources/data/mns/structure/nether_tower.nbt`

---

#### Step 7: Upload to the Creative Server (Recommended)

**Why upload to the server?**
We maintain a creative server that stores all structures used in the mod. This provides several benefits:
- ✅ **Centralized storage** - All structures in one accessible location
- ✅ **Easy updates** - Anyone can modify structures if needed later
- ✅ **Team access** - All developers can view and reference any structure
- ✅ **Backup** - Structures are safe even if local files are lost

**How to upload your structure:**

1. **Use WorldEdit, Litematica, or similar tools** to save and upload your structure to the creative server
   - Make sure to include everything:
     - ✅ The complete structure
     - ✅ All structure voids
     - ✅ Structure blocks (if any)
     - ✅ Jigsaw blocks (if it's a multi-part structure)
     - ✅ Chests with loot tables (still closed!)
     - ✅ Any mobs you placed

2. **Connect to the creative server** (if you have access) and paste your structure in the **MNS (Moog's Nether Structures) zone**
   - ⚠️ **Important:** The server has different zones for each structure mod
   - Make sure you save your structure in the **MNS area**, not MVS, MTR, or other mod zones
   - If you're unsure which area is for MNS, ask in Discord or DM FinnDog

3. **Label it** with a sign including your structure name and username

**Need help or don't have server access?**
- **DM @FinnDog** on the [Discord server](https://discord.gg/S5nffJbuvA)
- FinnDog will help you upload it or grant you server access

**Note:** 
- **For the mod to work:** The NBT file must be in `src/main/resources/data/mns/structure/`
- **For contributing to the project:** You must also upload to the creative server so the team can access and maintain your structure
- The server upload is about team collaboration, not technical functionality

---

### Creating Jigsaw Structures

For multi-part structures (like the `lava_pool` example), you'll need to use jigsaw blocks.

#### What Are Jigsaw Blocks?

Jigsaw blocks are connection points that tell Minecraft: "another structure piece can attach here."

#### How to Use Them

1. **Build your main structure** and save it normally
2. **Add jigsaw blocks** where you want pieces to connect:
   - Get jigsaw blocks: `/give @s jigsaw`
   - Place them at connection points (doorways, edges, etc.)
3. **Configure each jigsaw block:**
   - **Target Pool:** Which pool to pull from (e.g., `mns:lava_pool/side_pool`)
   - **Name:** Connection point name (e.g., `mns:bottom`)
   - **Target Name:** What to connect to (e.g., `mns:bottom`)
   - **Turns into:** What block replaces the jigsaw (usually `minecraft:air`)
4. **Save the structure** with the jigsaw blocks included
5. **Create pool files** for both the start and side pools (see [Multi-Part Structures](#5-multi-part-structures-advanced))

**📺 Tutorial:** For a detailed walkthrough on using jigsaw blocks, watch [this YouTube tutorial](https://www.youtube.com/watch?v=5a4DAkWW3JQ).

**Note:** Jigsaw structures are advanced! Start with simple single structures first.

---

### Best Practices

#### Size Limits
- **Single chunk:** 16×16 blocks (good for common structures)
- **Multiple chunks:** Up to 48×48 blocks (structure block limit)
- **Mega structures:** Use jigsaw system to connect multiple 48×48 pieces

#### Performance Tips
- **Keep it reasonable:** Structures over 30×30×30 can lag on generation
- **Use air blocks wisely:** Empty space is stored too, so avoid huge hollow structures
- **Optimize entity count:** Too many mobs/armor stands can cause lag
- **Test generation:** Spawn your structure multiple times to check for issues

---

## Submitting Your Contribution via GitHub

If you followed the [Step-by-Step tutorial](#step-by-step-adding-a-new-structure), you've already forked, cloned, created a branch, and pushed your changes! This section provides detailed information on creating the Pull Request and responding to feedback.

**If you haven't set up Git yet:** Go back to [Step 1: Set Up Your Development Environment](#step-1-set-up-your-development-environment) to get started.

---

### Creating a Pull Request (PR)

**What is a Pull Request?** A formal request to merge your changes into the main project.

1. Go to your fork on GitHub:
   - `https://github.com/YourUsername/MoogsNetherStructures2`
2. You'll see a banner: **"add-nether-tower had recent pushes"**
3. Click **"Compare & pull request"**
4. Fill out the PR form:

   **Title:** Clear and descriptive
   ```
   Add Nether Tower Structure
   ```

   **Description:** Detailed explanation
   ```markdown
   ## Description
   Adds a new rare tower structure to the Nether dimension.

   ## Structure Details
   - **Name:** Nether Tower
   - **Size:** 15x15x25 blocks
   - **Biomes:** All Nether biomes
   - **Rarity:** Rare (spacing: 50, separation: 45)
   - **Features:** Contains treasure loot with Netherite

   ## Files Added
   - `nether_tower.nbt`
   - `nether_tower.json` (structure definition)
   - `nether_tower_start_pool.json` (template pool)
   - `nether_tower.json` (structure set)
   - `nether_tower.json` (loot table)

   ## Testing
   - Tested in a new world
   - Structure generates correctly
   - Loot table works as expected
   - No conflicts with existing structures

   ## Screenshots
   [Include screenshots if possible!]
   ```

5. Click **"Create pull request"**

---

### Responding to Feedback

The maintainers will review your PR and may request changes.

**If changes are requested:**
1. Make the changes in your local files in VSCode
2. Stage and commit again:
   - Open Source Control (`Ctrl+Shift+G`)
   - Stage files with **+**
   - Write commit message
   - Click **✓ Commit**
3. Push your changes:
   - Click **•••** → "Push"
4. The PR automatically updates with your new changes!

**Be patient and polite:**
- Reviews may take a few days
- Be open to suggestions
- Ask questions if something is unclear

---

### Celebration! 🎉

Once your PR is approved and merged:
- Your structure is now part of the official mod!
- You'll be credited as a contributor
- Thank you for contributing to the community!

---

### Contributing Guidelines

To ensure your PR is accepted quickly:

✅ **Do:**
- Test your structure thoroughly
- Follow existing naming conventions
- Use appropriate rarity settings
- Include clear documentation
- Add screenshots if possible
- Respond to feedback promptly

❌ **Don't:**
- Copy structures from other mods without permission
- Add overpowered loot tables
- Make structures too common (causes lag)
- Submit broken or untested structures
- Ignore feedback from maintainers

---

## Summary

Congratulations! You now know how to add structures to Moog's Nether Structures!

### Quick Recap

**To add a structure, you need:**
1. ✅ An NBT structure file (the building)
2. ✅ A template pool JSON (links NBT to structure)
3. ✅ A structure definition JSON (how it spawns)
4. ✅ A structure set JSON (spacing and frequency)
5. ✅ (Optional) Loot table JSON (chest contents)
6. ✅ (Optional) Custom biome tag JSON (specific biomes)

**Key points to remember:**
- **Set up Git/VSCode first** - Fork and clone before creating files
- Use `moogs_structures:` for library features
- Use `mns:` for your own structures
- Use `minecraft:` for vanilla elements
- **Balance your loot** - Match rewards to difficulty and rarity
- **Use structure voids** for natural terrain blending
- Test thoroughly before submitting
- **Upload to creative server** for team access
- Consider performance impact

**File locations:**
- NBT files: `src/main/resources/data/mns/structure/`
- Template pools: `src/main/resources/data/mns/worldgen/template_pool/`
- Structures: `src/main/resources/data/mns/worldgen/structure/`
- Structure sets: `src/main/resources/data/mns/worldgen/structure_set/`
- Loot tables: `src/main/resources/data/mns/loot_table/chests/`
- Biome tags: `src/main/resources/data/mns/tags/worldgen/biome/has_structure/`

### What's Next?

**Level up your skills:**
1. Learn jigsaw structures for multi-part buildings
2. Experiment with `spawn_overrides` for custom mob spawning
3. Create custom biome tag combinations (including modded biomes with `"required": false`)
4. Design balanced loot tables that enhance gameplay
5. Try different `land_search_direction` and terrain adaptation settings
6. Use `super_exclusion_zone` for satellite structures
7. Master structure voids for seamless terrain blending

**Contribute to the project:**
1. Share your structures on GitHub
2. Help others in the Discord
3. Report bugs and suggest improvements
4. Create texture variants
5. Write additional documentation

---

### Additional Resources

- **Project GitHub:** https://github.com/FinnSetchell/MoogsNetherStructures2
- **Discord Server:** https://discord.gg/S5nffJbuvA
- **CurseForge Page:** https://www.curseforge.com/minecraft/mc-mods/mns-moogs-nether-structures
- **Modrinth Page:** https://modrinth.com/mod/mns-moogs-nether-structures

---

### Thank You!

Thank you for taking the time to learn about adding structures to Moog's Nether Structures! We're excited to see what amazing creations you'll build.

Remember:
- **Start simple** - Begin with a basic structure before trying complex multi-part buildings
- **Test everything** - Always test your structures before submitting
- **Ask for help** - The community is friendly and ready to assist
- **Have fun** - Creativity is encouraged!

Happy building! 🏗️✨

---

**Last Updated:** October 2025
**Compatible with:** Minecraft 1.21+
**Mod Version:** 2.0.0+

**Found an error in this guide?** Please open an issue on GitHub or let us know in Discord!

