import uuid
from datetime import datetime, timezone

from sqlalchemy import (
    Boolean,
    BigInteger,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    String,
)
from sqlalchemy.dialects.postgresql import UUID, JSON
from sqlalchemy.orm import relationship

from app.core.database import Base


def utcnow():
    return datetime.now(timezone.utc)


class User(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String(255), unique=True, nullable=False, index=True)
    username = Column(String(100), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    full_name = Column(String(255))
    phone = Column(String(20))
    telegram_chat_id = Column(BigInteger)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), default=utcnow)
    updated_at = Column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)

    arb_settings = relationship(
        "UserArbSettings", back_populates="user", uselist=False, cascade="all, delete-orphan"
    )
    positions = relationship("HedgePosition", back_populates="user", cascade="all, delete-orphan")


class UserArbSettings(Base):
    __tablename__ = "user_arb_settings"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False
    )
    min_profit_pct = Column(Numeric(5, 2), default=1.00)
    max_stake = Column(Numeric(15, 2), default=10000.00)
    monitored_bookmakers = Column(JSON, default=list)
    monitored_markets = Column(JSON, default=list)
    monitored_formats = Column(JSON, default=list)
    telegram_alerts = Column(Boolean, default=True)
    web_push_alerts = Column(Boolean, default=True)
    sound_alerts = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), default=utcnow)
    updated_at = Column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)

    user = relationship("User", back_populates="arb_settings")
