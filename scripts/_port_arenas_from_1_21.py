"""Port the arena NBTs from MoogsNetherStructures2 (HEAD = 1.21-datapack)
into the 1.20-datapack worktree.

For each source NBT:
  - DV lowered to 3465 (top-level, works on 1.20.0-1.20.4)
  - Palette substituted: trial_spawner -> spawner (BE cleared),
    vault -> barrel (BE LootTable set to mns:chests/<arena>/main_barrel),
    tuff_slab -> cobbled_deepslate_slab (Properties preserved)
  - Hard-coded items translated from 1.20.5+ components shape to legacy
    tag.* form: Count:byte, tag.Potion, tag.title+tag.pages (JSON-encoded),
    tag.Enchantments, etc.
  - Entity equipment compound translated to ArmorItems/HandItems arrays
    + drop_chances to ArmorDropChances/HandDropChances arrays. Attributes
    block on the entity is dropped on the legacy side (mob spawns with
    vanilla defaults pre-1.20.5).

Item-bearing pieces ALSO get a v1_20_5/<rel> mirror at DV 3837 with the
components shape preserved (palette still subbed). This matches the pattern
established by _legacy_item_translate.py for the existing 5 hard-coded-item
pieces.

Non-item pieces get only the top-level translated copy.

Idempotent. Safe to re-run.
"""
import json
import os
import shutil
import sys

import nbtlib
from nbtlib.tag import (
    Compound,
    List,
    Int,
    Byte,
    Short,
    Long,
    Float,
    Double,
    String,
    IntArray,
    LongArray,
)

SRC = r"C:\Users\finn\IdeaProjects\MoogsNetherStructures2"
DST = r"C:\Users\finn\IdeaProjects\MoogsNetherStructures2-1.20-datapack"

SRC_STRUCT = os.path.join(SRC, "src", "main", "resources", "data", "mns", "structure")
DST_STRUCT = os.path.join(DST, "src", "main", "resources", "data", "mns", "structures")

DV_LEGACY = 3465       # 1.20.1
DV_COMPONENTS = 3837   # 1.20.5

# Source subfolders (under structure/) to port.
ARENAS = [
    "small_arena",
    "large_arena",
    "dragon_arena",
    "mega_arenas/mobs",
]

# A piece is "item-bearing" if it has hard-coded ItemStacks that need
# legacy translation. Vault key_items don't count (vault becomes barrel).
ITEM_BEARING_RELS = {
    "small_arena/front.nbt",
    "dragon_arena/c2.nbt",
    "large_arena/l3.nbt",
    "large_arena/r3.nbt",
    "mega_arenas/mobs/arena_bowman.nbt",
    "mega_arenas/mobs/arena_gladiator.nbt",
    "mega_arenas/mobs/drakebone_tyrant.nbt",
    "mega_arenas/mobs/ember_sentinel.nbt",
    "mega_arenas/mobs/pit_brute.nbt",
    "mega_arenas/mobs/pit_vanguard.nbt",
}

# Palette substitution map.
PALETTE_SUBS = {
    "minecraft:tuff_slab": "minecraft:cobbled_deepslate_slab",
}

# Returns the arena name (small_arena, large_arena, dragon_arena) for a
# given relative path. Used to set barrel LootTable when subbing vaults.
def arena_of_rel(rel):
    parts = rel.replace("\\", "/").split("/")
    return parts[0]

# Set of relative paths (forward-slash) that contain vault palette entries,
# computed at runtime — we set the barrel LootTable based on which arena.

# --- Item translation: components shape -> legacy tag shape -----------
DROP_COMPONENTS_SILENTLY = {
    "minecraft:custom_name",
    "minecraft:item_name",
    "minecraft:lore",
    "minecraft:rarity",
    "minecraft:custom_data",
    "minecraft:item_model",
    "minecraft:tooltip_display",
    "minecraft:max_stack_size",
    "minecraft:enchantment_glint_override",
    "minecraft:damage",
    "minecraft:max_damage",
    "minecraft:unbreakable",
    "minecraft:repair_cost",
    "minecraft:dyed_color",
    "minecraft:attribute_modifiers",
    "minecraft:fire_resistant",
    "minecraft:tooltip_style",
}


def stack_components_to_legacy(stack):
    """Translate one ItemStack from 1.20.5+ components shape to legacy
    (1.20.0-1.20.4) tag-based shape. Returns a fresh Compound.
    """
    if not isinstance(stack, Compound) or "id" not in stack:
        # Empty / placeholder slot
        return Compound()
    out = Compound()
    out["id"] = stack["id"]
    out["Count"] = Byte(int(stack.get("count", 1)))
    components = stack.get("components")
    if not isinstance(components, Compound) or len(components) == 0:
        return out
    tag = Compound()
    for key, val in components.items():
        key = str(key)
        if key == "minecraft:potion_contents":
            potion = val.get("potion") if isinstance(val, Compound) else None
            if potion is not None:
                tag["Potion"] = potion
        elif key == "minecraft:written_book_content":
            title = val.get("title")
            if isinstance(title, Compound):
                title_str = str(title.get("raw", ""))
            else:
                title_str = str(title) if title is not None else ""
            tag["title"] = String(title_str)
            if "author" in val:
                tag["author"] = String(str(val["author"]))
            pages_in = val.get("pages", [])
            pages_out = []
            for p in pages_in:
                if isinstance(p, Compound):
                    raw = str(p.get("raw", ""))
                else:
                    raw = str(p)
                # raw may already be a JSON string literal ('"..."') —
                # unwrap that layer to get plain text. If raw is a JSON
                # object literal (e.g. '{"text":"..."}'), keep it verbatim
                # so the resulting page is that component JSON.
                page_json = None
                try:
                    parsed = json.loads(raw)
                    if isinstance(parsed, str):
                        page_json = json.dumps({"text": parsed})
                    elif isinstance(parsed, (dict, list)):
                        page_json = raw
                except Exception:
                    pass
                if page_json is None:
                    page_json = json.dumps({"text": raw})
                pages_out.append(String(page_json))
            tag["pages"] = List[String](pages_out)
            if val.get("resolved"):
                tag["resolved"] = Byte(1)
        elif key == "minecraft:enchantments":
            entries = []
            if isinstance(val, Compound):
                for eid, lvl in val.items():
                    entries.append(
                        Compound({"id": String(str(eid)), "lvl": Short(int(lvl))})
                    )
            if entries:
                tag["Enchantments"] = List[Compound](entries)
        elif key == "minecraft:stored_enchantments":
            entries = []
            if isinstance(val, Compound):
                for eid, lvl in val.items():
                    entries.append(
                        Compound({"id": String(str(eid)), "lvl": Short(int(lvl))})
                    )
            if entries:
                tag["StoredEnchantments"] = List[Compound](entries)
        elif key in DROP_COMPONENTS_SILENTLY:
            pass
        else:
            # Unknown component — log loudly but don't crash; drop it.
            print(f"  WARN: dropping unknown component {key}", file=sys.stderr)
    if len(tag) > 0:
        out["tag"] = tag
    return out


# --- Entity translation: equipment compound -> legacy arrays ----------
def entity_components_to_legacy(entity):
    """Mutate entity Compound in-place: equipment/drop_chances to legacy
    arrays; strip attributes block (defaulted on 1.20.0-1.20.4).
    """
    eq = entity.get("equipment", Compound())
    if not isinstance(eq, Compound):
        eq = Compound()
    dc = entity.get("drop_chances", Compound())
    if not isinstance(dc, Compound):
        dc = Compound()

    def slot(name):
        s = eq.get(name)
        return s if isinstance(s, Compound) else Compound()

    hand_items = [stack_components_to_legacy(slot("mainhand")),
                  stack_components_to_legacy(slot("offhand"))]
    armor_items = [stack_components_to_legacy(slot("feet")),
                   stack_components_to_legacy(slot("legs")),
                   stack_components_to_legacy(slot("chest")),
                   stack_components_to_legacy(slot("head"))]

    DEF = 0.085
    hand_dc = [Float(float(dc.get("mainhand", DEF))),
               Float(float(dc.get("offhand", DEF)))]
    armor_dc = [Float(float(dc.get("feet", DEF))),
                Float(float(dc.get("legs", DEF))),
                Float(float(dc.get("chest", DEF))),
                Float(float(dc.get("head", DEF)))]

    entity["HandItems"] = List[Compound](hand_items)
    entity["ArmorItems"] = List[Compound](armor_items)
    entity["HandDropChances"] = List[Float](hand_dc)
    entity["ArmorDropChances"] = List[Float](armor_dc)

    if "equipment" in entity:
        del entity["equipment"]
    if "drop_chances" in entity:
        del entity["drop_chances"]
    if "attributes" in entity:
        del entity["attributes"]


# --- Block entity item-array translation (dispenser/dropper/chest/...) -
def translate_be_items(nbt):
    """If a block-entity Compound has Items[], translate each ItemStack."""
    if not isinstance(nbt, Compound):
        return
    items = nbt.get("Items")
    if isinstance(items, list):
        new_items = []
        for it in items:
            if isinstance(it, Compound):
                # Lecterns/item_frames carry the slot index; preserve it.
                slot = it.get("Slot")
                t = stack_components_to_legacy(it)
                if slot is not None:
                    t["Slot"] = slot
                new_items.append(t)
        nbt["Items"] = List[Compound](new_items)
    # Lectern: Book field is a single ItemStack
    if "Book" in nbt and isinstance(nbt["Book"], Compound):
        nbt["Book"] = stack_components_to_legacy(nbt["Book"])


# --- Palette substitution ---------------------------------------------
def sub_palette(root, arena_name):
    """Mutate root in place to substitute palette entries. Returns set of
    palette indices that were vault->barrel (we'll rewrite their BE) and
    indices that were trial_spawner->spawner.
    """
    palette = root.get("palette", [])
    vault_indices = set()
    trial_indices = set()
    for i, entry in enumerate(palette):
        name = str(entry["Name"])
        if name == "minecraft:vault":
            entry["Name"] = String("minecraft:barrel")
            # drop properties (incompatible); use barrel defaults
            if "Properties" in entry:
                del entry["Properties"]
            vault_indices.add(i)
        elif name == "minecraft:trial_spawner":
            entry["Name"] = String("minecraft:spawner")
            if "Properties" in entry:
                del entry["Properties"]
            trial_indices.add(i)
        elif name in PALETTE_SUBS:
            entry["Name"] = String(PALETTE_SUBS[name])
    return vault_indices, trial_indices


def rewrite_block_entities(root, vault_indices, trial_indices, arena_name, legacy_items):
    """Walk blocks list, fix BEs whose palette index was subbed, and
    translate item-bearing BEs if legacy_items=True.
    """
    barrel_loot = f"mns:chests/{arena_name}/main_barrel"
    for b in root.get("blocks", []):
        state = int(b["state"])
        if state in vault_indices:
            # Replace BE with fresh barrel BE.
            b["nbt"] = Compound({
                "id": String("minecraft:barrel"),
                "LootTable": String(barrel_loot),
            })
            continue
        if state in trial_indices:
            b["nbt"] = Compound({
                "id": String("minecraft:spawner"),
            })
            continue
        if legacy_items and isinstance(b.get("nbt"), Compound):
            translate_be_items(b["nbt"])


def translate_entities(root, legacy_items):
    """If legacy_items=True, translate entity equipment + items."""
    for e in root.get("entities", []):
        en = e.get("nbt")
        if not isinstance(en, Compound):
            continue
        if legacy_items:
            # Item-frames: components-shape Item
            if "Item" in en and isinstance(en["Item"], Compound):
                en["Item"] = stack_components_to_legacy(en["Item"])
            # Living entities: equipment compound
            if "equipment" in en or "drop_chances" in en or "attributes" in en:
                entity_components_to_legacy(en)


def fix_palette_default_states(palette):
    """For palette entries that may not have a 'Properties' field but the
    target block requires one. For barrel and spawner, no properties are
    required (both have non-property-bearing default state)."""
    pass  # noop


def process_one(rel, src_path):
    arena = arena_of_rel(rel)
    if arena == "mega_arenas":
        arena = "mega_arenas"  # mob NBTs - LootTable in vault sub uses mega_arenas/<...> path, but mobs have no vaults
    legacy_dst = os.path.join(DST_STRUCT, rel)
    components_dst = os.path.join(DST_STRUCT, "v1_20_5", rel)

    is_item_bearing = rel.replace("\\", "/") in ITEM_BEARING_RELS

    # Ensure dest dirs.
    os.makedirs(os.path.dirname(legacy_dst), exist_ok=True)

    # --- Legacy (top-level) copy ---
    root = nbtlib.load(src_path)
    root["DataVersion"] = Int(DV_LEGACY)
    vault_idx, trial_idx = sub_palette(root, arena)
    rewrite_block_entities(root, vault_idx, trial_idx, arena, legacy_items=True)
    translate_entities(root, legacy_items=True)
    root.save(legacy_dst, gzipped=True)

    if is_item_bearing:
        os.makedirs(os.path.dirname(components_dst), exist_ok=True)
        root2 = nbtlib.load(src_path)
        root2["DataVersion"] = Int(DV_COMPONENTS)
        vault_idx2, trial_idx2 = sub_palette(root2, arena)
        rewrite_block_entities(root2, vault_idx2, trial_idx2, arena, legacy_items=False)
        translate_entities(root2, legacy_items=False)
        root2.save(components_dst, gzipped=True)
        return ("dual", legacy_dst, components_dst, sorted(vault_idx), sorted(trial_idx))
    return ("single", legacy_dst, None, sorted(vault_idx), sorted(trial_idx))


def main():
    processed = []
    skipped = []
    for arena_sub in ARENAS:
        src_dir = os.path.join(SRC_STRUCT, arena_sub.replace("/", os.sep))
        if not os.path.isdir(src_dir):
            print(f"SKIP missing source dir: {src_dir}", file=sys.stderr)
            continue
        for root_dir, dirs, files in os.walk(src_dir):
            # Skip v1_21_* / 1.21/ mirror subdirs
            dirs[:] = [d for d in dirs if not (d.startswith("v1_21_") or d == "1.21")]
            for fn in files:
                if not fn.endswith(".nbt"):
                    continue
                src_path = os.path.join(root_dir, fn)
                rel = os.path.relpath(src_path, SRC_STRUCT)
                try:
                    res = process_one(rel, src_path)
                    processed.append((rel, res))
                except Exception as e:
                    import traceback
                    traceback.print_exc()
                    skipped.append((rel, str(e)))

    print(f"\n=== Processed: {len(processed)} files ===")
    dual_count = sum(1 for _, r in processed if r[0] == "dual")
    single_count = sum(1 for _, r in processed if r[0] == "single")
    print(f"  single-tree (no items): {single_count}")
    print(f"  dual-tree (item-bearing): {dual_count}")
    if skipped:
        print(f"\n=== Skipped: {len(skipped)} files ===")
        for rel, err in skipped:
            print(f"  {rel}: {err}")

    # Summary of vault/trial subs per file
    print("\n=== Substitution summary ===")
    for rel, (kind, l, c, vi, ti) in processed:
        if vi or ti:
            print(f"  {rel}: vault->barrel x{len(vi)}, trial->spawner x{len(ti)}")


if __name__ == "__main__":
    main()
