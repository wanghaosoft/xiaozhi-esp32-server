from __future__ import annotations

from datetime import datetime
from typing import Any

import httpx

from app.config import settings as app_settings
from app.schemas import BrainSettings, CommandEnvelope, NormalizedEvent


class XiaozhiReporter:
    def report_event(
        self,
        settings: BrainSettings,
        normalized: NormalizedEvent,
        live_heat: float,
        created_at: datetime,
    ) -> tuple[bool, str]:
        target = settings.xiaozhi_target
        if not target.base_url or not target.secret:
            return False, "xiaozhi target is not configured"

        payload = {
            "source": "douyin-live-brain",
            "recordId": normalized.event_id,
            "roomId": normalized.room_id,
            "roomTitle": settings.room_title,
            "eventType": normalized.event_type.value,
            "priority": normalized.priority.value,
            "actorId": normalized.actor_id,
            "actorName": normalized.actor_name,
            "content": normalized.content,
            "liveHeat": live_heat,
            "normalizedPayload": normalized.model_dump(mode="json"),
            "rawPayload": normalized.raw_payload,
            "eventCreatedAt": self._to_iso(created_at),
        }
        return self._post(target.base_url, target.secret, "/device/external/live-records/events", payload)

    def report_command(
        self,
        settings: BrainSettings,
        command: CommandEnvelope,
        status: str,
        target_device: str,
        error_message: str,
        room_id: str,
        room_title: str,
        created_at: datetime,
        dispatched_at: datetime | None,
    ) -> tuple[bool, str]:
        target = settings.xiaozhi_target
        if not target.base_url or not target.secret:
            return False, "xiaozhi target is not configured"

        payload = {
            "source": "douyin-live-brain",
            "recordId": command.cmd_id,
            "roomId": room_id,
            "roomTitle": room_title,
            "commandType": command.type,
            "priorityTrack": command.priority.value,
            "status": status,
            "targetDevice": target_device,
            "errorMessage": error_message,
            "payload": command.model_dump(mode="json"),
            "commandCreatedAt": self._to_iso(created_at),
            "dispatchedAt": self._to_iso(dispatched_at),
        }
        return self._post(target.base_url, target.secret, "/device/external/live-records/commands", payload)

    def fetch_events(self, settings: BrainSettings, limit: int) -> list[dict[str, Any]]:
        target = settings.xiaozhi_target
        if not target.base_url or not target.secret:
            return []
        return self._get(target.base_url, target.secret, "/device/external/live-records/events", {"limit": limit})

    def fetch_commands(self, settings: BrainSettings, limit: int) -> list[dict[str, Any]]:
        target = settings.xiaozhi_target
        if not target.base_url or not target.secret:
            return []
        return self._get(target.base_url, target.secret, "/device/external/live-records/commands", {"limit": limit})

    def _post(self, base_url: str, secret: str, path: str, payload: dict[str, Any]) -> tuple[bool, str]:
        headers = {
            "Authorization": f"Bearer {secret}",
            "Content-Type": "application/json",
        }
        url = f"{base_url.rstrip('/')}{path}"
        try:
            with httpx.Client(timeout=app_settings.xiaozhi_timeout_seconds) as client:
                response = client.post(url, headers=headers, json=payload)
            if response.status_code != 200:
                return False, f"http {response.status_code}: {response.text}"

            body = response.json()
            if body.get("code") != 0:
                return False, body.get("msg") or "unknown error"
            return True, body.get("data") or ""
        except (httpx.HTTPError, ValueError) as exc:
            return False, str(exc)

    def _get(self, base_url: str, secret: str, path: str, params: dict[str, Any]) -> list[dict[str, Any]]:
        headers = {"Authorization": f"Bearer {secret}"}
        url = f"{base_url.rstrip('/')}{path}"
        try:
            with httpx.Client(timeout=app_settings.xiaozhi_timeout_seconds) as client:
                response = client.get(url, headers=headers, params=params)
            if response.status_code != 200:
                return []
            body = response.json()
            if body.get("code") != 0:
                return []
            data = body.get("data")
            return data if isinstance(data, list) else []
        except (httpx.HTTPError, ValueError):
            return []

    def _to_iso(self, value: datetime | None) -> str | None:
        if value is None:
            return None
        return value.isoformat()