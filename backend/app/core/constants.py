from enum import Enum


class CricketMarketType(str, Enum):
    MATCH_WINNER = "match_winner"
    TOSS_WINNER = "toss_winner"
    TOP_BATSMAN = "top_batsman"
    TOP_BOWLER = "top_bowler"
    TOTAL_RUNS = "total_runs"
    TEAM_RUNS = "team_runs"
    TOTAL_SIXES = "total_sixes"
    TOTAL_FOURS = "total_fours"
    INNINGS_RUNS = "innings_runs"
    SESSION_RUNS = "session_runs"
    POWERPLAY_RUNS = "powerplay_runs"
    PLAYER_RUNS = "player_runs"
    PLAYER_WICKETS = "player_wickets"
    OVER_UNDER = "over_under"


class ArbType(str, Enum):
    CROSS_BOOK = "cross_book"
    BACK_LAY = "back_lay"
    LIVE_SWING = "live_swing"


class MatchStatus(str, Enum):
    UPCOMING = "upcoming"
    LIVE = "live"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class MatchFormat(str, Enum):
    T20 = "T20"
    ODI = "ODI"
    TEST = "TEST"


class BookmakerType(str, Enum):
    BOOKMAKER = "bookmaker"
    EXCHANGE = "exchange"


class PositionStatus(str, Enum):
    OPEN = "open"
    PARTIALLY_HEDGED = "partially_hedged"
    CLOSED = "closed"


class ArbStatus(str, Enum):
    ACTIVE = "active"
    EXPIRED = "expired"
    EXECUTED = "executed"
    DISMISSED = "dismissed"


# Markets prioritized for arb detection (most liquid)
ARB_PRIORITY_MARKETS = [
    CricketMarketType.MATCH_WINNER,
    CricketMarketType.TOTAL_RUNS,
    CricketMarketType.TEAM_RUNS,
    CricketMarketType.SESSION_RUNS,
    CricketMarketType.TOP_BATSMAN,
]
