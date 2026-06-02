"""Translate legacy-tag ItemStacks INSIDE block-entity Items[]/Book to the
1.20.5+ data-components shape. The entity-level fields (HandItems/ArmorItems/
Attributes/etc.) stay legacy — only ItemStacks change.

Use this on `v1_20_5/<rel>` mirror NBTs that were copied verbatim from a
1.20.0-1.20.4 save: bump DV to 3837, lift items in place.
"""
import json
import os
import sys

import nbtlib
from nbtlib.tag import Compound, List, Int, Byte, Short, Long, Float, String


DV_COMPONENTS = 3837  # 1.20.5

# Pre-1.20.5 → 1.20.5+ ItemStack translation.
def _component_text_from_json_str(raw):
    """raw is a NBT String containing JSON for a chat component.
    Return a Compound representation suitable for components-shape pages/lore.
    For pages in v1_20_5 we use {"raw": <plain text>} where possible.
    """
    s = str(raw)
    try:
        parsed = json.loads(s)
    except Exception:
        return Compound({"raw": String(s)})
    if isinstance(parsed, dict) and "text" in parsed and len(parsed) <= 4:
        # simple {"text": "..."} component — collapse to raw plain text
        return Compound({"raw": String(str(parsed["text"]))})
    # complex component — keep as JSON-encoded raw string
    return Compound({"raw": String(s)})


def _enchant_list_to_map(ench_list):
    out = Compound()
    for e in ench_list:
        if not isinstance(e, Compound):
            continue
        eid = str(e.get("id", ""))
        lvl = int(e.get("lvl", 1))
        if eid:
            out[eid] = Int(lvl)
    return out


def stack_legacy_to_components(stack):
    """Mutate-free legacy → components-shape ItemStack. Returns a fresh Compound."""
    if not isinstance(stack, Compound) or "id" not in stack:
        return Compound()
    out = Compound()
    out["id"] = stack["id"]
    out["count"] = Int(int(stack.get("Count", 1)))
    # preserve Slot if present (used in Items[] arrays)
    if "Slot" in stack:
        out["Slot"] = stack["Slot"]

    tag = stack.get("tag")
    if not isinstance(tag, Compound) or len(tag) == 0:
        return out

    comps = Compound()

    # Potion (tipped_arrow / potion / splash_potion / lingering_potion)
    if "Potion" in tag:
        comps["minecraft:potion_contents"] = Compound({"potion": tag["Potion"]})

    # Written book
    if "pages" in tag:
        wbc = Compound()
        if "title" in tag:
            wbc["title"] = Compound({"raw": String(str(tag["title"]))})
        if "author" in tag:
            wbc["author"] = String(str(tag["author"]))
        pages_out = []
        pages_in = tag["pages"]
        for p in pages_in:
            pages_out.append(_component_text_from_json_str(p))
        wbc["pages"] = List[Compound](pages_out)
        if "resolved" in tag:
            wbc["resolved"] = Byte(int(tag["resolved"]))
        comps["minecraft:written_book_content"] = wbc

    # Writable book
    if "title" in tag and "pages" not in tag:
        # treat as just a title — unusual, but handle
        comps["minecraft:custom_name"] = String(str(tag["title"]))

    # Enchantments
    if "Enchantments" in tag and isinstance(tag["Enchantments"], list):
        enchs = _enchant_list_to_map(tag["Enchantments"])
        if len(enchs) > 0:
            comps["minecraft:enchantments"] = enchs
    if "StoredEnchantments" in tag and isinstance(tag["StoredEnchantments"], list):
        enchs = _enchant_list_to_map(tag["StoredEnchantments"])
        if len(enchs) > 0:
            comps["minecraft:stored_enchantments"] = enchs

    # display.Name -> custom_name (as JSON-encoded chat component string)
    display = tag.get("display")
    if isinstance(display, Compound):
        if "Name" in display:
            comps["minecraft:custom_name"] = String(str(display["Name"]))
        if "Lore" in display and isinstance(display["Lore"], list):
            lore_lines = []
            for line in display["Lore"]:
                lore_lines.append(String(str(line)))
            comps["minecraft:lore"] = List[String](lore_lines)

    # damage
    if "Damage" in tag:
        comps["minecraft:damage"] = Int(int(tag["Damage"]))

    if len(comps) > 0:
        out["components"] = comps
    return out


def lift_be(nbt):
    """Walk a block-entity Compound and translate Items[] and Book."""
    if not isinstance(nbt, Compound):
        return
    items = nbt.get("Items")
    if isinstance(items, list):
        new_items = []
        for it in items:
            if isinstance(it, Compound):
                new_items.append(stack_legacy_to_components(it))
        nbt["Items"] = List[Compound](new_items)
    if "Book" in nbt and isinstance(nbt["Book"], Compound):
        nbt["Book"] = stack_legacy_to_components(nbt["Book"])


def main(path):
    r = nbtlib.load(path)
    src_dv = int(r["DataVersion"])
    r["DataVersion"] = Int(DV_COMPONENTS)
    touched = 0
    for b in r.get("blocks", []):
        nbt = b.get("nbt")
        if isinstance(nbt, Compound):
            had_items = isinstance(nbt.get("Items"), list) and len(nbt["Items"]) > 0
            had_book = isinstance(nbt.get("Book"), Compound)
            lift_be(nbt)
            if had_items or had_book:
                touched += 1
    r.save(path, gzipped=True)
    print(f"{path}\n  DV {src_dv} -> {DV_COMPONENTS}, lifted BE items in {touched} block-entities")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("usage: _lift_items_to_components.py <path-to-nbt>")
        sys.exit(1)
    for p in sys.argv[1:]:
        main(p)
