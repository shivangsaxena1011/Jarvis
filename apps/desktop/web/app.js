// SHIVANI Desktop Dashboard Controller

const stateBadge = document.getElementById('systemStateBadge');
const stateText = document.getElementById('agentStateText');
const wsStatus = document.getElementById('wsStatus');
const commandForm = document.getElementById('commandForm');
const commandInput = document.getElementById('commandInput');
const sendBtn = document.getElementById('sendBtn');
const emergencyStopBtn = document.getElementById('emergencyStopBtn');
const startListeningBtn = document.getElementById('startListeningBtn');
const settingsBtn = document.getElementById('settingsBtn');
const taskHistoryBtn = document.getElementById('taskHistoryBtn');

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
const healthStatus = document.getElementById('healthStatus');
const providerBadge = document.getElementById('providerBadge');
const envName = document.getElementById('envName');

let currentActiveTaskId = null;
let currentPendingApprovalId = null;
let ws = null;
let isListening = false;

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
      handleServerEvent(payload.event, payload.data, payload.task_id);
    } catch (err) {
      console.error('Failed to parse WS message', err);
    }
  };
}

function handleServerEvent(eventType, data, taskId) {
  addTimelineItem(eventType, data);

  if (eventType === 'TASK_CREATED' || eventType === 'TASK_PLANNED') {
    const task = data.task;
    renderActiveTask(task);
  } else if (eventType === 'TASK_STARTED' || eventType === 'TOOL_STARTED') {
    if (data.message) {
      currentStepLabel.textContent = data.message;
    } else if (data.action) {
      currentStepLabel.textContent = `Executing: ${data.action} [${data.tool}]`;
    }
    setAgentState('WORKING...', '#8b5cf6');
  } else if (eventType === 'TASK_VERIFYING') {
    currentStepLabel.textContent = `Verifying environment side-effects...`;
    setAgentState('VERIFYING...', '#06b6d4');
  } else if (eventType === 'TASK_COMPLETED') {
    if (data.result) {
      currentStepLabel.textContent = data.result;
    }
    setAgentState('IDLE / COMPLETED', '#10b981');
    taskProgressBar.style.width = '100%';
    taskProgressBar.style.background = '#10b981';
    currentTaskStateBadge.textContent = 'COMPLETED';
    setTimeout(checkPendingApprovals, 500);
  } else if (eventType === 'TASK_FAILED') {
    currentStepLabel.textContent = `Error: ${data.error || 'Execution failed'}`;
    setAgentState('FAILED', '#ef4444');
    currentTaskStateBadge.textContent = 'FAILED';
  } else if (eventType === 'TASK_CANCELLED') {
    setAgentState('CANCELLED', '#f87171');
    currentStepLabel.textContent = 'Task was cancelled.';
    currentTaskStateBadge.textContent = 'CANCELLED';
  }

  checkPendingApprovals();
}

function addTimelineItem(title, data) {
  const item = document.createElement('div');
  item.className = 'timeline-item';
  const now = new Date().toLocaleTimeString();

  let details = '';
  if (data.task) {
    details = `[${data.task.status || data.task.state}] ${data.task.user_request || data.task.user_query}`;
  } else if (data.message) {
    details = data.message;
  } else if (data.action) {
    details = `${data.action} (${data.tool})`;
  } else if (data.result) {
    details = data.result;
  } else {
    details = JSON.stringify(data);
  }

  item.innerHTML = `
    <div class="timeline-time">${now} • ${title}</div>
    <div class="timeline-content">${escapeHtml(details)}</div>
  `;

  timelineList.prepend(item);
}

function renderActiveTask(task) {
  if (!task) return;

  currentActiveTaskId = task.id;
  noActiveTaskMsg.classList.add('hidden');
  taskDetailsContent.classList.remove('hidden');

  currentTaskQuery.textContent = task.user_request || task.user_query;
  const status = task.status || task.state || 'PLANNING';
  currentTaskStateBadge.textContent = status;

  const stateColors = {
    'PLANNING': { text: 'THINKING...', color: '#38bdf8', pct: 25 },
    'WAITING_FOR_PERMISSION': { text: 'WAITING FOR APPROVAL', color: '#f59e0b', pct: 40 },
    'EXECUTING': { text: 'WORKING...', color: '#8b5cf6', pct: 60 },
    'VERIFYING': { text: 'VERIFYING...', color: '#06b6d4', pct: 85 },
    'COMPLETED': { text: 'IDLE', color: '#10b981', pct: 100 },
    'FAILED': { text: 'FAILED', color: '#ef4444', pct: 100 },
    'CANCELLED': { text: 'CANCELLED', color: '#f87171', pct: 100 },
  };

  const meta = stateColors[status] || { text: status, color: '#94a3b8', pct: 10 };
  setAgentState(meta.text, meta.color);
  taskProgressBar.style.width = `${meta.pct}%`;
  taskProgressBar.style.background = meta.color;
}

function setAgentState(text, color) {
  stateText.textContent = text;
  stateBadge.style.color = color;
  stateBadge.style.borderColor = color;
}

// Fetch Initial Status & Health
async function loadStatus() {
  try {
    const res = await fetch('/status');
    const data = await res.json();
    toolCount.textContent = data.registered_tools_count;
    providerBadge.textContent = `${data.llm_provider.toUpperCase()} (${data.llm_model})`;
    envName.textContent = data.environment;

    const healthRes = await fetch('/health');
    const healthData = await healthRes.json();
    healthStatus.textContent = healthData.status.toUpperCase();
    healthStatus.style.color = healthData.status === 'healthy' ? '#10b981' : '#f59e0b';
  } catch (err) {
    console.error('Failed to load status', err);
  }
}

// Check Pending Approvals
async function checkPendingApprovals() {
  try {
    const res = await fetch('/approvals');
    const approvals = await res.json();

    if (approvals.length > 0) {
      const req = approvals[0];
      currentPendingApprovalId = req.id;
      approvalDesc.textContent = `${req.description} [${req.tool_name}]`;
      approvalTargetText.textContent = req.target || 'System';
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

// Submit Task Form
commandForm.addEventListener('submit', async (e) => {
  e.preventDefault();
  const instruction = commandInput.value.trim();
  if (!instruction) return;

  commandInput.value = '';
  sendBtn.disabled = true;
  setAgentState('THINKING...', '#38bdf8');

  try {
    const res = await fetch('/tasks', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ user_request: instruction })
    });
    const task = await res.json();
    renderActiveTask(task);
  } catch (err) {
    alert('Failed to submit task: ' + err.message);
  } finally {
    sendBtn.disabled = false;
  }
});

// Approve & Reject Actions
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
    await fetch(`/approvals/${requestId}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ approved, resolved_by: 'dashboard' })
    });
    approvalCard.classList.add('hidden');
  } catch (err) {
    alert('Failed to resolve approval: ' + err.message);
  }
}

// Voice & Push-to-Talk (PTT) Audio Recorder
let mediaRecorder = null;
let audioChunks = [];
let activePlaybackAudio = null;

async function startRecording() {
  try {
    const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
    audioChunks = [];
    mediaRecorder = new MediaRecorder(stream);

    mediaRecorder.ondataavailable = (e) => {
      if (e.data.size > 0) {
        audioChunks.push(e.data);
      }
    };

    mediaRecorder.onstop = async () => {
      const audioBlob = new Blob(audioChunks, { type: 'audio/webm' });
      stream.getTracks().forEach(track => track.stop());
      await sendVoiceAudio(audioBlob);
    };

    mediaRecorder.start();
    isListening = true;
    startListeningBtn.classList.add('listening-active');
    startListeningBtn.innerHTML = `● Listening... (Click to Send)`;
    setAgentState('LISTENING', '#38bdf8');
  } catch (err) {
    console.error('Microphone access denied or unavailable', err);
    alert('Microphone access unavailable or blocked: ' + err.message);
    isListening = false;
    setAgentState('IDLE', '#10b981');
  }
}

function stopRecording() {
  if (mediaRecorder && mediaRecorder.state !== 'inactive') {
    mediaRecorder.stop();
  }
  isListening = false;
  startListeningBtn.classList.remove('listening-active');
  startListeningBtn.innerHTML = `Start Listening`;
}

async function sendVoiceAudio(blob) {
  setAgentState('PROCESSING...', '#8b5cf6');
  currentStepLabel.textContent = 'Transcribing speech & analyzing intent...';

  try {
    const res = await fetch('/api/voice/interact', {
      method: 'POST',
      headers: { 'Content-Type': 'audio/webm' },
      body: blob
    });
    const result = await res.json();

    if (result.transcribed_text) {
      addTimelineItem('VOICE INPUT', { message: `Transcribed: "${result.transcribed_text}" (${result.language})` });
    }

    if (result.task) {
      renderActiveTask(result.task);
    }

    // Play TTS audio response if provided
    if (result.tts && result.tts.audio_path) {
      const filename = result.tts.audio_path.split(/[\\/]/).pop();
      playVoiceResponse(`/api/voice/audio/${filename}`);
    } else {
      setAgentState('IDLE', '#10b981');
    }
  } catch (err) {
    console.error('Voice interaction error', err);
    setAgentState('ERROR', '#ef4444');
    currentStepLabel.textContent = 'Voice processing error: ' + err.message;
  }
}

function playVoiceResponse(audioUrl) {
  if (activePlaybackAudio) {
    activePlaybackAudio.pause();
  }
  setAgentState('SPEAKING', '#06b6d4');
  activePlaybackAudio = new Audio(audioUrl);
  activePlaybackAudio.onended = () => {
    setAgentState('IDLE', '#10b981');
  };
  activePlaybackAudio.onerror = () => {
    setAgentState('IDLE', '#10b981');
  };
  activePlaybackAudio.play().catch(e => console.log('Autoplay restriction:', e));
}

// Stop Button (Aborts Task + Interrupts Speech)
emergencyStopBtn.addEventListener('click', async () => {
  if (activePlaybackAudio) {
    activePlaybackAudio.pause();
    activePlaybackAudio = null;
  }
  if (isListening) {
    stopRecording();
  }
  try {
    await fetch('/api/voice/stop', { method: 'POST' });
    await fetch('/stop', { method: 'POST' });
  } catch (err) {
    console.error('Failed to trigger stop', err);
  }
});

// Start Listening / Push-To-Talk Button Toggle
startListeningBtn.addEventListener('click', () => {
  if (!isListening) {
    startRecording();
  } else {
    stopRecording();
  }
});


// Settings Button
settingsBtn.addEventListener('click', () => {
  alert('SHIVANI Settings:\n\nProvider: ' + providerBadge.textContent + '\nSecurity Policy: STRICT\nWake Word: "Shivani"\nAPI Port: 8000');
});

// Task History Button
taskHistoryBtn.addEventListener('click', async () => {
  try {
    const res = await fetch('/tasks');
    const tasks = await res.json();
    const summary = tasks.map(t => `• [${t.status}] ${t.user_request}`).join('\n') || 'No tasks yet.';
    alert('Task History:\n\n' + summary);
  } catch (err) {
    alert('Failed to fetch history: ' + err.message);
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

// Initialization
connectWebSocket();
loadStatus();
checkPendingApprovals();
setInterval(checkPendingApprovals, 2000);
