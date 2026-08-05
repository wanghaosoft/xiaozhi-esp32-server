from __future__ import annotations

import threading
import time
import uuid
from collections import deque
from dataclasses import dataclass, field
from datetime import datetime

from app.database import SessionLocal
from app.schemas import (
    BrainSettings,
    CommandEnvelope,
    CommandView,
    DashboardSnapshot,
    EventType,
    EventView,
    LiveEventIn,
    LiveStage,
    PriorityLevel,
    QueueTrack,
    RobotState,
    RoomMetrics,
)
from app.services.dispatcher import XiaozhiDispatcher
from app.services.preprocessor import EventPreprocessor
from app.services.reporter import XiaozhiReporter
from app.services.settings_service import SettingsService


@dataclass
class LocalCommandRecord:
    id: int
    cmd_id: str
    command_type: str
    priority_track: str
    status: str
    target_device: str
    payload: dict
    created_at: datetime = field(default_factory=datetime.utcnow)
    error_message: str = ""
    dispatched_at: datetime | None = None


class LiveBrainService:
    def __init__(self) -> None:
        self.settings_service = SettingsService()
        self.preprocessor = EventPreprocessor()
        self.dispatcher = XiaozhiDispatcher()
        self.reporter = XiaozhiReporter()
        self._lock = threading.RLock()
        self._stop_event = threading.Event()
        self._worker: threading.Thread | None = None
        self._emergency_queue: deque[CommandEnvelope] = deque()
        self._normal_queue: deque[CommandEnvelope] = deque()
        self._batch_queue: deque[CommandEnvelope] = deque()
        self._recent_events: deque[tuple[float, str]] = deque(maxlen=500)
        self._gift_bucket: list[dict] = []
        self._follow_bucket: list[dict] = []
        self._fansclub_bucket: list[dict] = []
        self._welcome_bucket: list[dict] = []
        self._like_counter = 0
        self._like_window_started_at = time.time()
        self._last_batch_dispatch_at = 0.0
        self._last_welcome_dispatch_at = 0.0
        self._last_output_at = time.time()
        self._last_idle_level_triggered = 0
        self._room_metrics = RoomMetrics()
        self._live_heat = 0.0
        self._robot_state = RobotState.IDLE
        self._recent_event_views: deque[EventView] = deque(maxlen=20)
        self._recent_command_ids: deque[str] = deque(maxlen=50)
        self._command_records: dict[str, LocalCommandRecord] = {}
        self._event_view_seq = 0
        self._command_view_seq = 0

    def start(self) -> None:
        if self._worker and self._worker.is_alive():
            return
        self._stop_event.clear()
        self._worker = threading.Thread(target=self._run_loop, daemon=True)
        self._worker.start()

    def stop(self) -> None:
        self._stop_event.set()
        if self._worker:
            self._worker.join(timeout=2)
            self._worker = None

    def ingest(self, event: LiveEventIn) -> EventView:
        with SessionLocal() as db:
            settings = self.settings_service.load(db)
            normalized = self.preprocessor.normalize(event, settings)
            created_at = event.created_at or datetime.utcnow()
            with self._lock:
                self._register_event(normalized.event_type.value)
                self._last_idle_level_triggered = 0
                if normalized.room_metrics is not None:
                    self._room_metrics = normalized.room_metrics
                self._live_heat = self._compute_live_heat()
                self._apply_event(normalized, settings)
                event_view = EventView(
                    id=self._next_event_view_id(),
                    event_id=normalized.event_id,
                    event_type=normalized.event_type.value,
                    priority=normalized.priority.value,
                    actor_name=normalized.actor_name,
                    content=normalized.content,
                    room_id=normalized.room_id,
                    live_heat=self._live_heat,
                    created_at=created_at,
                )
                self._recent_event_views.appendleft(event_view)

            self.reporter.report_event(settings, normalized, event_view.live_heat, event_view.created_at)
            return event_view

    def get_snapshot(self) -> DashboardSnapshot:
        with SessionLocal() as db:
            settings = self.settings_service.load(db)
            recent_events = self.list_events(20, settings)
            recent_commands = self.list_commands(20, settings)
            with self._lock:
                queue_sizes = {
                    "emergency": len(self._emergency_queue),
                    "normal": len(self._normal_queue),
                    "batch": len(self._batch_queue),
                }
                robot_state = self._robot_state
                live_heat = self._live_heat
                room_metrics = self._room_metrics
            return DashboardSnapshot(
                live_heat=live_heat,
                heat_bucket=self._heat_bucket(live_heat),
                robot_state=robot_state,
                stage=settings.stage,
                blocked=settings.blocked,
                current_topic=settings.current_topic,
                queue_sizes=queue_sizes,
                recent_events=recent_events,
                recent_commands=recent_commands,
                room_metrics=room_metrics,
            )

    def list_events(self, limit: int = 100, settings: BrainSettings | None = None) -> list[EventView]:
        local_settings = settings
        if local_settings is None:
            with SessionLocal() as db:
                local_settings = self.settings_service.load(db)
        rows = self.reporter.fetch_events(local_settings, limit)
        if rows:
            return [self._remote_event_to_view(row) for row in rows]
        with self._lock:
            return list(self._recent_event_views)[:limit]

    def list_commands(self, limit: int = 100, settings: BrainSettings | None = None) -> list[CommandView]:
        local_settings = settings
        if local_settings is None:
            with SessionLocal() as db:
                local_settings = self.settings_service.load(db)
        rows = self.reporter.fetch_commands(local_settings, limit)
        if rows:
            return [self._remote_command_to_view(row) for row in rows]
        with self._lock:
            return [self._to_command_view(self._command_records[cmd_id]) for cmd_id in list(self._recent_command_ids)[:limit] if cmd_id in self._command_records]

    def enqueue_manual(self, text: str, command_type: str, priority: QueueTrack, interrupt: bool) -> None:
        command = CommandEnvelope(
            cmd_id=str(uuid.uuid4()),
            priority=priority,
            type=command_type,
            params={"text": text},
            interrupt=interrupt,
        )
        with SessionLocal() as db:
            settings = self.settings_service.load(db)
            self._enqueue_command(command, settings)

    def _run_loop(self) -> None:
        while not self._stop_event.wait(1.0):
            with SessionLocal() as db:
                settings = self.settings_service.load(db)
                with self._lock:
                    self._flush_buckets_if_needed(settings)
                    self._trigger_idle_if_needed(settings)
                    command = self._next_command(settings)
                if command is None:
                    continue
                self._dispatch_command(command, settings)

    def _dispatch_command(self, command: CommandEnvelope, settings: BrainSettings) -> None:
        with self._lock:
            self._robot_state = RobotState.SPEAKING_KEY if command.priority == QueueTrack.EMERGENCY else RobotState.SPEAKING_FILL
            record = self._command_records.get(command.cmd_id)
        ok, message = self.dispatcher.dispatch(command, settings)
        if record is not None:
            record.status = "sent" if ok else "failed"
            record.error_message = "" if ok else message
            record.dispatched_at = datetime.utcnow()
        self.reporter.report_command(
            settings,
            command,
            "sent" if ok else "failed",
            record.target_device if record is not None else command.params.get("user", ""),
            "" if ok else message,
            settings.room_id,
            settings.room_title,
            record.created_at if record is not None else datetime.utcnow(),
            record.dispatched_at if record is not None else datetime.utcnow(),
        )
        with self._lock:
            self._last_output_at = time.time()
            self._robot_state = RobotState.IDLE

    def _apply_event(self, event, settings: BrainSettings) -> None:
        if event.event_type == EventType.GIFT:
            if event.priority == PriorityLevel.S:
                self._queue_structured_command(
                    QueueTrack.EMERGENCY,
                    "GIFT_THANKS_S",
                    {
                        "user": event.actor_name,
                        "gift_name": event.gift_name,
                        "gift_price": event.gift_price,
                    },
                    True,
                )
                return
            self._gift_bucket.append({"user": event.actor_name, "gift_name": event.gift_name})
            return

        if event.event_type == EventType.SOCIAL:
            self._follow_bucket.append({"user": event.actor_name})
            return

        if event.event_type == EventType.FANSCLUB:
            self._fansclub_bucket.append({"user": event.actor_name})
            return

        if event.event_type == EventType.MEMBER:
            self._welcome_bucket.append({"user": event.actor_name})
            return

        if event.event_type == EventType.LIKE:
            self._like_counter += 1
            return

        if event.event_type == EventType.CHAT and event.need_reply:
            track = QueueTrack.EMERGENCY if event.priority == PriorityLevel.S else QueueTrack.NORMAL
            self._queue_structured_command(
                track,
                "REPLY_CHAT",
                {
                    "user": event.actor_name,
                    "original_text": event.content,
                    "intent_type": event.intent_type,
                    "reply_hint": event.reply_hint,
                    "merged_count": event.merged_count,
                },
                interrupt=track == QueueTrack.EMERGENCY,
            )

    def _flush_buckets_if_needed(self, settings: BrainSettings) -> None:
        now = time.time()
        if self._gift_bucket and now - self._last_batch_dispatch_at >= settings.queue.gift_bucket_seconds:
            self._queue_structured_command(
                QueueTrack.BATCH,
                "GIFT_THANKS_BATCH",
                {"users": [item["user"] for item in self._gift_bucket], "gift_type": "gift"},
                False,
            )
            self._gift_bucket.clear()
            self._last_batch_dispatch_at = now

        if self._follow_bucket and now - self._last_batch_dispatch_at >= settings.queue.follow_bucket_seconds:
            self._queue_structured_command(
                QueueTrack.BATCH,
                "FOLLOW_THANKS",
                {"users": [item["user"] for item in self._follow_bucket]},
                False,
            )
            self._follow_bucket.clear()
            self._last_batch_dispatch_at = now

        if self._fansclub_bucket and now - self._last_batch_dispatch_at >= settings.queue.follow_bucket_seconds:
            self._queue_structured_command(
                QueueTrack.BATCH,
                "FANSCLUB_THANKS",
                {"users": [item["user"] for item in self._fansclub_bucket]},
                False,
            )
            self._fansclub_bucket.clear()
            self._last_batch_dispatch_at = now

        if self._welcome_bucket and now - self._last_welcome_dispatch_at >= settings.queue.welcome_bucket_seconds:
            command_type = "WELCOME_ALL" if self._live_heat >= settings.heat.active_threshold else "WELCOME_BATCH"
            params = (
                {"count": len(self._welcome_bucket)}
                if command_type == "WELCOME_ALL"
                else {"users": [item["user"] for item in self._welcome_bucket]}
            )
            self._queue_structured_command(QueueTrack.BATCH, command_type, params, False)
            self._welcome_bucket.clear()
            self._last_welcome_dispatch_at = now

        if self._like_counter >= settings.queue.like_storm_threshold_per_window and now - self._like_window_started_at >= settings.queue.like_storm_window_seconds:
            self._queue_structured_command(QueueTrack.BATCH, "LIKE_STORM", {}, False)
            self._like_counter = 0
            self._like_window_started_at = now
        elif now - self._like_window_started_at >= settings.queue.like_storm_window_seconds:
            self._like_counter = 0
            self._like_window_started_at = now

    def _trigger_idle_if_needed(self, settings: BrainSettings) -> None:
        idle_for = time.time() - self._last_output_at
        if self._live_heat >= settings.heat.cold_threshold:
            self._last_idle_level_triggered = 0
            return
        if not settings.xiaozhi_target.base_url or not settings.xiaozhi_target.secret:
            return
        if idle_for >= settings.idle.level4_seconds:
            level = 4
        elif idle_for >= settings.idle.level3_seconds:
            level = 3
        elif idle_for >= settings.idle.level2_seconds:
            level = 2
        elif idle_for >= settings.idle.level1_seconds:
            level = 1
        else:
            return
        if level <= self._last_idle_level_triggered:
            return
        if self._batch_queue and self._batch_queue[-1].type == "ENGAGE":
            return
        self._queue_structured_command(
            QueueTrack.BATCH,
            "ENGAGE",
            {"level": level, "topic_hint": settings.current_topic},
            False,
        )
        self._last_output_at = time.time()
        self._last_idle_level_triggered = level

    def _next_command(self, settings: BrainSettings) -> CommandEnvelope | None:
        if settings.blocked:
            return None
        if self._emergency_queue:
            return self._emergency_queue.popleft()
        if self._normal_queue:
            return self._normal_queue.popleft()
        if self._batch_queue:
            return self._batch_queue.popleft()
        return None

    def _queue_structured_command(self, priority: QueueTrack, command_type: str, params: dict, interrupt: bool) -> None:
        command = CommandEnvelope(
            cmd_id=str(uuid.uuid4()),
            priority=priority,
            type=command_type,
            params=params,
            interrupt=interrupt,
        )
        with SessionLocal() as session:
            settings = self.settings_service.load(session)
            self._enqueue_command(command, settings)

    def _enqueue_command(self, command: CommandEnvelope, settings: BrainSettings) -> None:
        record = LocalCommandRecord(
            id=self._next_command_view_id(),
            cmd_id=command.cmd_id,
            command_type=command.type,
            priority_track=command.priority.value,
            status="queued",
            target_device=str(command.params.get("user") or command.params.get("count") or ""),
            payload=command.model_dump(mode="json"),
        )
        with self._lock:
            self._command_records[command.cmd_id] = record
            self._recent_command_ids.appendleft(command.cmd_id)
            if command.priority == QueueTrack.EMERGENCY:
                self._emergency_queue.append(command)
            elif command.priority == QueueTrack.NORMAL:
                self._normal_queue.append(command)
            else:
                self._batch_queue.append(command)
        self.reporter.report_command(
            settings,
            command,
            record.status,
            record.target_device,
            record.error_message,
            settings.room_id,
            settings.room_title,
            record.created_at,
            record.dispatched_at,
        )

    def _register_event(self, event_type: str) -> None:
        now = time.time()
        self._recent_events.append((now, event_type))
        while self._recent_events and now - self._recent_events[0][0] > 60:
            self._recent_events.popleft()

    def _compute_live_heat(self) -> float:
        now = time.time()
        last_minute = [event_type for ts, event_type in self._recent_events if now - ts <= 60]
        chat_density = min(last_minute.count(EventType.CHAT.value) / 20.0, 1.0)
        gift_gpm = min(last_minute.count(EventType.GIFT.value) / 10.0, 1.0)
        entry_rate = min(last_minute.count(EventType.MEMBER.value) / 30.0, 1.0)
        like_rate = min(last_minute.count(EventType.LIKE.value) / 60.0, 1.0)
        audience_trend = min((self._room_metrics.audience_count or 0) / 1000.0, 1.0)
        score = (
            chat_density * 30
            + audience_trend * 25
            + gift_gpm * 25
            + entry_rate * 10
            + like_rate * 10
        )
        return round(score, 2)

    def _heat_bucket(self, heat: float) -> str:
        if heat < 20:
            return "COLD"
        if heat < 40:
            return "CALM"
        if heat < 65:
            return "ACTIVE"
        if heat < 85:
            return "HOT"
        return "PEAK"

    def _to_event_view(self, record: EventView) -> EventView:
        return record

    def _to_command_view(self, record: LocalCommandRecord) -> CommandView:
        return CommandView(
            id=record.id,
            cmd_id=record.cmd_id,
            command_type=record.command_type,
            priority_track=record.priority_track,
            status=record.status,
            target_device=record.target_device,
            error_message=record.error_message,
            created_at=record.created_at,
            dispatched_at=record.dispatched_at,
        )

    def _remote_event_to_view(self, payload: dict) -> EventView:
        return EventView(
            id=int(payload.get("id") or 0),
            event_id=str(payload.get("recordId") or payload.get("eventId") or ""),
            event_type=str(payload.get("eventType") or ""),
            priority=str(payload.get("priority") or "C"),
            actor_name=str(payload.get("actorName") or ""),
            content=str(payload.get("content") or ""),
            room_id=str(payload.get("roomId") or ""),
            live_heat=float(payload.get("liveHeat") or 0),
            created_at=self._parse_datetime(payload.get("eventCreatedAt") or payload.get("reportedAt")),
        )

    def _remote_command_to_view(self, payload: dict) -> CommandView:
        return CommandView(
            id=int(payload.get("id") or 0),
            cmd_id=str(payload.get("recordId") or payload.get("cmdId") or ""),
            command_type=str(payload.get("commandType") or ""),
            priority_track=str(payload.get("priorityTrack") or "NORMAL"),
            status=str(payload.get("status") or "queued"),
            target_device=str(payload.get("targetDevice") or ""),
            error_message=str(payload.get("errorMessage") or ""),
            created_at=self._parse_datetime(payload.get("commandCreatedAt") or payload.get("reportedAt")),
            dispatched_at=self._parse_optional_datetime(payload.get("dispatchedAt")),
        )

    def _parse_optional_datetime(self, value: str | None) -> datetime | None:
        if not value:
            return None
        return self._parse_datetime(value)

    def _parse_datetime(self, value: str | None) -> datetime:
        if not value:
            return datetime.utcnow()
        for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%dT%H:%M:%S.%f"):
            try:
                return datetime.strptime(value, fmt)
            except ValueError:
                continue
        try:
            return datetime.fromisoformat(value)
        except ValueError:
            return datetime.utcnow()

    def _next_event_view_id(self) -> int:
        self._event_view_seq += 1
        return self._event_view_seq

    def _next_command_view_id(self) -> int:
        self._command_view_seq += 1
        return self._command_view_seq
