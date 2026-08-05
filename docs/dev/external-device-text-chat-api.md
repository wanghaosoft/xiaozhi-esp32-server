# 外部设备文本对话接口说明

## 适用场景

该接口用于外部服务直接把文本互动内容投递给指定小智设备，例如：

- 直播间弹幕转发
- 互动问答消息推送
- 中控系统下发文本指令
- 第三方业务系统触发设备播报

接口直接调用 manager-api，复用现有设备对话链路，不需要经过 Web 前端页面。

## 启动前提

如果你在本地开发环境验证，请先启动对应服务：

### manager-api

```bash
conda activate xiaozhi-esp32-server
cd /home/wanghao/xiaozhi-esp32-server/main/manager-api
mvn spring-boot:run
```

默认监听地址：

- http://192.168.0.199:8002/xiaozhi

### xiaozhi-server

```bash
conda activate xiaozhi-esp32-server
cd /home/wanghao/xiaozhi-esp32-server/main/xiaozhi-server
python app.py
```

默认 WebSocket 地址：

- ws://192.168.0.199:8000/xiaozhi/v1/

### manager-web

只有当你希望通过前端开发服务器代理访问接口时，才需要启动：

```bash
conda activate xiaozhi-esp32-server
cd /home/wanghao/xiaozhi-esp32-server/main/manager-web
npm run serve
```

默认代理地址：

- http://192.168.0.199:8001/xiaozhi

## 鉴权方式

请求头：

```http
Authorization: Bearer <server.secret>
Content-Type: application/json
```

说明：

- server.secret 为服务端密钥
- 与现有 /config/** 机器间调用使用同一套鉴权机制
- 未携带或填写错误时，接口返回 401

## 接口地址

```http
POST /xiaozhi/device/external/text-chat
```

实际调用有两种方式：

- 后端直连：`http://192.168.0.199:8002/xiaozhi/device/external/text-chat`
- 前端代理：`http://192.168.0.199:8001/xiaozhi/device/external/text-chat`

注意：

- `http://192.168.0.199:8001/device/external/text-chat` 是错误地址
- 因为 manager-api 配置了统一上下文前缀 `/xiaozhi`
- 8001 本身是前端开发服务器，只有走 `/xiaozhi/*` 才会代理到后端

## 请求参数

请求体支持两种设备定位方式，任选一种：

1. 直接传 deviceId
2. 传 agentId + macAddress

请求体字段：

| 字段 | 是否必填 | 说明 |
| --- | --- | --- |
| deviceId | 否 | 设备主键。已知时优先使用，定位最快、最准确 |
| agentId | 条件必填 | 未传 deviceId 时必填 |
| macAddress | 条件必填 | 未传 deviceId 时必填 |
| text | 是 | 要发送给设备的文本内容 |
| interrupt | 否 | 是否先打断设备当前会话，默认 true |

## 请求示例

### 示例一：直接按 deviceId 投递

```bash
curl -X POST "http://192.168.0.199:8002/xiaozhi/device/external/text-chat" \
  -H "Authorization: Bearer your_server_secret" \
  -H "Content-Type: application/json" \
  -d '{
    "deviceId": "9c:13:9e:91:ba:e4",
    "text": "请读取刚刚收到的三条弹幕，并用简短口吻回复。",
    "interrupt": true
  }'
```

### 示例二：按 agentId + macAddress 投递

```bash
curl -X POST "http://192.168.0.199:8002/xiaozhi/device/external/text-chat" \
  -H "Authorization: Bearer your_server_secret" \
  -H "Content-Type: application/json" \
  -d '{
    "agentId": "0734f1046b5948e490f8527ca057f145",
    "macAddress": "9c:13:9e:91:ba:e4",
    "text": "直播间有人问：你现在在做什么？",
    "interrupt": true
  }'
```

如果你已经启动了前端开发服务器，也可以改为：

```bash
curl -X POST "http://192.168.0.199:8001/xiaozhi/device/external/text-chat" \
  -H "Authorization: Bearer your_server_secret" \
  -H "Content-Type: application/json" \
  -d '{
    "agentId": "0734f1046b5948e490f8527ca057f145",
    "macAddress": "9c:13:9e:91:ba:e4",
    "text": "直播间有人问：你现在在做什么？",
    "interrupt": true
  }'
```

## 成功响应

```json
{
  "code": 0,
  "msg": "success",
  "data": "ws://your-server:8000/xiaozhi/v1/"
}
```

说明：

- data 为本次实际投递成功的 Python WebSocket 服务地址
- 返回成功即表示文本已经作为一次新的用户输入送入设备对话链路

## 已验证结果

在当前环境中已完成以下验证：

- `POST http://192.168.0.199:8001/device/external/text-chat`：返回 `Cannot POST /device/external/text-chat`
- `POST http://192.168.0.199:8001/xiaozhi/device/external/text-chat`：接口可达，返回业务结果
- `POST http://192.168.0.199:8002/xiaozhi/device/external/text-chat`：接口可达，返回业务结果
- 不带 `Authorization`：返回 `401`，说明 server.secret 鉴权生效

当前示例设备 `9c:13:9e:91:ba:e4` 返回的是：

```json
{
  "code": 500,
  "msg": "设备当前不在线或文本消息发送失败",
  "data": null
}
```

这说明：

- 接口路径和鉴权已经正确
- manager-api 与 xiaozhi-server 的联动也正常
- 当前失败原因是目标设备不在线，或者设备当前未连接到 WebSocket 服务

## 失败响应说明

常见失败场景：

- 401：Authorization 未携带或服务密钥错误
- 设备不存在：deviceId 不存在，或 agentId + macAddress 未匹配到设备
- deviceId 与 agentId 不匹配：传了 deviceId 和 agentId，但两者不对应
- deviceId 与 macAddress 不匹配：传了 deviceId 和 macAddress，但两者不对应
- agentId 与 macAddress 匹配到多台设备，请改用 deviceId 精确指定：组合无法唯一定位
- 设备当前不在线或文本消息发送失败：设备离线，或后端控制链路投递失败

如果你看到 `Cannot POST /device/external/text-chat`，优先检查是否漏掉了 `/xiaozhi` 前缀。

## 精准控制建议

- 外部系统如果已经保存设备主键，优先使用 deviceId
- 只有在拿不到设备主键时，再使用 agentId + macAddress
- 若业务侧会管理多个相同智能体下的设备，建议在你的系统里持久化 deviceId

## 性能说明

- 接口直接在服务端投递，不经过前端页面
- deviceId 走主键查询，开销最低
- agentId + macAddress 走数据库精确匹配，不做前端轮询或页面转发
- 实际消息投递仍复用已有 WebSocket 控制链路，不重复实现会话逻辑

## 行为说明

发送成功后，后端会：

1. 精准定位目标设备
2. 默认先中断当前设备会话
3. 将 text 作为一次新的用户输入注入原有对话流程
4. 继续复用原有意图识别、LLM、工具调用、TTS 和聊天记录逻辑

因此，外部消息的处理效果与“设备文本对话”页面发送文本保持一致，但链路更短，更适合服务端集成。