import json
from typing import Dict, Any

from core.handle.textMessageHandler import TextMessageHandler
from core.handle.textMessageType import TextMessageType

TAG = __name__

class ServerTextMessageHandler(TextMessageHandler):
    """MCP消息处理器"""

    @property
    def message_type(self) -> TextMessageType:
        return TextMessageType.SERVER

    async def handle(self, conn, msg_json: Dict[str, Any]) -> None:
        # 如果配置是从API读取的，则需要验证secret
        if not conn.read_config_from_api:
            return
        # 获取post请求的secret
        post_secret = msg_json.get("content", {}).get("secret", "")
        secret = conn.config["manager-api"].get("secret", "")
        # 如果secret不匹配，则返回
        if post_secret != secret:
            await conn.websocket.send(
                json.dumps(
                    {
                        "type": "server",
                        "status": "error",
                        "message": "服务器密钥验证失败",
                    }
                )
            )
            return
        # 动态更新配置
        if msg_json["action"] == "update_config":
            try:
                # 更新WebSocketServer的配置
                if not conn.server:
                    await conn.websocket.send(
                        json.dumps(
                            {
                                "type": "server",
                                "status": "error",
                                "message": "无法获取服务器实例",
                                "content": {"action": "update_config"},
                            }
                        )
                    )
                    return

                if not await conn.server.update_config():
                    await conn.websocket.send(
                        json.dumps(
                            {
                                "type": "server",
                                "status": "error",
                                "message": "更新服务器配置失败",
                                "content": {"action": "update_config"},
                            }
                        )
                    )
                    return

                # 发送成功响应
                await conn.websocket.send(
                    json.dumps(
                        {
                            "type": "server",
                            "status": "success",
                            "message": "配置更新成功",
                            "content": {"action": "update_config"},
                        }
                    )
                )
            except Exception as e:
                conn.logger.bind(tag=TAG).error(f"更新配置失败: {str(e)}")
                await conn.websocket.send(
                    json.dumps(
                        {
                            "type": "server",
                            "status": "error",
                            "message": f"更新配置失败: {str(e)}",
                            "content": {"action": "update_config"},
                        }
                    )
                )
        # 重启服务器
        elif msg_json["action"] == "restart":
            await conn.handle_restart(msg_json)
        elif msg_json["action"] == "text_chat":
            if not conn.server:
                await conn.websocket.send(
                    json.dumps(
                        {
                            "type": "server",
                            "status": "error",
                            "message": "无法获取服务器实例",
                            "content": {"action": "text_chat"},
                        }
                    )
                )
                return

            device_id = msg_json.get("content", {}).get("device_id", "")
            text = msg_json.get("content", {}).get("text", "")
            interrupt = msg_json.get("content", {}).get("interrupt", True)

            if not device_id or not text:
                await conn.websocket.send(
                    json.dumps(
                        {
                            "type": "server",
                            "status": "error",
                            "message": "device_id 和 text 不能为空",
                            "content": {"action": "text_chat"},
                        }
                    )
                )
                return

            success, message = await conn.server.send_text_to_device(device_id, text, interrupt)
            await conn.websocket.send(
                json.dumps(
                    {
                        "type": "server",
                        "status": "success" if success else "error",
                        "message": message,
                        "content": {"action": "text_chat", "device_id": device_id},
                    }
                )
            )