// SHIVANI Desktop Dashboard Controller

const stateBadge = document.getElementById('systemStateBadge');
const stateText = document.getElementById('agentStateText');
const wsStatus = document.getElementById('wsStatus');
const commandForm = document.getElementById('commandForm');
const commandInput = document.getElementById('commandInput');
const sendBtn = document.getElementById('sendBtn');
const emergencyStopBtn = document.getElementById('emergencyStopBtn');

const noActiveTaskMsg = document.getElementById('noActiveTaskMsg');
const taskDetailsContent = document.getElementById('taskDetailsContent');
const currentTaskQuery = document.getElementById('currentTaskQuery');
const currentTaskStateBadge = document.getElementById('currentTaskStateBadge');
const taskProgressBar = document.getElementById('taskProgressBar');
const currentStepLabel = document.getElementById('currentStepLabel');

const approvalCard = document.getElementById('approvalCard');
const approvalDesc = document.getElementById('approvalDesc');
const approvalTargetText = document.getElementById('approvalTargetText');
const approvalRisk = document.getElementById('approvalRisk');
const approveBtn = document.getElementById('approveBtn');
const rejectBtn = document.getElementById('rejectBtn');

const timelineList = document.getElementById('timelineList');
const toolCount = document.getElementById('toolCount');
const providerBadge = document.getElementById('providerBadge');
const envName = document.getElementById('envName');

let currentActiveTaskId = null;
let currentPendingApprovalId = null;
let ws = null;

// Initialize WebSocket
function connectWebSocket() {
  const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
  const wsUrl = `${protocol}//${window.location.host}/ws/events`;

  ws = new WebSocket(wsUrl);

  ws.onopen = () => {
    wsStatus.textContent = '● Connected';
    wsStatus.style.color = '#10b981';
  };

  ws.onclose = () => {
    wsStatus.textContent = '○ Reconnecting...';
    wsStatus.style.color = '#f59e0b';
    setTimeout(connectWebSocket, 3000);
  };

  ws.onmessage = (event) => {
    try {
      const payload = JSON.parse(event.data);
      handleServerEvent(payload.event, payload.data);
    } catch (err) {
      console.error('Failed to parse WS message', err);
    }
  };
}

function handleServerEvent(eventType, data) {
  addTimelineItem(eventType, data);

  if (eventType === 'task_created' || eventType === 'task_updated') {
    const task = data.task;
    renderActiveTask(task);
  } else if (eventType === 'step_progress') {
    currentStepLabel.textContent = data.message;
  } else if (eventType === 'task_completed') {
    const task = data.task;
    renderActiveTask(task);
    setTimeout(() => {
      checkPendingApprovals();
    }, 500);
  } else if (eventType === 'emergency_stop') {
    setAgentState('CANCELLED / STOPPED', '#ef4444');
    currentStepLabel.textContent = `Emergency stop aborted ${data.cancelled_count} task(s).`;
  }

  checkPendingApprovals();
}

function addTimelineItem(title, data) {
  const item = document.createElement('div');
  item.className = 'timeline-item';
  const now = new Date().toLocaleTimeString();

  let details = '';
  if (data.task) {
    details = `[${data.task.state}] ${data.task.user_query}`;
  } else if (data.message) {
    details = data.message;
  } else {
    details = JSON.stringify(data);
  }

  item.innerHTML = `
    <div class="timeline-time">${now} • ${title.toUpperCase()}</div>
    <div class="timeline-content">${escapeHtml(details)}</div>
  `;

  timelineList.prepend(item);
}

function renderActiveTask(task) {
  if (!task) return;

  currentActiveTaskId = task.id;
  noActiveTaskMsg.classList.add('hidden');
  taskDetailsContent.classList.remove('hidden');

  currentTaskQuery.textContent = task.user_query;
  currentTaskStateBadge.textContent = task.state;

  // State color mapping
  const stateColors = {
    'PLANNING': { text: 'THINKING...', color: '#38bdf8', pct: 25 },
    'WAITING_FOR_PERMISSION': { text: 'WAITING APPROVAL', color: '#f59e0b', pct: 40 },
    'EXECUTING': { text: 'WORKING...', color: '#8b5cf6', pct: 60 },
    'VERIFYING': { text: 'VERIFYING...', color: '#06b6d4', pct: 85 },
    'COMPLETED': { text: 'COMPLETED', color: '#10b981', pct: 100 },
    'FAILED': { text: 'FAILED', color: '#ef4444', pct: 100 },
    'CANCELLED': { text: 'CANCELLED', color: '#f87171', pct: 100 },
  };

  const meta = stateColors[task.state] || { text: task.state, color: '#94a3b8', pct: 10 };
  setAgentState(meta.text, meta.color);
  taskProgressBar.style.width = `${meta.pct}%`;
  taskProgressBar.style.background = meta.color;

  if (task.state === 'COMPLETED') {
    currentStepLabel.textContent = task.final_output || 'Task verified and completed.';
  } else if (task.state === 'FAILED') {
    currentStepLabel.textContent = `Error: ${task.error || 'Execution failed'}`;
  }
}

function setAgentState(text, color) {
  stateText.textContent = text;
  stateBadge.style.color = color;
  stateBadge.style.borderColor = color;
}

// Fetch Initial Status
async function loadStatus() {
  try {
    const res = await fetch('/api/status');
    const data = await res.json();
    toolCount.textContent = data.registered_tools_count;
    providerBadge.textContent = `${data.llm_provider.toUpperCase()} (${data.llm_model})`;
    envName.textContent = data.environment;
  } catch (err) {
    console.error('Failed to load status', err);
  }
}

// Check Pending Approvals
async function checkPendingApprovals() {
  try {
    const res = await fetch('/api/approvals');
    const approvals = await res.json();

    if (approvals.length > 0) {
      const req = approvals[0];
      currentPendingApprovalId = req.id;
      approvalDesc.textContent = `${req.description} [${req.tool_name}]`;
      approvalTargetText.textContent = req.target || 'System/Process';
      approvalRisk.textContent = req.risk_level;
      approvalCard.classList.remove('hidden');
      setAgentState('WAITING FOR PERMISSION', '#f59e0b');
    } else {
      currentPendingApprovalId = null;
      approvalCard.classList.add('hidden');
    }
  } catch (err) {
    console.error('Failed to check approvals', err);
  }
}

// Submit Task via form
commandForm.addEventListener('submit', async (e) => {
  e.preventDefault();
  const query = commandInput.value.trim();
  if (!query) return;

  commandInput.value = '';
  sendBtn.disabled = true;
  setAgentState('THINKING...', '#38bdf8');

  try {
    const res = await fetch('/api/tasks', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ query })
    });
    const task = await res.json();
    renderActiveTask(task);
  } catch (err) {
    alert('Failed to submit task: ' + err.message);
  } finally {
    sendBtn.disabled = false;
  }
});

// Approve & Reject Buttons
approveBtn.addEventListener('click', async () => {
  if (!currentPendingApprovalId) return;
  await resolveApproval(currentPendingApprovalId, true);
});

rejectBtn.addEventListener('click', async () => {
  if (!currentPendingApprovalId) return;
  await resolveApproval(currentPendingApprovalId, false);
});

async function resolveApproval(requestId, approved) {
  try {
    await fetch(`/api/approvals/${requestId}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ approved, resolved_by: 'web_dashboard' })
    });
    approvalCard.classList.add('hidden');
  } catch (err) {
    alert('Failed to resolve approval: ' + err.message);
  }
}

// Emergency Stop Button
emergencyStopBtn.addEventListener('click', async () => {
  try {
    await fetch('/api/stop', { method: 'POST' });
  } catch (err) {
    console.error('Failed to trigger stop', err);
  }
});

function escapeHtml(str) {
  return String(str).replace(/[&<>"']/g, (m) => ({
    '&': '&amp;',
    '<': '&lt;',
    '>': '&gt;',
    '"': '&quot;',
    "'": '&#39;'
  })[m]);
}

// Start
connectWebSocket();
loadStatus();
checkPendingApprovals();
setInterval(checkPendingApprovals, 2000);
