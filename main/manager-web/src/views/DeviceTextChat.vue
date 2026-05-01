<template>
  <div class="welcome">
    <HeaderBar />

    <div class="operation-bar">
      <div>
        <h2 class="page-title">设备文本对话</h2>
        <div class="page-subtitle">在页面输入文本，服务端会打断设备当前对话并像语音识别结果一样继续后续问答。</div>
      </div>
      <div class="right-operations">
        <el-button @click="goBack">返回设备管理</el-button>
      </div>
    </div>

    <div class="main-wrapper">
      <div class="content-panel">
        <div class="content-area">
          <el-card shadow="never" class="chat-card">
            <div class="device-meta">
              <div class="meta-item">
                <span class="label">设备ID</span>
                <span class="value">{{ deviceId || '-' }}</span>
              </div>
              <div class="meta-item">
                <span class="label">MAC</span>
                <span class="value">{{ macAddress || '-' }}</span>
              </div>
              <div class="meta-item">
                <span class="label">型号</span>
                <span class="value">{{ model || '-' }}</span>
              </div>
              <div class="meta-item">
                <span class="label">当前状态</span>
                <el-tag :type="statusTagType">{{ statusText }}</el-tag>
              </div>
            </div>

            <el-alert
              title="发送后会先下发 stop，再把文本作为用户输入送入现有对话链路。"
              type="info"
              :closable="false"
              show-icon
            />

            <div class="editor-block">
              <div class="editor-label">输入文本</div>
              <el-input
                v-model="text"
                type="textarea"
                :rows="8"
                maxlength="1000"
                show-word-limit
                placeholder="请输入要发送给小智机器人的文本，例如：今天的天气怎么样？"
              />
            </div>

            <div class="options-row">
              <el-switch v-model="interrupt" active-text="发送前打断当前对话" inactive-text="不主动打断" />
            </div>

            <div class="actions-row">
              <el-button type="primary" :loading="sending" @click="sendText">发送文本</el-button>
              <el-button @click="fillExample('今天天气怎么样，顺便告诉我适合穿什么衣服？')">填充示例</el-button>
              <el-button @click="fillExample('帮我总结一下今天的聊天重点。')">填充总结示例</el-button>
              <el-button @click="clearText">清空</el-button>
            </div>

            <div class="history-block">
              <div class="history-title">发送记录</div>
              <div v-if="sendHistory.length === 0" class="empty-history">暂无发送记录</div>
              <div v-for="item in sendHistory" :key="item.id" class="history-item">
                <div class="history-item-header">
                  <span :class="['status-dot', item.success ? 'success' : 'error']"></span>
                  <span class="history-time">{{ item.time }}</span>
                  <span class="history-message">{{ item.message }}</span>
                </div>
                <div class="history-content">{{ item.text }}</div>
              </div>
            </div>
          </el-card>
        </div>
      </div>
    </div>

    <el-footer>
      <version-footer />
    </el-footer>
  </div>
</template>

<script>
import Api from '@/apis/api';
import HeaderBar from '@/components/HeaderBar.vue';
import VersionFooter from '@/components/VersionFooter.vue';

export default {
  name: 'DeviceTextChat',
  components: {
    HeaderBar,
    VersionFooter,
  },
  data() {
    return {
      text: '',
      interrupt: true,
      sending: false,
      sendHistory: [],
      deviceId: this.$route.query.deviceId || '',
      agentId: this.$route.query.agentId || '',
      macAddress: this.$route.query.macAddress || '',
      model: this.$route.query.model || '',
      status: this.$route.query.status || 'offline',
    }
  },
  computed: {
    statusText() {
      return this.status === 'online' ? '在线' : '离线/未知'
    },
    statusTagType() {
      return this.status === 'online' ? 'success' : 'info'
    },
  },
  methods: {
    goBack() {
      this.$router.push({ path: '/device-management', query: { agentId: this.agentId } })
    },
    clearText() {
      this.text = ''
    },
    fillExample(example) {
      this.text = example
    },
    appendHistory(success, message, text) {
      this.sendHistory.unshift({
        id: `${Date.now()}-${Math.random()}`,
        success,
        message,
        text,
        time: new Date().toLocaleString(),
      })
    },
    sendText() {
      const payloadText = (this.text || '').trim()
      if (!this.deviceId) {
        this.$message.error('缺少设备ID，无法发送')
        return
      }
      if (!payloadText) {
        this.$message.warning('请输入要发送的文本')
        return
      }
      this.sending = true
      Api.device.sendTextChat(this.deviceId, {
        text: payloadText,
        interrupt: this.interrupt,
      }, ({ data }) => {
        this.sending = false
        if (data.code === 0) {
          const message = data.data ? `已投递到 ${data.data}` : '发送成功'
          this.$message.success(message)
          this.appendHistory(true, message, payloadText)
          this.text = ''
          this.status = 'online'
          return
        }
        const errorMessage = data.msg || '发送失败'
        this.$message.error(errorMessage)
        this.appendHistory(false, errorMessage, payloadText)
      })
    },
  },
}
</script>

<style scoped>
.welcome {
  min-width: 900px;
  min-height: 506px;
  height: 100vh;
  display: flex;
  position: relative;
  flex-direction: column;
  background: linear-gradient(to bottom right, #dce8ff, #e4eeff, #e6cbfd);
}

.operation-bar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 24px;
}

.page-title {
  margin: 0;
  font-size: 24px;
}

.page-subtitle {
  margin-top: 8px;
  color: #667085;
  font-size: 14px;
}

.right-operations {
  display: flex;
  gap: 10px;
}

.main-wrapper {
  height: calc(100vh - 63px - 35px - 72px);
  margin: 0 22px;
  border-radius: 15px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.1);
  background: rgba(237, 242, 255, 0.5);
  display: flex;
  flex-direction: column;
}

.content-panel {
  flex: 1;
  display: flex;
  overflow: hidden;
  border-radius: 15px;
  background: transparent;
  border: 1px solid #fff;
}

.content-area {
  flex: 1;
  padding: 20px;
  overflow: auto;
}

.chat-card {
  background: rgba(255, 255, 255, 0.72);
  border-radius: 16px;
}

.device-meta {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 12px;
  margin-bottom: 20px;
}

.meta-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px 14px;
  border-radius: 12px;
  background: #f6f8ff;
}

.label {
  width: 72px;
  color: #667085;
}

.value {
  color: #344054;
  word-break: break-all;
}

.editor-block {
  margin-top: 20px;
}

.editor-label,
.history-title {
  margin-bottom: 12px;
  font-weight: 600;
  color: #344054;
}

.options-row,
.actions-row {
  margin-top: 20px;
  display: flex;
  align-items: center;
  gap: 12px;
  flex-wrap: wrap;
}

.history-block {
  margin-top: 28px;
}

.empty-history {
  color: #98a2b3;
  padding: 18px 0;
}

.history-item {
  padding: 12px 14px;
  border-radius: 12px;
  background: #f8faff;
  margin-bottom: 12px;
}

.history-item-header {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 8px;
}

.status-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  display: inline-block;
}

.status-dot.success {
  background: #12b76a;
}

.status-dot.error {
  background: #f04438;
}

.history-time {
  color: #667085;
  font-size: 12px;
}

.history-message {
  color: #344054;
  font-size: 13px;
}

.history-content {
  color: #101828;
  white-space: pre-wrap;
  word-break: break-word;
}
</style>
