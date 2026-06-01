"""Port arena JSON content (pools, processor_lists, structures, structure_set,
loot tables) from MoogsNetherStructures2 (1.21-datapack HEAD) to
MoogsNetherStructures2-1.20-datapack.

Transforms applied:
  - Path renames: structure/ -> structures/, loot_table/ -> loot_tables/.
  - Pool element processor ref: mns:large_arena_pillars -> mns:arena_pillars.
  - Pool element versioned_single_pool_element:
      * If the piece is item-bearing (matches ITEM_BEARING_RELS) the element
        keeps element_type=versioned, but `locations` is rewritten to
        {"1.20-1.20.4": "mns:<rel>", "1.20.5-1.20.6": "mns:v1_20_5/<rel>"}.
      * Otherwise the element is downgraded to minecraft:single_pool_element
        with `locations` dropped.
  - Processor lists: trial_spawner_randomizing_processor and
    vault_randomizing_processor entries are dropped.
  - Loot tables under chests/ are copied verbatim. trial_reward_* and
    vaults/* tables are NOT copied (skip entire trees).
  - Structure JSONs and structure_set/mega_arenas.json copied verbatim.

Item-bearing list mirrors the NBT porter; keep them in sync.
"""
import json
import os
import shutil
import sys

SRC = r"C:\Users\finn\IdeaProjects\MoogsNetherStructures2"
DST = r"C:\Users\finn\IdeaProjects\MoogsNetherStructures2-1.20-datapack"

ITEM_BEARING_RELS = {
    "small_arena/front",
    "dragon_arena/c2",
    "large_arena/l3",
    "large_arena/r3",
    "mega_arenas/mobs/arena_bowman",
    "mega_arenas/mobs/arena_gladiator",
    "mega_arenas/mobs/drakebone_tyrant",
    "mega_arenas/mobs/ember_sentinel",
    "mega_arenas/mobs/pit_brute",
    "mega_arenas/mobs/pit_vanguard",
}

# Processor-list renames inside pool element references.
PROCESSOR_RENAMES = {
    "mns:large_arena_pillars": "mns:arena_pillars",
}

# Processor types stripped from processor lists (don't exist on 1.20.x).
STRIP_PROCESSORS = {
    "moogs_structures:trial_spawner_randomizing_processor",
    "moogs_structures:vault_randomizing_processor",
}

def location_to_rel(loc):
    """'mns:large_arena/l1' -> 'large_arena/l1'"""
    if loc.startswith("mns:"):
        return loc[len("mns:"):]
    return loc


def transform_pool_element(element):
    """Mutate element in place."""
    # Processor rename
    proc = element.get("processors")
    if isinstance(proc, str) and proc in PROCESSOR_RENAMES:
        element["processors"] = PROCESSOR_RENAMES[proc]

    et = element.get("element_type")
    if et == "moogs_structures:versioned_single_pool_element":
        loc = element.get("location", "")
        rel = location_to_rel(loc)
        if rel in ITEM_BEARING_RELS:
            element["locations"] = {
                "1.20-1.20.4": f"mns:{rel}",
                "1.20.5-1.20.6": f"mns:v1_20_5/{rel}",
            }
            element["location"] = f"mns:{rel}"
        else:
            element["element_type"] = "minecraft:single_pool_element"
            if "locations" in element:
                del element["locations"]


def transform_pool(pool):
    for entry in pool.get("elements", []):
        elt = entry.get("element")
        if isinstance(elt, dict):
            transform_pool_element(elt)


def transform_processor_list(plist):
    procs = plist.get("processors", [])
    new = [p for p in procs if p.get("processor_type") not in STRIP_PROCESSORS]
    plist["processors"] = new


def copy_json(src_path, dst_path, transformer=None):
    with open(src_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    if transformer is not None:
        transformer(data)
    os.makedirs(os.path.dirname(dst_path), exist_ok=True)
    with open(dst_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
        f.write("\n")


def copy_tree_json(src_dir, dst_dir, transformer=None):
    if not os.path.isdir(src_dir):
        return 0
    n = 0
    for root, _, files in os.walk(src_dir):
        for fn in files:
            if not fn.endswith(".json"):
                continue
            sp = os.path.join(root, fn)
            rel = os.path.relpath(sp, src_dir)
            dp = os.path.join(dst_dir, rel)
            copy_json(sp, dp, transformer)
            n += 1
    return n


def main():
    counts = {}

    # ---- Pools ----
    pool_src = os.path.join(SRC, "src", "main", "resources", "data", "mns",
                            "worldgen", "template_pool")
    pool_dst = os.path.join(DST, "src", "main", "resources", "data", "mns",
                            "worldgen", "template_pool")
    for arena in ("small_arena", "large_arena", "dragon_arena", "mega_arenas"):
        n = copy_tree_json(os.path.join(pool_src, arena),
                           os.path.join(pool_dst, arena),
                           transformer=transform_pool)
        counts[f"pools/{arena}"] = n

    # ---- Processor lists ----
    pl_src = os.path.join(SRC, "src", "main", "resources", "data", "mns",
                          "worldgen", "processor_list")
    pl_dst = os.path.join(DST, "src", "main", "resources", "data", "mns",
                          "worldgen", "processor_list")
    for fn in ("arena_pillars.json", "dragon_arena_pillars.json",
               "small_arena_spawners.json"):
        sp = os.path.join(pl_src, fn)
        if os.path.isfile(sp):
            copy_json(sp, os.path.join(pl_dst, fn),
                      transformer=transform_processor_list)
            counts[f"processor_list/{fn}"] = 1

    # ---- Structures ----
    st_src = os.path.join(SRC, "src", "main", "resources", "data", "mns",
                          "worldgen", "structure")
    st_dst = os.path.join(DST, "src", "main", "resources", "data", "mns",
                          "worldgen", "structure")
    for fn in ("small_arena.json", "large_arena.json", "dragon_arena.json"):
        sp = os.path.join(st_src, fn)
        if os.path.isfile(sp):
            copy_json(sp, os.path.join(st_dst, fn))
            counts[f"structure/{fn}"] = 1

    # ---- Structure_set: replace single-arena set with mega_arenas ----
    ss_dst = os.path.join(DST, "src", "main", "resources", "data", "mns",
                          "worldgen", "structure_set")
    mega_sp = os.path.join(SRC, "src", "main", "resources", "data", "mns",
                           "worldgen", "structure_set", "mega_arenas.json")
    copy_json(mega_sp, os.path.join(ss_dst, "mega_arenas.json"))
    counts["structure_set/mega_arenas.json"] = 1

    # ---- Loot tables: chests/ subset ----
    lt_src = os.path.join(SRC, "src", "main", "resources", "data", "mns",
                          "loot_table", "chests")
    lt_dst = os.path.join(DST, "src", "main", "resources", "data", "mns",
                          "loot_tables", "chests")
    for arena in ("small_arena", "large_arena", "dragon_arena"):
        n = copy_tree_json(os.path.join(lt_src, arena),
                           os.path.join(lt_dst, arena))
        counts[f"loot/chests/{arena}"] = n

    # Skipped intentionally: spawners/<arena>/trial_reward_* and
    # vaults/<arena>/* — both rely on 1.21-only mechanics.

    print("=== Port summary ===")
    for k, v in counts.items():
        print(f"  {k}: {v}")


if __name__ == "__main__":
    main()
