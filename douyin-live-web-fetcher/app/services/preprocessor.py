from __future__ import annotations

import re

from app.schemas import BrainSettings, EventType, LiveEventIn, NormalizedEvent, PriorityLevel


class EventPreprocessor:
    _noise_pattern = re.compile(r"^[\s\d~!,.?。！？👍❤️🔥]+$")

    def normalize(self, event: LiveEventIn, settings: BrainSettings) -> NormalizedEvent:
        actor_name = (event.user.name or "").strip()
        actor_id = (event.user.id or "").strip()
        content = (event.content or "").strip()
        gift_name = event.gift.name if event.gift else ""
        gift_price = event.gift.price if event.gift else 0

        normalized = NormalizedEvent(
            event_id=event.event_id or "",
            event_type=event.event_type,
            priority=self._base_priority(event.event_type, gift_price),
            actor_id=actor_id,
            actor_name=actor_name,
            room_id=(event.room_id or settings.room_id or "").strip(),
            content=content,
            gift_name=gift_name,
            gift_price=gift_price,
            room_metrics=event.room,
            raw_payload=event.raw_payload,
        )

        if event.event_type == EventType.CHAT:
            self._route_chat(normalized, settings)

        return normalized

    def _base_priority(self, event_type: EventType, gift_price: int) -> PriorityLevel:
        if event_type == EventType.GIFT:
            return PriorityLevel.S if gift_price >= 100 else PriorityLevel.A
        if event_type in {EventType.SOCIAL, EventType.FANSCLUB}:
            return PriorityLevel.A
        if event_type in {EventType.MEMBER, EventType.LIKE}:
            return PriorityLevel.B
        if event_type in {EventType.ROOM_STATS, EventType.ROOM_USER_SEQ, EventType.ROOM_DATA_SYNC}:
            return PriorityLevel.C
        return PriorityLevel.B

    def _route_chat(self, event: NormalizedEvent, settings: BrainSettings) -> None:
        text = event.content.strip()
        if not text:
            event.priority = PriorityLevel.C
            return

        lower_text = text.lower()
        if any(keyword.lower() in lower_text for keyword in settings.moderation.blocked_keywords):
            event.priority = PriorityLevel.C
            event.intent_type = "blocked"
            return

        if self._noise_pattern.match(text):
            event.priority = PriorityLevel.C
            event.intent_type = "noise"
            return

        if any(keyword.lower() in lower_text for keyword in settings.moderation.negative_keywords):
            event.priority = PriorityLevel.S
            event.need_reply = True
            event.intent_type = "negative_attack"
            event.reply_hint = "请保持直播秩序，理性沟通。"
            return

        if any(keyword.lower() in lower_text for keyword in settings.moderation.price_keywords):
            event.priority = PriorityLevel.A
            event.need_reply = True
            event.intent_type = "product_consulting"
            event.reply_hint = "价格和优惠我马上给大家统一讲一下。"
            return

        if any(keyword.lower() in lower_text for keyword in settings.moderation.logistics_keywords):
            event.priority = PriorityLevel.A
            event.need_reply = True
            event.intent_type = "logistics"
            event.reply_hint = "发货和快递问题我给大家统一说明。"
            return

        if any(keyword.lower() in lower_text for keyword in settings.moderation.interaction_keywords):
            event.priority = PriorityLevel.A
            event.need_reply = True
            event.intent_type = "interaction"
            event.reply_hint = "这个问题问得好，我现在就回答。"
            return

        event.priority = PriorityLevel.B
        event.need_reply = False
        event.intent_type = "small_talk"
