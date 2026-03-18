from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


# --- Bookmaker ---
class BookmakerResponse(BaseModel):
    id: UUID
    name: str
    display_name: str
    bookmaker_type: str
    is_active: bool
    commission_pct: float
    last_scraped_at: datetime | None = None

    model_config = {"from_attributes": True}


# --- Match ---
class MatchResponse(BaseModel):
    id: UUID
    tournament: str | None = None
    format: str | None = None
    team_a: str
    team_b: str
    match_status: str
    start_time: datetime | None = None
    venue: str | None = None
    current_score_a: str | None = None
    current_score_b: str | None = None
    current_innings: int | None = None
    current_over: float | None = None
    created_at: datetime

    model_config = {"from_attributes": True}


class MatchListParams(BaseModel):
    status: str | None = None  # upcoming, live, completed
    format: str | None = None  # T20, ODI, TEST


# --- Odds ---
class OddsResponse(BaseModel):
    id: UUID
    match_id: UUID
    bookmaker_id: UUID
    bookmaker_name: str | None = None
    market_type: str
    selection: str
    odds_decimal: float
    odds_original: str | None = None
    is_back: bool
    lay_odds: float | None = None
    available_volume: float | None = None
    scraped_at: datetime
    is_live: bool

    model_config = {"from_attributes": True}


class OddsComparisonItem(BaseModel):
    selection: str
    bookmaker_odds: dict[str, float]  # {"bet365": 2.10, "betfair": 2.05}
    best_bookmaker: str
    best_odds: float


# --- Arbitrage ---
class ArbLeg(BaseModel):
    bookmaker: str
    selection: str
    odds: float
    side: str  # "back" or "lay"
    stake: float


class ArbResponse(BaseModel):
    id: UUID
    match_id: UUID
    match_name: str | None = None
    arb_type: str
    market_type: str
    profit_pct: float
    total_stake: float | None = None
    status: str
    legs: list[ArbLeg]
    detected_at: datetime
    expired_at: datetime | None = None

    model_config = {"from_attributes": True}


class ArbListParams(BaseModel):
    status: str | None = None
    arb_type: str | None = None
    min_profit: float | None = None


# --- Position ---
class PositionCreate(BaseModel):
    match_id: UUID
    market_type: str
    initial_bet_bookmaker: str
    initial_bet_selection: str
    initial_bet_odds: float
    initial_bet_stake: float
    notes: str | None = None


class PositionHedge(BaseModel):
    hedge_bet_bookmaker: str
    hedge_bet_selection: str
    hedge_bet_odds: float
    hedge_bet_stake: float


class PositionResponse(BaseModel):
    id: UUID
    match_id: UUID
    market_type: str
    position_status: str
    initial_bet_bookmaker: str | None = None
    initial_bet_selection: str | None = None
    initial_bet_odds: float | None = None
    initial_bet_stake: float | None = None
    hedge_bet_bookmaker: str | None = None
    hedge_bet_selection: str | None = None
    hedge_bet_odds: float | None = None
    hedge_bet_stake: float | None = None
    guaranteed_profit: float | None = None
    notes: str | None = None
    created_at: datetime

    model_config = {"from_attributes": True}


# --- User Arb Settings ---
class ArbSettingsUpdate(BaseModel):
    min_profit_pct: float | None = None
    max_stake: float | None = None
    monitored_bookmakers: list[str] | None = None
    monitored_markets: list[str] | None = None
    monitored_formats: list[str] | None = None
    telegram_alerts: bool | None = None
    web_push_alerts: bool | None = None
    sound_alerts: bool | None = None


class ArbSettingsResponse(BaseModel):
    min_profit_pct: float
    max_stake: float
    monitored_bookmakers: list[str]
    monitored_markets: list[str]
    monitored_formats: list[str]
    telegram_alerts: bool
    web_push_alerts: bool
    sound_alerts: bool

    model_config = {"from_attributes": True}


# --- Capture (from extension / manual entry) ---
class CapturedOddsItem(BaseModel):
    selection: str
    odds_decimal: float
    odds_original: str | None = None
    odds_format: str = "decimal"
    is_back: bool = True
    is_live: bool = False


class CaptureRequest(BaseModel):
    match_team_a: str
    match_team_b: str
    bookmaker: str
    market_type: str = "match_winner"
    source_url: str | None = None
    odds: list[CapturedOddsItem]


class CaptureResponse(BaseModel):
    message: str
    odds_received: int
    arbs_found: int = 0


# --- Live Hedge Monitor ---
class HedgeMonitorCreate(BaseModel):
    """Record your pre-match bet to start monitoring for hedge opportunities."""
    match_team_a: str
    match_team_b: str
    tournament: str | None = None
    bookmaker: str
    selection: str  # Which team you bet on
    odds: float  # Odds you got
    stake: float  # How much you bet
    market_type: str = "match_winner"


class HedgeOpportunity(BaseModel):
    """A hedge opportunity detected from live odds."""
    opposite_selection: str
    opposite_bookmaker: str
    live_odds: float
    hedge_stake: float  # How much to bet on opposite
    guaranteed_profit: float
    profit_pct: float
    breakeven_odds: float  # Min odds needed for profit
    source: str = "live"  # "demo", "api", "manual"


class HedgeMonitorResponse(BaseModel):
    id: str
    match_team_a: str
    match_team_b: str
    tournament: str | None = None
    bookmaker: str
    selection: str
    odds: float
    stake: float
    potential_return: float
    market_type: str
    status: str  # "monitoring", "hedge_available", "hedged", "expired"
    breakeven_odds: float  # Min opposite odds for profit
    best_hedge: HedgeOpportunity | None = None
    created_at: datetime


# --- WebSocket messages ---
class WsArbMessage(BaseModel):
    type: str = "arb_detected"
    data: ArbResponse


class WsHedgeMessage(BaseModel):
    type: str = "hedge_available"
    monitor_id: str
    data: HedgeOpportunity
