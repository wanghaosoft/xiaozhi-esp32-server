const stageOptions = ["WARMUP", "PRESENT", "INTERACT", "CONVERT", "WRAP"];
const robotStateOptions = ["IDLE", "SPEAKING_KEY", "SPEAKING_FILL", "BLOCKED"];

const els = {
  healthStatus: document.querySelector("#healthStatus"),
  metricsGrid: document.querySelector("#metricsGrid"),
  eventsTable: document.querySelector("#eventsTable"),
  commandsTable: document.querySelector("#commandsTable"),
  saveSettingsBtn: document.querySelector("#saveSettingsBtn"),
  sendManualBtn: document.querySelector("#sendManualBtn"),
  roomId: document.querySelector("#roomId"),
  stage: document.querySelector("#stage"),
  robotState: document.querySelector("#robotState"),
  currentTopic: document.querySelector("#currentTopic"),
  roomTitle: document.querySelector("#roomTitle"),
  xiaozhiBaseUrl: document.querySelector("#xiaozhiBaseUrl"),
  xiaozhiSecret: document.querySelector("#xiaozhiSecret"),
  deviceId: document.querySelector("#deviceId"),
  agentId: document.querySelector("#agentId"),
  macAddress: document.querySelector("#macAddress"),
  blocked: document.querySelector("#blocked"),
  manualText: document.querySelector("#manualText"),
};

let currentSettings = null;

function fillOptions(element, options) {
  element.innerHTML = options.map((value) => `<option value="${value}">${value}</option>`).join("");
}

fillOptions(els.stage, stageOptions);
fillOptions(els.robotState, robotStateOptions);

function fmtTime(value) {
  if (!value) return "-";
  return new Date(value).toLocaleTimeString("zh-CN", { hour12: false });
}

function renderMetrics(snapshot) {
  const items = [
    ["LiveHeat", snapshot.live_heat],
    ["热度档位", snapshot.heat_bucket],
    ["机器人状态", snapshot.robot_state],
    ["直播阶段", snapshot.stage],
    ["在线人数", snapshot.room_metrics?.audience_count ?? 0],
    ["点赞总量", snapshot.room_metrics?.like_count ?? 0],
    ["关注总量", snapshot.room_metrics?.follow_count ?? 0],
    ["队列", `E ${snapshot.queue_sizes.emergency} / N ${snapshot.queue_sizes.normal} / B ${snapshot.queue_sizes.batch}`],
  ];
  els.metricsGrid.innerHTML = items.map(([label, value]) => `
    <article class="metric-card">
      <span>${label}</span>
      <strong>${value}</strong>
    </article>
  `).join("");
}

function renderEvents(items) {
  els.eventsTable.innerHTML = items.map((item) => `
    <tr>
      <td>${fmtTime(item.created_at)}</td>
      <td>${item.event_type}</td>
      <td>${item.actor_name || "-"}</td>
      <td>${item.content || "-"}</td>
      <td>${item.live_heat}</td>
    </tr>
  `).join("");
}

function renderCommands(items) {
  els.commandsTable.innerHTML = items.map((item) => `
    <tr>
      <td>${fmtTime(item.created_at)}</td>
      <td>${item.command_type}</td>
      <td>${item.priority_track}</td>
      <td>${item.status}</td>
      <td>${item.error_message || "-"}</td>
    </tr>
  `).join("");
}

function renderSettings(settings) {
  currentSettings = settings;
  els.roomId.value = settings.room_id || "";
  els.stage.value = settings.stage;
  els.robotState.value = settings.robot_state;
  els.currentTopic.value = settings.current_topic;
  els.roomTitle.value = settings.room_title;
  els.xiaozhiBaseUrl.value = settings.xiaozhi_target.base_url;
  els.xiaozhiSecret.value = settings.xiaozhi_target.secret;
  els.deviceId.value = settings.xiaozhi_target.device_id;
  els.agentId.value = settings.xiaozhi_target.agent_id;
  els.macAddress.value = settings.xiaozhi_target.mac_address;
  els.blocked.value = String(settings.blocked);
}

async function loadSettings() {
  const res = await fetch("/api/settings");
  const data = await res.json();
  renderSettings(data);
}

async function loadDashboard() {
  const res = await fetch("/api/dashboard");
  const data = await res.json();
  els.healthStatus.textContent = `在线 · ${data.heat_bucket}`;
  renderMetrics(data);
  renderEvents(data.recent_events || []);
  renderCommands(data.recent_commands || []);
}

async function saveSettings() {
  if (!currentSettings) return;
  const payload = structuredClone(currentSettings);
  payload.room_id = els.roomId.value;
  payload.stage = els.stage.value;
  payload.robot_state = els.robotState.value;
  payload.current_topic = els.currentTopic.value;
  payload.room_title = els.roomTitle.value;
  payload.blocked = els.blocked.value === "true";
  payload.xiaozhi_target.base_url = els.xiaozhiBaseUrl.value;
  payload.xiaozhi_target.secret = els.xiaozhiSecret.value;
  payload.xiaozhi_target.device_id = els.deviceId.value;
  payload.xiaozhi_target.agent_id = els.agentId.value;
  payload.xiaozhi_target.mac_address = els.macAddress.value;
  const res = await fetch("/api/settings", {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  const data = await res.json();
  renderSettings(data);
  await loadDashboard();
}

async function sendManual() {
  const text = els.manualText.value.trim();
  if (!text) return;
  await fetch("/api/commands/manual", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ text, command_type: "CUSTOM_SCRIPT", priority: "EMERGENCY", interrupt: true }),
  });
  els.manualText.value = "";
  await loadDashboard();
}

els.saveSettingsBtn.addEventListener("click", saveSettings);
els.sendManualBtn.addEventListener("click", sendManual);

async function boot() {
  await loadSettings();
  await loadDashboard();
  window.setInterval(loadDashboard, 5000);
}

boot();