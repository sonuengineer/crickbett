import uuid
from datetime import datetime, timezone

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import UUID, JSON
from sqlalchemy.orm import relationship

from app.core.database import Base


def utcnow():
    return datetime.now(timezone.utc)


class Bookmaker(Base):
    __tablename__ = "bookmakers"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(100), unique=True, nullable=False)  # "bet365", "betfair"
    display_name = Column(String(100), nullable=False)  # "Bet365"
    bookmaker_type = Column(String(20), nullable=False)  # "bookmaker" | "exchange"
    base_url = Column(String(500))
    is_active = Column(Boolean, default=True)
    scrape_interval_seconds = Column(Integer, default=30)
    last_scraped_at = Column(DateTime(timezone=True))
    commission_pct = Column(Numeric(5, 2), default=0.00)  # Betfair ~5%
    created_at = Column(DateTime(timezone=True), default=utcnow)

    odds_snapshots = relationship("OddsSnapshot", back_populates="bookmaker")


class CricketMatch(Base):
    __tablename__ = "cricket_matches"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    external_ids = Column(JSON, default=dict)  # {"bet365": "123", "betfair": "456"}
    tournament = Column(String(200))
    format = Column(String(10))  # T20, ODI, TEST
    team_a = Column(String(200), nullable=False)
    team_b = Column(String(200), nullable=False)
    team_a_normalized = Column(String(200), index=True)
    team_b_normalized = Column(String(200), index=True)
    match_status = Column(String(20), default="upcoming", index=True)
    start_time = Column(DateTime(timezone=True))
    venue = Column(String(300))
    # Live state
    current_score_a = Column(String(50))  # "185/4 (18.2)"
    current_score_b = Column(String(50))
    current_innings = Column(Integer, default=1)
    current_over = Column(Numeric(4, 1))
    created_at = Column(DateTime(timezone=True), default=utcnow)
    updated_at = Column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)

    odds_snapshots = relationship("OddsSnapshot", back_populates="match")
    arb_opportunities = relationship("ArbitrageOpportunity", back_populates="match")
    positions = relationship("HedgePosition", back_populates="match")


class OddsSnapshot(Base):
    __tablename__ = "odds_snapshots"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    match_id = Column(
        UUID(as_uuid=True), ForeignKey("cricket_matches.id"), nullable=False, index=True
    )
    bookmaker_id = Column(
        UUID(as_uuid=True), ForeignKey("bookmakers.id"), nullable=False, index=True
    )
    market_type = Column(String(50), nullable=False)
    selection = Column(String(200), nullable=False)  # "India", "Over 160.5"
    odds_decimal = Column(Numeric(10, 4), nullable=False)
    odds_original = Column(String(50))  # original scraped value
    odds_format = Column(String(20))  # decimal, fractional, american
    is_back = Column(Boolean, default=True)  # True=back, False=lay
    lay_odds = Column(Numeric(10, 4))  # only for exchanges
    available_volume = Column(Numeric(15, 2))  # liquidity
    scraped_at = Column(DateTime(timezone=True), default=utcnow)
    is_live = Column(Boolean, default=False)

    __table_args__ = (
        Index("ix_odds_match_market_selection", "match_id", "market_type", "selection"),
        Index("ix_odds_scraped_at", "scraped_at"),
    )

    match = relationship("CricketMatch", back_populates="odds_snapshots")
    bookmaker = relationship("Bookmaker", back_populates="odds_snapshots")


class ArbitrageOpportunity(Base):
    __tablename__ = "arbitrage_opportunities"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    match_id = Column(
        UUID(as_uuid=True), ForeignKey("cricket_matches.id"), nullable=False, index=True
    )
    arb_type = Column(String(30), nullable=False)  # cross_book, back_lay, live_swing
    market_type = Column(String(50), nullable=False)
    profit_pct = Column(Numeric(8, 4), nullable=False)
    total_stake = Column(Numeric(15, 2))
    status = Column(String(20), default="active", index=True)
    legs = Column(JSON, nullable=False)
    # Example legs:
    # [{"bookmaker": "bet365", "selection": "India", "odds": 2.10, "side": "back", "stake": 476.19}]
    detected_at = Column(DateTime(timezone=True), default=utcnow)
    expired_at = Column(DateTime(timezone=True))
    notified = Column(Boolean, default=False)
    notification_sent_at = Column(DateTime(timezone=True))

    __table_args__ = (Index("ix_arb_status_profit", "status", "profit_pct"),)

    match = relationship("CricketMatch", back_populates="arb_opportunities")


class HedgePosition(Base):
    __tablename__ = "hedge_positions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    arb_opportunity_id = Column(
        UUID(as_uuid=True), ForeignKey("arbitrage_opportunities.id"), nullable=True
    )
    match_id = Column(
        UUID(as_uuid=True), ForeignKey("cricket_matches.id"), nullable=False
    )
    market_type = Column(String(50), nullable=False)
    position_status = Column(String(20), default="open")  # open, partially_hedged, closed
    # Original bet
    initial_bet_bookmaker = Column(String(100))
    initial_bet_selection = Column(String(200))
    initial_bet_odds = Column(Numeric(10, 4))
    initial_bet_stake = Column(Numeric(15, 2))
    # Hedge bet
    hedge_bet_bookmaker = Column(String(100))
    hedge_bet_selection = Column(String(200))
    hedge_bet_odds = Column(Numeric(10, 4))
    hedge_bet_stake = Column(Numeric(15, 2))
    # Result
    guaranteed_profit = Column(Numeric(15, 2))
    notes = Column(Text)
    created_at = Column(DateTime(timezone=True), default=utcnow)
    updated_at = Column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)

    user = relationship("User", back_populates="positions")
    match = relationship("CricketMatch", back_populates="positions")
