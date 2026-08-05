# 设备文本对话功能使用说明

## 功能目标

新增“设备文本对话”能力：

- 在管理后台页面输入文本
- 服务端把文本作为一次新的用户输入送入现有对话链路
- 默认会先打断设备当前正在播报/对话的内容
- 文本会像语音识别结果一样同步到硬件端显示
- 不改动原有语音交互逻辑，属于并行新增能力

## 页面入口

Web 管理后台中进入：

1. 打开 `设备管理`
2. 在目标设备所在行点击 `文本对话`
3. 进入 `设备文本对话` 页面
4. 输入文本并发送

## 发送效果

发送成功后，后端执行顺序如下：

1. 通过控制链路定位当前在线设备连接
2. 默认发送一次中断指令，停止设备当前 TTS/对话播报
3. 将页面输入的文本按“用户输入”送入现有 `startToChat(...)` 流程
4. 服务端继续复用现有：
   - 意图识别
   - LLM 对话
   - 工具调用
   - TTS 合成
   - 聊天记录上报
5. 设备端会收到：
   - `stt` 文本显示消息
   - 新一轮 `tts` 音频播报
- 页面发送的文本也会按“用户消息”写入聊天记录；当前该入口不上传语音，因此聊天记录中的音频字段为空，便于后续扩展页面语音输入能力。

## 后端接口

### 业务接口

`POST /device/text-chat/{deviceId}`

请求体：

```json
{
  "text": "今天天气怎么样？",
  "interrupt": true
}
```

字段说明：

- `text`：必填，要发送给设备的文本
- `interrupt`：可选，默认 `true`，表示发送前先打断当前设备对话

成功响应示例：

```json
{
  "code": 0,
  "msg": "success",
  "data": "ws://your-server:8000/xiaozhi/v1/"
}
```

说明：`data` 为实际投递成功的 Python WebSocket 服务地址。

### 外部调用接口

适用于直播弹幕、互动消息、中控系统等服务端直接投递文本，不依赖前端页面。

- 后端直连地址：`POST /xiaozhi/device/external/text-chat`
- 前端代理地址：`POST /xiaozhi/device/external/text-chat`
- 鉴权方式：`Authorization: Bearer <server.secret>`
- 设备定位：优先传 `deviceId`，或传 `agentId + macAddress`
- 完整对接说明见：`docs/dev/external-device-text-chat-api.md`

说明：

- 若直连 manager-api，默认地址为 `http://<host>:8002/xiaozhi/device/external/text-chat`
- 若走 manager-web 开发代理，默认地址为 `http://<host>:8001/xiaozhi/device/external/text-chat`
- `http://<host>:8001/device/external/text-chat` 是错误地址，因为缺少 `/xiaozhi`

## 实现说明

### Java 管理后台

主要改动：

- `manager-api` 新增接口：`DeviceController.sendTextChat(...)`
- `manager-api` 新增外部接口：`DeviceController.sendTextChatByExternal(...)`
- `DeviceServiceImpl.sendTextChat(...)` 负责：
  - 校验设备归属
  - 遍历配置的 Python WebSocket 服务地址
  - 通过已有 `server` 控制消息链路发送 `text_chat` 指令
- `DeviceServiceImpl.sendTextChatByExternal(...)` 负责：
  - 使用 `deviceId` 或 `agentId + macAddress` 精准定位设备
  - 复用同一条服务端投递链路
  - 通过 `server.secret` 进行服务间鉴权

### Python 运行时

主要改动：

- `WebSocketServer` 增加在线连接注册表
- `ConnectionHandler` 在连接建立/关闭时注册和注销设备连接
- `ServerTextMessageHandler` 新增 `text_chat` 动作处理
- `ConnectionHandler.handle_manual_text_input(...)` 复用原有 `startToChat(...)` 链路

### 前端页面

- 新增页面：`manager-web/src/views/DeviceTextChat.vue`
- 入口：`DeviceManagement.vue` 行内按钮 `文本对话`

## 使用建议

- 仅对在线设备使用；若设备不在线，会返回发送失败
- 默认保留 `interrupt=true`，这样更符合“文本代替当前语音输入”的交互预期
- 若你希望排队而不是打断，可将 `interrupt` 设为 `false`
- 外部系统对接时优先传 `deviceId`；只有在无法拿到设备主键时，再使用 `agentId + macAddress`

## 不影响现有功能的原因

本次实现没有替换原语音链路，只是新增了一条“页面文本输入 → 复用现有对话链路”的入口：

- 语音输入仍走原有 ASR / VAD / listen 流程
- 设备显示仍复用现有 `stt` 消息
- TTS 仍复用现有发送逻辑
- 对话、工具调用、上报、记忆保存逻辑均保持原样

因此该功能属于“无缝新增”，不会改变原有语音交互行为。
