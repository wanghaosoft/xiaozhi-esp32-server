# 抖音直播中控大脑

该项目是独立于小智服务端部署的直播中控系统，负责：

- 接收并标准化抖音直播事件
- 计算直播间状态与 LiveHeat 热度指数
- 根据三轨队列和优先级规则生成结构化指令
- 通过兼容层把决策结果投递给小智机器人
- 本地保存中控设置，并把直播事件、调度指令同步到小智后端持久化
- 提供设置页与实时中控展示页

## 当前实现

当前版本已经具备可运行的第一阶段能力：

- FastAPI 服务入口
- MySQL/SQLite 通用数据库层
- 直播事件标准化与后端同步
- LiveHeat 基础热度计算
- 三轨队列基础调度
- 小智兼容投递器
- 设置页、实时看板、人工干预入口

当前仍属于兼容版中控，后续会继续补齐：

- 更细粒度的直播阶段切换
- 更完整的 LLM 路由与话题恢复
- 更严格的队列过期、合流与熔断策略
- 独立于文本提示词的结构化小智执行协议

## 架构分层

当前实现按五层组织：

1. 接入层：接收直播事件与人工指令。
2. 感知层：完成事件标准化、分类和热度计算。
3. 决策层：根据优先级、冷场时间和队列状态生成结构化命令。
4. 执行层：把结构化命令转换成兼容负载并投递到小智服务端。
5. 展示层：提供设置页、实时看板和最近事件/命令回放。

队列采用三轨：

- EMERGENCY：高优先级礼物、攻击性消息等需要抢占处理的事件。
- NORMAL：普通咨询、互动回复等常规指令。
- BATCH：欢迎、连赞、冷场暖场等可聚合任务。

更多设计细节见 [docs/architecture.md](docs/architecture.md)。

## 启动方式

```bash
cd /home/wanghao/xiaozhi-esp32-server/douyin-live-web-fetcher
pip install -r requirements.txt
uvicorn app.main:app --reload --host 0.0.0.0 --port 8090
```

默认页面：

- http://127.0.0.1:8090/

## 环境变量

复制 .env.example 后按需填写：

```bash
cp .env.example .env
```

关键配置说明：

- LIVE_BRAIN_DATABASE_URL：中控本地设置存储连接，默认可用 SQLite；事件与命令记录不再落本地库。
- LIVE_BRAIN_XIAOZHI_BASE_URL：小智 manager-api 地址，需带 /xiaozhi 前缀，例如 http://192.168.0.199:8002/xiaozhi。
- LIVE_BRAIN_XIAOZHI_SECRET：小智服务端 server.secret，对应外部文本接口鉴权。
- LIVE_BRAIN_SETTINGS_KEY：设置存储主键，支持多套配置。

MySQL 示例：

```env
LIVE_BRAIN_DATABASE_URL=mysql+pymysql://root:password@127.0.0.1:3306/live_brain?charset=utf8mb4
```

## 小智兼容投递

当前版本通过已有外部文本接口把结构化命令兼容投递给小智：

- 目标接口：POST /xiaozhi/device/external/text-chat
- 鉴权方式：Authorization: Bearer <server.secret>
- 定位方式：优先 deviceId，也支持 agentId + macAddress 精准定位

要让自动投递真正生效，需要在设置页中补齐：

- 小智服务地址
- 小智服务密钥
- deviceId 或 agentId + macAddress

如果未配置这些字段，中控仍会继续完成事件处理、决策和页面展示，但无法把事件/命令同步到小智后端，命令状态会标记为 failed，错误为 xiaozhi target is not configured。

## HTTP API

已开放的核心接口：

- GET /health：健康检查
- GET /api/settings：读取当前中控配置
- PUT /api/settings：更新中控配置
- GET /api/dashboard：获取实时看板快照
- GET /api/events：分页查看事件记录
- GET /api/commands：分页查看命令记录
- POST /api/events/ingest：注入标准化直播事件
- POST /api/commands/manual：插入人工干预命令

事件注入示例：

```bash
curl -X POST 'http://127.0.0.1:8090/api/events/ingest' \
	-H 'Content-Type: application/json' \
	-d '{
		"event_id": "evt-demo-1",
		"event_type": "CHAT",
		"room_id": "room-demo",
		"content": "这个多少钱？",
		"user": {
			"id": "user-1",
			"name": "测试观众"
		},
		"raw_payload": {
			"source": "manual-test"
		}
	}'
```

## 开发验证状态

当前已完成以下运行验证：

- FastAPI 入口可正常导入
- 首页、设置接口、看板接口可正常返回
- GIFT 与 CHAT 事件可成功同步到小智后端记录接口
- 冷场任务在未配置小智目标时不会继续刷屏生成失败记录

## 部署约束

- 生产环境中，douyin-live-web-fetcher 与 xiaozhi-server 不应部署在同一台机器。
- 开发环境可以临时同机部署，便于联调。
- 生产环境建议将数据库切换为 MySQL，并为中控服务单独配置网络、日志与监控。
