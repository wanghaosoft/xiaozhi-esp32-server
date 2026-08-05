from __future__ import annotations

import json
from datetime import datetime

import httpx

from app.schemas import BrainSettings, CommandEnvelope


class XiaozhiDispatcher:
    def dispatch(self, command: CommandEnvelope, settings: BrainSettings) -> tuple[bool, str]:
        target = settings.xiaozhi_target
        if not target.base_url or not target.secret:
            return False, "xiaozhi target is not configured"

        payload = self._build_payload(command, settings)
        headers = {
            "Authorization": f"Bearer {target.secret}",
            "Content-Type": "application/json",
        }

        url = f"{target.base_url.rstrip('/')}/device/external/text-chat"
        try:
            with httpx.Client(timeout=12.0) as client:
                response = client.post(url, headers=headers, json=payload)
            if response.status_code != 200:
                return False, f"http {response.status_code}: {response.text}"

            body = response.json()
            if body.get("code") != 0:
                return False, body.get("msg") or "unknown error"
            return True, body.get("data") or ""
        except (httpx.HTTPError, ValueError) as exc:
            return False, str(exc)

    def _build_payload(self, command: CommandEnvelope, settings: BrainSettings) -> dict:
        target = settings.xiaozhi_target
        payload = {
            "text": self._build_compatibility_prompt(command, settings),
            "interrupt": command.interrupt if command.interrupt is not None else target.interrupt_default,
        }
        if target.device_id:
            payload["deviceId"] = target.device_id
        else:
            payload["agentId"] = target.agent_id
            payload["macAddress"] = target.mac_address
        return payload

    def _build_compatibility_prompt(self, command: CommandEnvelope, settings: BrainSettings) -> str:
        hint = {
            "cmd_id": command.cmd_id,
            "type": command.type,
            "priority": command.priority.value,
            "stage": settings.stage.value,
            "topic": settings.current_topic,
            "params": command.params,
            "generated_at": datetime.utcnow().isoformat(),
        }
        return (
            "你现在扮演直播执行机器人，只需要根据中控指令生成直播口播内容并自然说出来，"
            "不要解释协议、不要复述JSON、不要提中控系统。"
            "请严格围绕当前直播话题进行表达。指令如下："
            f"{json.dumps(hint, ensure_ascii=False)}"
        )
