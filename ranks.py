from __future__ import annotations

GAME_CHOICES = ["League of Legends", "Valorant", "Counter-Strike 2", "Overwatch 2"]

GAMES: dict[str, dict] = {
    "League of Legends": {
        "tiers": [
            "Iron", "Bronze", "Silver", "Gold", "Platinum",
            "Emerald", "Diamond", "Master", "Grandmaster", "Challenger",
        ],
        "colors": {
            "Iron": 0x8e8e8e, "Bronze": 0xcd7f32, "Silver": 0xc0c0c0,
            "Gold": 0xffd700, "Platinum": 0x00e5cc, "Emerald": 0x50c878,
            "Diamond": 0x0070dd, "Master": 0x9d50bb,
            "Grandmaster": 0xff4444, "Challenger": 0x00e5ff,
        },
        "emojis": {
            "Iron":        "<:iron:1512545611860279397>",
            "Bronze":      "<:bronze:1512549713046409216>",
            "Silver":      "<:silver:1512545617937957035>",
            "Gold":        "<:gold:1512545629233221834>",
            "Platinum":    "<:platinum:1512546662659133522>",
            "Emerald":     "<:emerald:1512545659071238274>",
            "Diamond":     "<:dia:1512545647545421885>",
            "Master":      "<:master:1512545605606572214>",
            "Grandmaster": "<:grandmaster:1512545582072467647>",
            "Challenger":  "<:challenger:1512545597276688435>",
        },
    },
    "Valorant": {
        "tiers": [
            "Iron", "Bronze", "Silver", "Gold", "Platinum",
            "Diamond", "Ascendant", "Immortal", "Radiant",
        ],
        "colors": {
            "Iron": 0x777777, "Bronze": 0xcd7f32, "Silver": 0xc0c0c0,
            "Gold": 0xffd700, "Platinum": 0x00e5cc, "Diamond": 0x0099ff,
            "Ascendant": 0x00c851, "Immortal": 0xff3860, "Radiant": 0xffe97a,
        },
        "emojis": {
            "Iron": "⬛", "Bronze": "\U0001f7eb", "Silver": "⬜",
            "Gold": "\U0001f7e8", "Platinum": "\U0001fa75", "Diamond": "\U0001f537",
            "Ascendant": "\U0001f7e2", "Immortal": "\U0001f534", "Radiant": "⭐",
        },
    },
    "Counter-Strike 2": {
        "flat": True,
        "ranks": [
            "Level 1", "Level 2", "Level 3", "Level 4", "Level 5",
            "Level 6", "Level 7", "Level 8", "Level 9", "Level 10",
        ],
        "btn_labels": [
            "Lvl 1", "Lvl 2", "Lvl 3", "Lvl 4", "Lvl 5",
            "Lvl 6", "Lvl 7", "Lvl 8", "Lvl 9", "Lvl 10",
        ],
        "colors": {
            "Level 1":  0x9e9e9e, "Level 2":  0x9e9e9e, "Level 3":  0x9e9e9e,
            "Level 4":  0xf5a623, "Level 5":  0xf5a623, "Level 6":  0xf5a623,
            "Level 7":  0xff6b00, "Level 8":  0xff6b00,
            "Level 9":  0xff3c00, "Level 10": 0xff3c00,
        },
        "emojis": {
            "Level 1":  "<:lvl1:1512547369789554840>",
            "Level 2":  "<:lvl2:1512547364047687953>",
            "Level 3":  "<:lvl3:1512547375657386084>",
            "Level 4":  "<:lvl4:1512547330476216407>",
            "Level 5":  "<:lvl5:1512547287513960629>",
            "Level 6":  "<:lvl6:1512547314533929084>",
            "Level 7":  "<:lvl7:1512547337283829870>",
            "Level 8":  "<:lvl8:1512547352538517514>",
            "Level 9":  "<:lvl9:1512547345961717993>",
            "Level 10": "<:lvl10:1512547299396554784>",
        },
    },
    "Overwatch 2": {
        "tiers": ["Bronze", "Silver", "Gold", "Platinum", "Diamond", "Master", "Grandmaster", "Champion"],
        "colors": {
            "Bronze": 0xcd7f32, "Silver": 0xc0c0c0, "Gold": 0xffd700,
            "Platinum": 0x00e5cc, "Diamond": 0x0070dd, "Master": 0x9d50bb,
            "Grandmaster": 0xff8c00, "Champion": 0xffe97a,
        },
        "emojis": {
            "Bronze": "\U0001f7eb", "Silver": "⬜", "Gold": "\U0001f7e8",
            "Platinum": "\U0001fa75", "Diamond": "\U0001f537", "Master": "\U0001f7e3",
            "Grandmaster": "\U0001f7e0", "Champion": "\U0001f3c6",
        },
    },
}


def get_tiers(game: str) -> list[str]:
    config = GAMES.get(game, {})
    return config.get("ranks", []) if config.get("flat") else config.get("tiers", [])


def get_btn_labels(game: str) -> list[str]:
    config = GAMES.get(game, {})
    if config.get("flat"):
        return config.get("btn_labels", config.get("ranks", []))
    return config.get("tiers", [])


def tier_needs_division(game: str, tier: str) -> bool:
    return False


def get_divisions(game: str) -> list[str]:
    return []


def get_color(game: str, tier: str) -> int:
    return GAMES.get(game, {}).get("colors", {}).get(tier, 0x7289da)


def get_emoji(game: str, tier: str) -> str:
    return GAMES.get(game, {}).get("emojis", {}).get(tier, "\U0001f3ae")


def format_rank(game: str, tier: str, division: str = "") -> str:
    if GAMES.get(game, {}).get("flat"):
        return tier
    return f"{tier} {division}" if division else tier


def score_guess(
    game: str,
    actual_tier: str, actual_div: str,
    guessed_tier: str, guessed_div: str,
) -> tuple[bool, bool, int]:
    """Returns (is_correct, exact_match, points). No divisions — tier match = 3pts."""
    correct = actual_tier.lower() == guessed_tier.lower()
    return correct, correct, 3 if correct else 0
