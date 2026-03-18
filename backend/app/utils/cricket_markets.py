from difflib import get_close_matches

# Canonical team name → all known aliases
TEAM_ALIASES: dict[str, list[str]] = {
    # International
    "india": ["india", "ind", "team india", "india men", "bcci"],
    "australia": ["australia", "aus", "team australia", "australia men"],
    "england": ["england", "eng", "team england", "england men"],
    "south_africa": ["south africa", "sa", "rsa", "proteas"],
    "new_zealand": ["new zealand", "nz", "nzl", "black caps", "blackcaps"],
    "pakistan": ["pakistan", "pak", "team pakistan"],
    "sri_lanka": ["sri lanka", "sl", "slk", "sri lanka men"],
    "bangladesh": ["bangladesh", "ban", "bdesh", "tigers"],
    "west_indies": ["west indies", "wi", "windies"],
    "afghanistan": ["afghanistan", "afg"],
    "zimbabwe": ["zimbabwe", "zim"],
    "ireland": ["ireland", "ire"],
    "netherlands": ["netherlands", "ned", "holland"],
    "scotland": ["scotland", "sco"],
    # IPL
    "mumbai_indians": ["mumbai indians", "mi", "mumbai"],
    "chennai_super_kings": ["chennai super kings", "csk", "chennai"],
    "royal_challengers": ["royal challengers bengaluru", "royal challengers bangalore", "rcb", "bengaluru"],
    "kolkata_knight_riders": ["kolkata knight riders", "kkr", "kolkata"],
    "sunrisers_hyderabad": ["sunrisers hyderabad", "srh", "hyderabad", "sunrisers"],
    "rajasthan_royals": ["rajasthan royals", "rr", "rajasthan"],
    "delhi_capitals": ["delhi capitals", "dc", "delhi"],
    "punjab_kings": ["punjab kings", "pbks", "punjab", "kings xi punjab", "kxip"],
    "gujarat_titans": ["gujarat titans", "gt", "gujarat"],
    "lucknow_super_giants": ["lucknow super giants", "lsg", "lucknow"],
}

# Flat lookup: alias → canonical
_ALIAS_TO_CANONICAL: dict[str, str] = {}
for canonical, aliases in TEAM_ALIASES.items():
    for alias in aliases:
        _ALIAS_TO_CANONICAL[alias.lower()] = canonical


def normalize_team_name(raw_name: str) -> str:
    cleaned = raw_name.strip().lower()

    # Direct match
    if cleaned in _ALIAS_TO_CANONICAL:
        return _ALIAS_TO_CANONICAL[cleaned]

    # Fuzzy fallback
    all_aliases = list(_ALIAS_TO_CANONICAL.keys())
    matches = get_close_matches(cleaned, all_aliases, n=1, cutoff=0.7)
    if matches:
        return _ALIAS_TO_CANONICAL[matches[0]]

    return cleaned  # return as-is if no match


# Market display names
MARKET_DISPLAY_NAMES = {
    "match_winner": "Match Winner",
    "toss_winner": "Toss Winner",
    "top_batsman": "Top Batsman",
    "top_bowler": "Top Bowler",
    "total_runs": "Total Runs (Over/Under)",
    "team_runs": "Team Runs",
    "total_sixes": "Total Sixes",
    "total_fours": "Total Fours",
    "innings_runs": "Innings Runs",
    "session_runs": "Session Runs",
    "powerplay_runs": "Powerplay Runs",
    "player_runs": "Player Runs",
    "player_wickets": "Player Wickets",
    "over_under": "Over/Under",
}
