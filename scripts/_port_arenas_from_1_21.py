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
    "mega_fortress/mobs",
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
    "mega_fortress/mobs/black_guard.nbt",
    "mega_fortress/mobs/blaze_sentinel.nbt",
    "mega_fortress/mobs/fortress_archer.nbt",
    "mega_fortress/mobs/fortress_champion.nbt",
    "mega_fortress/mobs/fortress_guard.nbt",
    "mega_fortress/mobs/warden_of_the_keep.nbt",
}

# Attribute id translation: 1.20.5+ has dropped the `generic.` namespace
# segment; 1.20.0-1.20.4 used `minecraft:generic.<name>` (and per-mob
# namespaces like `minecraft:zombie.spawn_reinforcements`). Map each
# 1.20.5+ id back to the 1.20.4 form. Attributes not in this map are
# stripped from the legacy NBT (they don't exist on 1.20.4).
LEGACY_ATTRIBUTE_NAMES = {
    "minecraft:max_health":         "minecraft:generic.max_health",
    "minecraft:follow_range":       "minecraft:generic.follow_range",
    "minecraft:knockback_resistance":"minecraft:generic.knockback_resistance",
    "minecraft:movement_speed":     "minecraft:generic.movement_speed",
    "minecraft:flying_speed":       "minecraft:generic.flying_speed",
    "minecraft:attack_damage":      "minecraft:generic.attack_damage",
    "minecraft:attack_knockback":   "minecraft:generic.attack_knockback",
    "minecraft:attack_speed":       "minecraft:generic.attack_speed",
    "minecraft:armor":              "minecraft:generic.armor",
    "minecraft:armor_toughness":    "minecraft:generic.armor_toughness",
    "minecraft:luck":               "minecraft:generic.luck",
    "minecraft:spawn_reinforcements":"minecraft:zombie.spawn_reinforcements",
    "minecraft:jump_strength":      "minecraft:horse.jump_strength",
}

# Modifier operation enum→int (pre-1.20.5).
LEGACY_MODIFIER_OP = {
    "add_value": 0,
    "add_multiplied_base": 1,
    "add_multiplied_total": 2,
}

# Attributes that exist on 1.20.5/1.20.6 — used to filter the v1_20_5
# mirror's attributes list (drop 1.21-only ones like oxygen_bonus).
ATTRS_OK_ON_1_20_5 = set(LEGACY_ATTRIBUTE_NAMES.keys())

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
    "minecraft:item_name",
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


def _component_to_json_str(comp):
    """Recursively turn an NBT chat-component Compound into a plain Python
    dict suitable for json.dumps. NBT Bytes are converted to bool for
    fields known to be boolean (bold/italic/underlined/strikethrough/obfuscated).
    """
    BOOL_KEYS = {"bold", "italic", "underlined", "strikethrough", "obfuscated"}
    if isinstance(comp, Compound):
        out = {}
        for k, v in comp.items():
            k = str(k)
            if isinstance(v, (Compound, list)):
                out[k] = _component_to_json_str(v)
            elif isinstance(v, Byte) and k in BOOL_KEYS:
                out[k] = bool(int(v))
            elif isinstance(v, (Byte, Short, Int, Long)):
                out[k] = int(v)
            elif isinstance(v, (Float, Double)):
                out[k] = float(v)
            else:
                out[k] = str(v)
        return out
    if isinstance(comp, list):
        return [_component_to_json_str(x) for x in comp]
    return str(comp)


def component_to_json(comp):
    """Compound chat component -> JSON string for legacy CustomName / Lore."""
    return json.dumps(_component_to_json_str(comp), ensure_ascii=False)


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
    display = Compound()  # collects custom_name + lore into tag.display
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
        elif key == "minecraft:custom_name":
            # 1.20.4 stores item display name as tag.display.Name = JSON-string
            display["Name"] = String(component_to_json(val))
        elif key == "minecraft:lore":
            # 1.20.4 stores lore as tag.display.Lore = List[String] of JSON-stringified components
            lore_lines = []
            if isinstance(val, list):
                for line in val:
                    lore_lines.append(String(component_to_json(line)))
            tag["display"] = display  # set early so subsequent assignment is on the same compound
            display["Lore"] = List[String](lore_lines)
        elif key == "minecraft:damage":
            # damage int -> tag.Damage Int
            try:
                tag["Damage"] = Int(int(val))
            except Exception:
                pass
        elif key in DROP_COMPONENTS_SILENTLY:
            pass
        else:
            # Unknown component — log loudly but don't crash; drop it.
            print(f"  WARN: dropping unknown component {key}", file=sys.stderr)
    if len(display) > 0:
        tag["display"] = display
    if len(tag) > 0:
        out["tag"] = tag
    return out


# --- Entity translation: equipment compound -> legacy arrays ----------
def _uuid_int_array_from(name):
    """Deterministic UUID (IntArray[4]) from a name string. md5-derived."""
    import hashlib
    h = hashlib.md5(name.encode("utf-8")).digest()  # 16 bytes
    ints = []
    for i in range(4):
        b = h[i*4:(i+1)*4]
        v = int.from_bytes(b, "big", signed=True)
        ints.append(Int(v))
    return IntArray(ints)


def _translate_attributes_to_legacy(attrs):
    """`attributes` (1.20.5+ list of {id, base, modifiers}) -> legacy
    `Attributes` list of {Name, Base, Modifiers:[{Name, Amount, Operation:Int, UUID:IntArray}]}.
    Unknown / 1.21-only attribute ids are dropped.
    """
    out = []
    for a in attrs:
        if not isinstance(a, Compound):
            continue
        new_id = LEGACY_ATTRIBUTE_NAMES.get(str(a.get("id", "")))
        if new_id is None:
            continue  # attribute not on 1.20.4
        entry = Compound()
        entry["Name"] = String(new_id)
        if "base" in a:
            try:
                entry["Base"] = Double(float(a["base"]))
            except Exception:
                pass
        mods_in = a.get("modifiers")
        if isinstance(mods_in, list):
            mods_out = []
            for m in mods_in:
                if not isinstance(m, Compound):
                    continue
                op_str = str(m.get("operation", "add_value"))
                op_int = LEGACY_MODIFIER_OP.get(op_str, 0)
                mid = str(m.get("id", "minecraft:unknown"))
                try:
                    amount = float(m.get("amount", 0.0))
                except Exception:
                    amount = 0.0
                mods_out.append(Compound({
                    "Name": String(mid),
                    "Amount": Double(amount),
                    "Operation": Int(op_int),
                    "UUID": _uuid_int_array_from(mid),
                }))
            if mods_out:
                entry["Modifiers"] = List[Compound](mods_out)
        out.append(entry)
    return out


def entity_components_to_legacy(entity):
    """Mutate entity Compound in-place to 1.20.0-1.20.4 shape:
    - equipment / drop_chances -> ArmorItems/HandItems + drop chances arrays
    - attributes (lowercase) -> Attributes (capital A) with `minecraft:generic.*`
      prefix mapping; modifiers translated with deterministic UUIDs
    - CustomName Compound -> JSON-string
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

    # Attributes translation
    if "attributes" in entity and isinstance(entity["attributes"], list):
        legacy_attrs = _translate_attributes_to_legacy(entity["attributes"])
        if legacy_attrs:
            entity["Attributes"] = List[Compound](legacy_attrs)
        del entity["attributes"]

    # CustomName: Compound -> JSON-encoded String (1.20.x chat-component format)
    if "CustomName" in entity and isinstance(entity["CustomName"], Compound):
        entity["CustomName"] = String(component_to_json(entity["CustomName"]))

    if "equipment" in entity:
        del entity["equipment"]
    if "drop_chances" in entity:
        del entity["drop_chances"]


def filter_v1_20_5_entity(entity):
    """For the v1_20_5/ mirror: strip 1.21-only attributes (oxygen_bonus etc.)
    from the components-shape `attributes` list. Other fields kept as-is.
    """
    if "attributes" in entity and isinstance(entity["attributes"], list):
        kept = [a for a in entity["attributes"]
                if isinstance(a, Compound) and str(a.get("id", "")) in ATTRS_OK_ON_1_20_5]
        entity["attributes"] = List[Compound](kept)


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
    """If legacy_items=True, translate entity equipment + items + attributes
    + CustomName to 1.20.0-1.20.4 shape. Otherwise (v1_20_5 mirror) just
    strip 1.21-only attributes so the components-shape NBT loads cleanly.
    """
    for e in root.get("entities", []):
        en = e.get("nbt")
        if not isinstance(en, Compound):
            continue
        if legacy_items:
            # Item-frames: components-shape Item
            if "Item" in en and isinstance(en["Item"], Compound):
                en["Item"] = stack_components_to_legacy(en["Item"])
            # Living entities: equipment + attributes + CustomName
            if ("equipment" in en or "drop_chances" in en or
                "attributes" in en or
                (isinstance(en.get("CustomName"), Compound))):
                entity_components_to_legacy(en)
        else:
            filter_v1_20_5_entity(en)


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
