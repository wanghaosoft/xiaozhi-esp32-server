# 直播中控架构说明

## 目标

直播中控负责把直播间事件转成可执行、可追踪、可人工干预的结构化动作，再把动作可靠投递给小智机器人。

## 五层职责

### 1. 接入层

负责接收外部直播事件和人工命令。

当前入口：

- POST /api/events/ingest
- POST /api/commands/manual

### 2. 感知层

负责把原始事件归一化为统一结构，并提取决策所需信号：

- 事件类型
- 用户信息
- 礼物信息
- 房间统计
- 关键词路由结果
- LiveHeat 热度

当前实现位于 app/services/preprocessor.py，已覆盖：

- 攻击性弹幕识别
- 噪声弹幕识别
- 价格咨询识别
- 物流咨询识别
- 互动型弹幕识别
- 礼物、欢迎、关注、粉丝团、点赞等基础事件分类

### 3. 决策层

负责维护直播状态和命令队列，按优先级输出结构化命令。

当前实现位于 app/services/brain.py，核心机制包括：

- 三轨队列：EMERGENCY / NORMAL / BATCH
- 机器人状态：IDLE / SPEAKING_KEY / SPEAKING_FILL / BLOCKED
- 直播阶段：WARMUP / PRESENT / INTERACT / CONVERT / WRAP
- LiveHeat 基础热度计算
- 冷场触发 ENGAGE
- 礼物感谢、欢迎、连赞等聚合逻辑

当前版本仍是简化实现，尚未完整覆盖严格版方案中的：

- LLM 多路由器
- 更精细的状态回调闭环
- resume_topic 话题恢复
- 更复杂的熔断与过期策略

### 4. 执行层

负责把结构化命令投递到小智执行端。

当前实现位于 app/services/dispatcher.py，采用兼容模式：

1. 把结构化命令封装为可读提示词
2. 调用小智 manager-api 的外部文本接口
3. 由现有小智链路完成设备投递

兼容模式的优点是接入成本低，能立即复用已有能力；缺点是执行协议仍依赖文本提示词，不是纯结构化执行。

### 5. 展示层

负责让运营能够看到当前直播状态并进行人工干预。

当前实现位于 app/main.py 和 app/static/，包括：

- 实时热度、阶段、机器人状态
- 最近事件列表
- 最近命令列表
- 中控设置编辑
- 人工插入命令

## 数据落库

当前持久化三类数据：

- SettingsRecord：中控设置
- LiveEventRecord：直播事件记录，由小智 manager-api 持久化
- LiveCommandRecord：指令记录，由小智 manager-api 持久化

中控本地数据库仅用于设置存储；事件与命令记录统一上报到小智 manager-api 的直播记录接口。

## 小智接入要求

要让中控自动把决策发给小智，需要配置：

- base_url：指向 manager-api 的 /xiaozhi 根路径
- secret：server.secret
- device_id 或 agent_id + mac_address：精确设备定位

如果这些配置不完整，中控不会阻塞事件处理，但命令会被标记为 failed，便于排查。

## 下一步建议

后续优先级建议如下：

1. 增加抖音抓取端到中控的真实桥接适配器。
2. 为 PRESENT / INTERACT / CONVERT 阶段补齐更细的节奏策略。
3. 引入结构化执行协议，替代当前文本兼容投递。
4. 为关键策略补齐自动化测试和回放验证。