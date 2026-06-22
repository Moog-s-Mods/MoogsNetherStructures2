"""Post a unified Discord release announcement (banner + changelog + download cards)."""
import json
import os
import urllib.request


def read_props(path):
    props = {}
    with open(path) as f:
        for line in f:
            line = line.strip()
            if "=" in line and not line.startswith("#"):
                k, v = line.split("=", 1)
                props[k.strip()] = v.strip()
    return props


def main():
    is_alpha = os.environ.get("IS_ALPHA", "false").strip() == "true"
    webhook_key = "DISCORD_ALPHA_WEBHOOK_URL" if is_alpha else "DISCORD_WEBHOOK"
    webhook = os.environ.get(webhook_key, "")
    if not webhook:
        print(f"{webhook_key} not set, skipping Discord announcement.")
        return

    props = read_props("gradle.properties")
    version     = props.get("modVersion", "")
    mod_name    = props.get("modName", "")
    mc_version  = props.get("minecraftVersion", "")
    mc_start    = props.get("publishMcStart", "")
    mc_end      = props.get("publishMcEnd", "")
    extra       = props.get("publishExtraMcVersions", "")
    prefix      = props.get("publishDisplayPrefix", "MNS")
    suffix      = props.get("publishDisplaySuffix", "[UNIVERSAL]")
    role_id     = props.get("discordRoleId", "")
    discord_ping = props.get("discordPing", "false").strip() == "true"
    banner_url  = props.get("discordBannerUrl", "")
    avatar_url  = props.get("discordAvatarUrl", "")
    thumbnail   = props.get("discordThumbnailUrl", "")
    color_hex   = props.get("discordEmbedColor", "#c20045").lstrip("#")
    color       = int(color_hex, 16)
    cf_slug     = props.get("curseforgeProjectSlug", "mns-moogs-nether-structures")
    mr_slug     = "mns-moogs-nether-structures"

    versions_str = f"{mc_start} - {mc_end}"
    if extra:
        versions_str += f", {extra}"

    changelog = os.environ.get("CHANGELOG_BODY", "").strip()

    if is_alpha:
        header = f"\U0001f9ea **{mod_name} {version}** alpha build is up for testing!"
    else:
        header = f"\U0001f389 **{mod_name} {version}** has been released!"

    description = (
        f"## {header}\n\n"
        f"**{prefix} {version}-{mc_version}.x {suffix}**\n"
        f"Versions - {versions_str}\n\n"
        f"### \U0001f4dd **Changelog:**\n{changelog}\n\n"
        f"<:curseforge:1132291568305459250> [CurseForge](https://www.curseforge.com/minecraft/mc-mods/{cf_slug}/files) "
        f"| <:modrinth:1132291566019563550> [Modrinth](https://modrinth.com/mod/{mr_slug}/versions)"
    )

    payload = {
        "username": "Moog's Mods",
        "avatar_url": avatar_url,
        "embeds": [
            {"image": {"url": banner_url}, "color": color},
            {"description": description, "color": color, "thumbnail": {"url": thumbnail}},
            {
                "description": f"<:curseforge:1132291568305459250> [Download from CurseForge](https://www.curseforge.com/minecraft/mc-mods/{cf_slug}/files)",
                "color": 0xE87C2E,
            },
            {
                "description": f"<:modrinth:1132291566019563550> [Download from Modrinth](https://modrinth.com/mod/{mr_slug}/versions)",
                "color": 0x1BD96A,
            },
        ],
    }

    # Alpha never pings; stable pings only if discordPing=true
    if not is_alpha and discord_ping and role_id:
        payload["content"] = f"<@&{role_id}>"
        payload["allowed_mentions"] = {"parse": [], "roles": [role_id]}

    data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    req = urllib.request.Request(
        webhook,
        data=data,
        headers={"Content-Type": "application/json; charset=utf-8"},
        method="POST",
    )
    with urllib.request.urlopen(req) as resp:
        print(f"Discord announcement posted: HTTP {resp.status}")


if __name__ == "__main__":
    main()
