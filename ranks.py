from __future__ import annotations

GAME_CHOICES = ["League of Legends", "Valorant", "Counter-Strike 2", "Overwatch 2"]

GAMES: dict[str, dict] = {
    "League of Legends": {
        "tiers": [
            "Iron", "Bronze", "Silver", "Gold", "Platinum",
            "Emerald", "Diamond", "Master", "Grandmaster", "Challenger",
        ],
        "divisions": ["IV", "III", "II", "I"],
        "no_division": {"Master", "Grandmaster", "Challenger"},
        "colors": {
            "Iron": 0x8e8e8e, "Bronze": 0xcd7f32, "Silver": 0xc0c0c0,
            "Gold": 0xffd700, "Platinum": 0x00e5cc, "Emerald": 0x50c878,
            "Diamond": 0x0070dd, "Master": 0x9d50bb,
            "Grandmaster": 0xff4444, "Challenger": 0x00e5ff,
        },
        "emojis": {
            "Iron": "⬛", "Bronze": "\U0001f7eb", "Silver": "⬜",
            "Gold": "\U0001f7e8", "Platinum": "\U0001fa75", "Emerald": "\U0001f7e9",
            "Diamond": "\U0001f537", "Master": "\U0001f7e3",
            "Grandmaster": "\U0001f534", "Challenger": "\U0001f3c6",
        },
    },
    "Valorant": {
        "tiers": [
            "Iron", "Bronze", "Silver", "Gold", "Platinum",
            "Diamond", "Ascendant", "Immortal", "Radiant",
        ],
        "divisions": ["1", "2", "3"],
        "no_division": {"Radiant"},
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
            "Silver I", "Silver II", "Silver III", "Silver IV",
            "Silver Elite", "Silver Elite Master",
            "Gold Nova I", "Gold Nova II", "Gold Nova III", "Gold Nova Master",
            "Master Guardian I", "Master Guardian II", "Master Guardian Elite",
            "Distinguished Master Guardian",
            "Legendary Eagle", "Legendary Eagle Master",
            "Supreme Master First Class", "Global Elite",
        ],
        "btn_labels": [
            "S I", "S II", "S III", "S IV", "SE", "SEM",
            "GN I", "GN II", "GN III", "GNM",
            "MG I", "MG II", "MGE", "DMG",
            "LE", "LEM", "SMFC", "GE",
        ],
        "colors": {
            "Silver I": 0x9e9e9e, "Silver II": 0x9e9e9e, "Silver III": 0x9e9e9e,
            "Silver IV": 0x9e9e9e, "Silver Elite": 0x9e9e9e, "Silver Elite Master": 0x9e9e9e,
            "Gold Nova I": 0xffd700, "Gold Nova II": 0xffd700,
            "Gold Nova III": 0xffd700, "Gold Nova Master": 0xffd700,
            "Master Guardian I": 0x00e5cc, "Master Guardian II": 0x00e5cc,
            "Master Guardian Elite": 0x4fc3f7, "Distinguished Master Guardian": 0x0070dd,
            "Legendary Eagle": 0x9d50bb, "Legendary Eagle Master": 0x9d50bb,
            "Supreme Master First Class": 0xff4444, "Global Elite": 0xffe97a,
        },
        "emojis": {
            "Silver I": "⬜", "Silver II": "⬜", "Silver III": "⬜",
            "Silver IV": "⬜", "Silver Elite": "⬜", "Silver Elite Master": "⬜",
            "Gold Nova I": "\U0001f7e8", "Gold Nova II": "\U0001f7e8",
            "Gold Nova III": "\U0001f7e8", "Gold Nova Master": "\U0001f7e8",
            "Master Guardian I": "\U0001fa75", "Master Guardian II": "\U0001fa75",
            "Master Guardian Elite": "\U0001fa75", "Distinguished Master Guardian": "\U0001f537",
            "Legendary Eagle": "\U0001f985", "Legendary Eagle Master": "\U0001f985",
            "Supreme Master First Class": "\U0001f534", "Global Elite": "⭐",
        },
    },
    "Overwatch 2": {
        "tiers": ["Bronze", "Silver", "Gold", "Platinum", "Diamond", "Master", "Grandmaster", "Champion"],
        "divisions": ["5", "4", "3", "2", "1"],
        "no_division": {"Champion"},
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
    config = GAMES.get(game, {})
    return not config.get("flat") and tier not in config.get("no_division", set())


def get_divisions(game: str) -> list[str]:
    return GAMES.get(game, {}).get("divisions", [])


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
    """Returns (is_correct, exact_match, points)."""
    config = GAMES.get(game, {})
    tier_match = actual_tier.lower() == guessed_tier.lower()

    if not tier_match:
        return False, False, 0

    if config.get("flat"):
        return True, True, 3

    no_division = not actual_div or actual_tier in config.get("no_division", set())
    exact = no_division or guessed_div.lower() == actual_div.lower()
    return True, exact, 3 if exact else 1
