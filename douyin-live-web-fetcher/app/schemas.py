from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class EventType(str, Enum):
    CHAT = "CHAT"
    GIFT = "GIFT"
    MEMBER = "MEMBER"
    SOCIAL = "SOCIAL"
    FANSCLUB = "FANSCLUB"
    LIKE = "LIKE"
    ROOM_STATS = "ROOM_STATS"
    ROOM_USER_SEQ = "ROOM_USER_SEQ"
    ROOM_DATA_SYNC = "ROOM_DATA_SYNC"
    CUSTOM = "CUSTOM"


class PriorityLevel(str, Enum):
    S = "S"
    A = "A"
    B = "B"
    C = "C"


class RobotState(str, Enum):
    IDLE = "IDLE"
    SPEAKING_KEY = "SPEAKING_KEY"
    SPEAKING_FILL = "SPEAKING_FILL"
    BLOCKED = "BLOCKED"


class LiveStage(str, Enum):
    WARMUP = "WARMUP"
    PRESENT = "PRESENT"
    INTERACT = "INTERACT"
    CONVERT = "CONVERT"
    WRAP = "WRAP"


class QueueTrack(str, Enum):
    EMERGENCY = "EMERGENCY"
    NORMAL = "NORMAL"
    BATCH = "BATCH"


class UserRef(BaseModel):
    id: str = ""
    name: str = ""


class GiftRef(BaseModel):
    name: str = ""
    price: int = 0
    count: int = 1


class RoomMetrics(BaseModel):
    audience_count: int = 0
    like_count: int = 0
    follow_count: int = 0
    total_user_count: int = 0
    status: int | None = None


class LiveEventIn(BaseModel):
    event_id: str = ""
    event_type: EventType
    room_id: str = ""
    content: str = ""
    user: UserRef = Field(default_factory=UserRef)
    gift: GiftRef | None = None
    room: RoomMetrics | None = None
    raw_payload: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime | None = None


class NormalizedEvent(BaseModel):
    event_id: str
    event_type: EventType
    priority: PriorityLevel
    actor_id: str = ""
    actor_name: str = ""
    room_id: str = ""
    content: str = ""
    need_reply: bool = False
    intent_type: str = ""
    reply_hint: str = ""
    merged_count: int = 1
    gift_name: str = ""
    gift_price: int = 0
    room_metrics: RoomMetrics | None = None
    raw_payload: dict[str, Any] = Field(default_factory=dict)


class XiaozhiTargetSettings(BaseModel):
    mode: str = "external_text_chat"
    base_url: str = ""
    secret: str = ""
    device_id: str = ""
    agent_id: str = ""
    mac_address: str = ""
    interrupt_default: bool = True


class ModerationSettings(BaseModel):
    blocked_keywords: list[str] = Field(default_factory=lambda: ["加微", "私聊", "返现", "赌博", "刷单"])
    negative_keywords: list[str] = Field(default_factory=lambda: ["骗子", "假货", "投诉", "举报", "坑人"])
    price_keywords: list[str] = Field(default_factory=lambda: ["多少钱", "价格", "优惠", "券", "便宜"])
    logistics_keywords: list[str] = Field(default_factory=lambda: ["发货", "快递", "包邮", "几天到"])
    interaction_keywords: list[str] = Field(default_factory=lambda: ["好用吗", "适合", "推荐", "怎么选"])


class QueueSettings(BaseModel):
    gift_bucket_seconds: int = 10
    welcome_bucket_seconds: int = 15
    follow_bucket_seconds: int = 10
    like_storm_window_seconds: int = 5
    like_storm_threshold_per_window: int = 50
    batch_cooldown_seconds: int = 30
    welcome_cooldown_seconds: int = 45
    normal_queue_limit: int = 5
    normal_expire_seconds: int = 60
    batch_expire_seconds: int = 120


class IdleSettings(BaseModel):
    level1_seconds: int = 10
    level2_seconds: int = 25
    level3_seconds: int = 45
    level4_seconds: int = 60


class HeatSettings(BaseModel):
    cold_threshold: float = 20.0
    calm_threshold: float = 40.0
    active_threshold: float = 65.0
    hot_threshold: float = 85.0


class BrainSettings(BaseModel):
    stage: LiveStage = LiveStage.WARMUP
    robot_state: RobotState = RobotState.IDLE
    blocked: bool = False
    current_topic: str = "默认话题"
    room_id: str = ""
    room_title: str = ""
    xiaozhi_target: XiaozhiTargetSettings = Field(default_factory=XiaozhiTargetSettings)
    moderation: ModerationSettings = Field(default_factory=ModerationSettings)
    queue: QueueSettings = Field(default_factory=QueueSettings)
    idle: IdleSettings = Field(default_factory=IdleSettings)
    heat: HeatSettings = Field(default_factory=HeatSettings)


class CommandEnvelope(BaseModel):
    cmd_id: str
    priority: QueueTrack
    type: str
    params: dict[str, Any]
    interrupt: bool = False
    resume_topic: str = ""
    created_at: datetime = Field(default_factory=datetime.utcnow)


class EventView(BaseModel):
    id: int
    event_id: str
    event_type: str
    priority: str
    actor_name: str
    content: str
    room_id: str
    live_heat: float
    created_at: datetime


class CommandView(BaseModel):
    id: int
    cmd_id: str
    command_type: str
    priority_track: str
    status: str
    target_device: str
    error_message: str
    created_at: datetime
    dispatched_at: datetime | None = None


class DashboardSnapshot(BaseModel):
    live_heat: float
    heat_bucket: str
    robot_state: RobotState
    stage: LiveStage
    blocked: bool
    current_topic: str
    queue_sizes: dict[str, int]
    recent_events: list[EventView]
    recent_commands: list[CommandView]
    room_metrics: RoomMetrics


class ManualCommandIn(BaseModel):
    text: str = Field(min_length=1)
    command_type: str = "CUSTOM_SCRIPT"
    priority: QueueTrack = QueueTrack.EMERGENCY
    interrupt: bool = True
