from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, Float, Integer, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class EventRecord(Base):
    __tablename__ = "live_events"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    event_id: Mapped[str] = mapped_column(String(128), index=True, default="")
    event_type: Mapped[str] = mapped_column(String(64), index=True)
    priority: Mapped[str] = mapped_column(String(8), index=True, default="C")
    actor_id: Mapped[str] = mapped_column(String(128), default="")
    actor_name: Mapped[str] = mapped_column(String(255), default="")
    room_id: Mapped[str] = mapped_column(String(128), index=True, default="")
    content: Mapped[str] = mapped_column(Text, default="")
    live_heat: Mapped[float] = mapped_column(Float, default=0.0)
    normalized_payload: Mapped[dict] = mapped_column(JSON, default=dict)
    raw_payload: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, index=True)


class CommandRecord(Base):
    __tablename__ = "brain_commands"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    cmd_id: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    command_type: Mapped[str] = mapped_column(String(64), index=True)
    priority_track: Mapped[str] = mapped_column(String(16), index=True)
    status: Mapped[str] = mapped_column(String(32), index=True, default="queued")
    interrupt: Mapped[int] = mapped_column(Integer, default=0)
    target_device: Mapped[str] = mapped_column(String(255), default="")
    payload: Mapped[dict] = mapped_column(JSON, default=dict)
    error_message: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, index=True)
    dispatched_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)


class SettingsRecord(Base):
    __tablename__ = "system_settings"

    key: Mapped[str] = mapped_column(String(128), primary_key=True)
    payload: Mapped[dict] = mapped_column(JSON, default=dict)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
