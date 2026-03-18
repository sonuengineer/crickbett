from datetime import datetime, timedelta, timezone

from app.utils.cricket_markets import normalize_team_name


def match_same_event(
    team_a_1: str,
    team_b_1: str,
    team_a_2: str,
    team_b_2: str,
    start_time_1: datetime | None = None,
    start_time_2: datetime | None = None,
    time_tolerance_minutes: int = 120,
) -> bool:
    """
    Determine if two match listings from different bookmakers refer to the same event.

    Normalizes team names and optionally checks start times are close.
    """
    norm_a1 = normalize_team_name(team_a_1)
    norm_b1 = normalize_team_name(team_b_1)
    norm_a2 = normalize_team_name(team_a_2)
    norm_b2 = normalize_team_name(team_b_2)

    teams_1 = {norm_a1, norm_b1}
    teams_2 = {norm_a2, norm_b2}

    if teams_1 != teams_2:
        return False

    # If start times provided, check they're close
    if start_time_1 and start_time_2:
        diff = abs((start_time_1 - start_time_2).total_seconds())
        if diff > time_tolerance_minutes * 60:
            return False

    return True


def normalize_selection(selection: str, team_a: str, team_b: str) -> str:
    """
    Normalize a selection string to use canonical team names.

    E.g., "MI" in a Mumbai Indians vs CSK match → "mumbai_indians"
    """
    norm = normalize_team_name(selection)
    norm_a = normalize_team_name(team_a)
    norm_b = normalize_team_name(team_b)

    if norm == norm_a or norm == norm_b:
        return norm

    # Check if it's an over/under or numeric selection
    sel_lower = selection.strip().lower()
    if sel_lower.startswith("over") or sel_lower.startswith("under"):
        return sel_lower
    if sel_lower in ("draw", "tie", "no result"):
        return sel_lower

    return norm


def is_odds_stale(scraped_at: datetime, max_age_seconds: int = 120) -> bool:
    """Check if odds are too old to be reliable."""
    age = (datetime.now(timezone.utc) - scraped_at).total_seconds()
    return age > max_age_seconds
