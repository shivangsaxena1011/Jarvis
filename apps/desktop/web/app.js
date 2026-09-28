/**
 * SHIVANI Desktop Assistant Controller (Phase 14)
 * Coordinates WebSocket events, REST endpoints, View navigation,
 * Floating HUD, Spotlight Command Bar, Approvals, and Multi-surface controls.
 */

// ==============================================================================
// DOM ELEMENT REFERENCES
// ==============================================================================

const appBody = document.getElementById('appBody');
const floatingHud = document.getElementById('floatingHud');
const hudDragHandle = document.getElementById('hudDragHandle');
const hudOrb = document.getElementById('hudOrb');
const hudStatus = document.getElementById('hudStatus');
const hudMicBtn = document.getElementById('hudMicBtn');
const hudCommandBtn = document.getElementById('hudCommandBtn');
const hudStopBtn = document.getElementById('hudStopBtn');
const hudExpandBtn = document.getElementById('hudExpandBtn');

const commandModal = document.getElementById('commandModal');
const commandBarInput = document.getElementById('commandBarInput');
const cmdMicBtn = document.getElementById('cmdMicBtn');
const cmdScreenToggle = document.getElementById('cmdScreenToggle');
const cmdSendBtn = document.getElementById('cmdSendBtn');
const commandSuggestions = document.getElementById('commandSuggestions');

const lockOverlay = document.getElementById('lockOverlay');
const pinInput = document.getElementById('pinInput');
const unlockBtn = document.getElementById('unlockBtn');
const unlockError = document.getElementById('unlockError');

const assistantStateBadge = document.getElementById('assistantStateBadge');
const statePulseDot = document.getElementById('statePulseDot');
const assistantStateLabel = document.getElementById('assistantStateLabel');
const assistantSubStepLabel = document.getElementById('assistantSubStepLabel');

const quickVoiceBtn = document.getElementById('quickVoiceBtn');
const privacyModeBtn = document.getElementById('privacyModeBtn');
const privacyBtnLabel = document.getElementById('privacyBtnLabel');
const lockAssistantBtn = document.getElementById('lockAssistantBtn');
const emergencyStopNavBtn = document.getElementById('emergencyStopNavBtn');
const themeSelect = document.getElementById('themeSelect');

const wsIndicator = document.getElementById('wsIndicator');
const wsStatusText = document.getElementById('wsStatusText');
const tasksBadge = document.getElementById('tasksBadge');
const approvalsBadge = document.getElementById('approvalsBadge');
const notifBadge = document.getElementById('notifBadge');

const chatStream = document.getElementById('chatStream');
const chatForm = document.getElementById('chatForm');
const chatInput = document.getElementById('chatInput');
const chatMicBtn = document.getElementById('chatMicBtn');
const screenContextToggle = document.getElementById('screenContextToggle');

const footToolCount = document.getElementById('footToolCount');
const footHealthStatus = document.getElementById('footHealthStatus');
const footActiveAgent = document.getElementById('footActiveAgent');
const footPrivacyStatus = document.getElementById('footPrivacyStatus');

// State variables
let ws = null;
let currentTaskId = null;
let isPrivacyMode = false;
let isLocked = false;
let currentScreenIncluded = false;
let isRecording = false;
let mediaRecorder = null;
let audioChunks = [];


// ==============================================================================
// INITIALIZATION & WEBSOCKET
// ==============================================================================

document.addEventListener('DOMContentLoaded', () => {
  setupNavigation();
  setupGlobalHotkeys();
  setupHUDDragging();
  setupTheme();
  setupVoiceInteraction();
  connectWebSocket();
  fetchInitialData();
});

function connectWebSocket() {
  const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
  const wsUrl = `${protocol}//${window.location.host}/ws/events`;

  ws = new WebSocket(wsUrl);

  ws.onopen = () => {
    wsIndicator.className = 'status-dot green';
    wsStatusText.textContent = 'Connected';
  };

  ws.onclose = () => {
    wsIndicator.className = 'status-dot amber';
    wsStatusText.textContent = 'Reconnecting...';
    setTimeout(connectWebSocket, 3000);
  };

  ws.onmessage = (event) => {
    try {
      const payload = JSON.parse(event.data);
      handleServerEvent(payload);
    } catch (err) {
      console.error('Error parsing WS event', err);
    }
  };
}

function handleServerEvent(event) {
  const et = event.event;
  const data = event.data || {};
  const state = event.assistant_state;

  if (state) {
    updateAssistantState(state, data.step || data.action || data.tool);
  }

  if (event.privacy_mode !== undefined) {
    updatePrivacyModeUI(event.privacy_mode);
  }

  if (event.locked !== undefined && event.locked) {
    showLockOverlay();
  }

  if (et === 'SNAPSHOT') {
    footToolCount.textContent = event.tools_count || 163;
    tasksBadge.textContent = event.tasks_count || 0;
  } else if (et === 'TASK_CREATED' || et === 'TASK_PLANNED') {
    appendTaskMessage(event.task_id, data.task || { user_request: 'New Task' });
    refreshTasksList();
  } else if (et === 'TOOL_STARTED') {
    const toolMsg = `Executing tool: ${data.tool || 'Action'}`;
    assistantSubStepLabel.textContent = toolMsg;
    footActiveAgent.textContent = data.agent || 'Computer Agent';
  } else if (et === 'TASK_WAITING_APPROVAL') {
    checkPendingApprovals();
  } else if (et === 'TASK_COMPLETED') {
    appendAssistantMessage(`Task completed: ${data.result || 'Success'}`);
    refreshTasksList();
    refreshArtifactsList();
  } else if (et === 'TASK_FAILED') {
    appendAssistantMessage(`⚠️ Task failed: ${data.error || 'Execution encountered an error'}`);
    refreshTasksList();
  } else if (et === 'TASK_CANCELLED') {
    appendAssistantMessage(`Task was stopped.`);
    refreshTasksList();
  }
}


// ==============================================================================
// STATE VISUALIZATION
// ==============================================================================

function updateAssistantState(state, subStep = '') {
  hudStatus.textContent = state;
  assistantStateLabel.textContent = state;
  assistantSubStepLabel.textContent = subStep;

  let color = '#3b82f6';
  if (state === 'IDLE') color = '#10b981';
  else if (state === 'LISTENING') color = '#38bdf8';
  else if (state === 'PLANNING' || state === 'UNDERSTANDING') color = '#8b5cf6';
  else if (state === 'WAITING_FOR_PERMISSION') color = '#f59e0b';
  else if (state === 'EXECUTING') color = '#3b82f6';
  else if (state === 'VERIFYING') color = '#06b6d4';
  else if (state === 'COMPLETED') color = '#10b981';
  else if (state === 'FAILED' || state === 'CANCELLED') color = '#ef4444';
  else if (state === 'LOCKED') color = '#94a3b8';

  statePulseDot.style.background = color;
  hudOrb.style.boxShadow = `0 0 10px ${color}`;
}

function updatePrivacyModeUI(enabled) {
  isPrivacyMode = enabled;
  if (enabled) {
    privacyModeBtn.classList.add('active');
    privacyBtnLabel.textContent = 'Privacy ON';
    footPrivacyStatus.textContent = 'Restricted';
    footPrivacyStatus.style.color = 'var(--color-warning)';
  } else {
    privacyModeBtn.classList.remove('active');
    privacyBtnLabel.textContent = 'Privacy';
    footPrivacyStatus.textContent = 'Standard';
    footPrivacyStatus.style.color = 'inherit';
  }
}


// ==============================================================================
// NAVIGATION & TABS
// ==============================================================================

function setupNavigation() {
  const navButtons = document.querySelectorAll('.nav-item');
  navButtons.forEach(btn => {
    btn.addEventListener('click', () => {
      const viewName = btn.getAttribute('data-view');
      switchView(viewName);
    });
  });
}

function switchView(viewName) {
  document.querySelectorAll('.nav-item').forEach(b => b.classList.remove('active'));
  document.querySelectorAll('.view-panel').forEach(p => p.classList.remove('active'));

  const activeBtn = document.querySelector(`.nav-item[data-view="${viewName}"]`);
  const activePanel = document.getElementById(`view-${viewName}`);

  if (activeBtn) activeBtn.classList.add('active');
  if (activePanel) activePanel.classList.add('active');

  // Trigger data refreshes on view activation
  if (viewName === 'tasks') refreshTasksList();
  else if (viewName === 'approvals') checkPendingApprovals();
  else if (viewName === 'memory') refreshMemoryView();
  else if (viewName === 'skills') refreshSkillsView();
  else if (viewName === 'devices') refreshDevicesView();
  else if (viewName === 'connectors') refreshConnectorsView();
  else if (viewName === 'artifacts') refreshArtifactsList();
  else if (viewName === 'notifications') refreshNotificationsView();
  else if (viewName === 'security') refreshSecurityView();
  else if (viewName === 'settings') refreshSettingsView();
  else if (viewName === 'automations') { loadAutomations(); loadAutomationAnalytics(); }
  else if (viewName === 'productivity') { loadProductivityDashboard(); loadProductivityTasks(); }
}


// ==============================================================================
// CONVERSATION & CHAT FORM
// ==============================================================================

chatForm.addEventListener('submit', async (e) => {
  e.preventDefault();
  const text = chatInput.value.trim();
  if (!text) return;

  appendUserMessage(text);
  chatInput.value = '';

  try {
    const res = await fetch('/api/conversation/message', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        message: text,
        include_screen: currentScreenIncluded,
      }),
    });
    const data = await res.json();
    if (res.ok) {
      currentTaskId = data.task_id;
      appendAssistantMessage(data.reply);
    } else {
      appendAssistantMessage(`⚠️ Error: ${data.detail || 'Could not submit task'}`);
    }
  } catch (err) {
    appendAssistantMessage(`⚠️ Network error: ${err.message}`);
  }
});

function appendUserMessage(text) {
  const msg = document.createElement('div');
  msg.className = 'chat-msg user';
  msg.innerHTML = `
    <div class="msg-avatar">👤</div>
    <div class="msg-bubble"><p>${escapeHtml(text)}</p></div>
  `;
  chatStream.appendChild(msg);
  chatStream.scrollTop = chatStream.scrollHeight;
}

function appendAssistantMessage(text) {
  const msg = document.createElement('div');
  msg.className = 'chat-msg assistant';
  msg.innerHTML = `
    <div class="msg-avatar">✦</div>
    <div class="msg-bubble"><p>${escapeHtml(text)}</p></div>
  `;
  chatStream.appendChild(msg);
  chatStream.scrollTop = chatStream.scrollHeight;
}

function appendTaskMessage(taskId, task) {
  const msg = document.createElement('div');
  msg.className = 'chat-msg assistant';
  msg.innerHTML = `
    <div class="msg-avatar">✦</div>
    <div class="msg-bubble">
      <p><strong>Starting Task:</strong> ${escapeHtml(task.user_request || '')}</p>
      <div class="task-progress" style="margin: 8px 0;"><div class="progress-fill" style="width: 25%;"></div></div>
      <button class="chat-chip" onclick="inspectTask('${taskId}')">View Execution Details</button>
    </div>
  `;
  chatStream.appendChild(msg);
  chatStream.scrollTop = chatStream.scrollHeight;
}

window.handleChipClick = function(text) {
  chatInput.value = text;
  chatForm.dispatchEvent(new Event('submit'));
};

window.inspectTask = function(taskId) {
  switchView('tasks');
  loadTaskTimeline(taskId);
};


// ==============================================================================
// GLOBAL COMMAND BAR & HOTKEYS
// ==============================================================================

function setupGlobalHotkeys() {
  window.addEventListener('keydown', (e) => {
    // Ctrl + Space -> Spotlight Command Bar
    if (e.ctrlKey && e.code === 'Space' && !e.shiftKey) {
      e.preventDefault();
      toggleCommandBar();
    }
    // Ctrl + Shift + X -> Emergency Stop
    else if (e.ctrlKey && e.shiftKey && e.code === 'KeyX') {
      e.preventDefault();
      triggerEmergencyStop();
    }
    // Escape -> Close Command Bar or Modals
    else if (e.code === 'Escape') {
      closeCommandBar();
      closeArtifactModal();
    }
  });

  hudCommandBtn.addEventListener('click', toggleCommandBar);
  hudStopBtn.addEventListener('click', triggerEmergencyStop);
  emergencyStopNavBtn.addEventListener('click', triggerEmergencyStop);

  cmdSendBtn.addEventListener('click', () => {
    const query = commandBarInput.value.trim();
    if (!query) return;
    executeCommandBarQuery(query);
  });

  commandBarInput.addEventListener('keydown', (e) => {
    if (e.key === 'Enter') {
      const query = commandBarInput.value.trim();
      if (query) executeCommandBarQuery(query);
    }
  });

  cmdScreenToggle.addEventListener('click', () => {
    currentScreenIncluded = !currentScreenIncluded;
    cmdScreenToggle.classList.toggle('active-toggle', currentScreenIncluded);
  });

  screenContextToggle.addEventListener('click', () => {
    currentScreenIncluded = !currentScreenIncluded;
    screenContextToggle.classList.toggle('active', currentScreenIncluded);
  });

  // Suggestion chips in command bar
  document.querySelectorAll('.suggestion-chip').forEach(chip => {
    chip.addEventListener('click', () => {
      commandBarInput.value = chip.textContent;
      executeCommandBarQuery(chip.textContent);
    });
  });
}

function toggleCommandBar() {
  commandModal.classList.toggle('hidden');
  if (!commandModal.classList.contains('hidden')) {
    commandBarInput.focus();
  }
}

function closeCommandBar() {
  commandModal.classList.add('hidden');
}

async function executeCommandBarQuery(query) {
  closeCommandBar();
  appendUserMessage(query);
  switchView('conversation');

  try {
    const res = await fetch('/api/tasks', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        query: query,
        screen_context: currentScreenIncluded,
      }),
    });
    const data = await res.json();
    if (res.ok) {
      currentTaskId = data.id;
      appendTaskMessage(data.id, data);
    } else {
      appendAssistantMessage(`⚠️ Error: ${data.detail || 'Could not start task'}`);
    }
  } catch (err) {
    appendAssistantMessage(`⚠️ Network error: ${err.message}`);
  }
}


// ==============================================================================
// FLOATING HUD DRAGGING
// ==============================================================================

function setupHUDDragging() {
  let isDragging = false;
  let startX, startY, initX, initY;

  hudDragHandle.addEventListener('mousedown', (e) => {
    isDragging = true;
    startX = e.clientX;
    startY = e.clientY;
    initX = floatingHud.offsetLeft;
    initY = floatingHud.offsetTop;
    document.addEventListener('mousemove', onMouseMove);
    document.addEventListener('mouseup', onMouseUp);
  });

  function onMouseMove(e) {
    if (!isDragging) return;
    const dx = e.clientX - startX;
    const dy = e.clientY - startY;
    floatingHud.style.left = `${Math.max(10, Math.min(window.innerWidth - 200, initX + dx))}px`;
    floatingHud.style.top = `${Math.max(10, Math.min(window.innerHeight - 80, initY + dy))}px`;
    floatingHud.style.right = 'auto';
  }

  function onMouseUp() {
    isDragging = false;
    document.removeEventListener('mousemove', onMouseMove);
    document.removeEventListener('mouseup', onMouseUp);
  }

  hudExpandBtn.addEventListener('click', () => {
    switchView('conversation');
    window.focus();
  });
}


// ==============================================================================
// VOICE COMMAND & AUDIO INTERACTION
// ==============================================================================

let isVoiceListening = false;
let activeRecognition = null;
let activeMediaStream = null;
let activeMediaRecorder = null;
let activeAudioChunks = [];

function setupVoiceInteraction() {
  const micButtons = [chatMicBtn, quickVoiceBtn, cmdMicBtn, hudMicBtn];

  micButtons.forEach((btn) => {
    if (!btn) return;
    btn.addEventListener('click', (e) => {
      e.preventDefault();
      e.stopPropagation();
      handleMicButtonClick(btn);
    });
  });
}

async function handleMicButtonClick(sourceBtn) {
  if (isPrivacyMode) {
    appendAssistantMessage('🛡️ Voice interaction blocked: Privacy Mode is ON. Please disable Privacy Mode to use voice commands.');
    return;
  }
  if (isLocked) {
    appendAssistantMessage('🔒 Voice interaction blocked: Assistant is locked. Please enter your PIN to unlock.');
    showLockOverlay();
    return;
  }

  if (isVoiceListening) {
    stopVoiceListening();
  } else {
    await startVoiceListening(sourceBtn);
  }
}

async function startVoiceListening(sourceBtn) {
  isVoiceListening = true;
  setMicButtonsRecording(true);
  updateAssistantState('LISTENING', 'Listening to voice...');

  // Ensure conversation view is visible for chat or quickVoice buttons
  if (sourceBtn === quickVoiceBtn || sourceBtn === hudMicBtn) {
    switchView('conversation');
  }

  // Notify server of listening state
  fetch('/api/state/control', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ action: 'listen' }),
  }).catch(() => {});

  const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;

  if (SpeechRecognition) {
    try {
      const recognition = new SpeechRecognition();
      recognition.continuous = false;
      recognition.interimResults = true;
      recognition.lang = navigator.language || 'en-US';

      let finalTranscript = '';

      recognition.onresult = (event) => {
        let interim = '';
        for (let i = event.resultIndex; i < event.results.length; ++i) {
          if (event.results[i].isFinal) {
            finalTranscript += event.results[i][0].transcript;
          } else {
            interim += event.results[i][0].transcript;
          }
        }
        const text = (finalTranscript || interim).trim();
        if (text) {
          if (sourceBtn === cmdMicBtn || !commandModal.classList.contains('hidden')) {
            commandBarInput.value = text;
          } else {
            chatInput.value = text;
          }
        }
      };

      recognition.onerror = (event) => {
        console.warn('SpeechRecognition error:', event.error);
        if (event.error === 'not-allowed') {
          appendAssistantMessage('⚠️ Microphone access was denied. Please allow microphone permission in your browser address bar.');
        } else if (event.error !== 'no-speech') {
          appendAssistantMessage(`⚠️ Voice recognition issue: ${event.error}`);
        }
        stopVoiceListening();
      };

      recognition.onend = () => {
        const text = (finalTranscript || chatInput.value || commandBarInput.value).trim();
        stopVoiceListening();

        if (text) {
          if (sourceBtn === cmdMicBtn || !commandModal.classList.contains('hidden')) {
            executeCommandBarQuery(text);
          } else {
            chatInput.value = text;
            chatForm.dispatchEvent(new Event('submit'));
          }
        }
      };

      activeRecognition = recognition;
      recognition.start();
      return;
    } catch (err) {
      console.warn('SpeechRecognition failed to start, falling back to MediaRecorder:', err);
    }
  }

  // Fallback: MediaRecorder stream to /api/voice/interact
  startMediaRecorderFallback(sourceBtn);
}

function startMediaRecorderFallback(sourceBtn) {
  if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
    appendAssistantMessage('⚠️ Audio input is not supported in this browser environment.');
    stopVoiceListening();
    return;
  }

  navigator.mediaDevices.getUserMedia({ audio: true })
    .then((stream) => {
      activeMediaStream = stream;
      const recorder = new MediaRecorder(stream);
      activeAudioChunks = [];

      recorder.ondataavailable = (e) => {
        if (e.data.size > 0) activeAudioChunks.push(e.data);
      };

      recorder.onstop = async () => {
        stream.getTracks().forEach((track) => track.stop());
        activeMediaStream = null;

        const audioBlob = new Blob(activeAudioChunks, { type: 'audio/wav' });
        if (audioBlob.size > 200) {
          appendAssistantMessage('🎙️ Processing spoken instruction...');
          updateAssistantState('UNDERSTANDING', 'Transcribing audio...');

          try {
            const res = await fetch('/api/voice/interact', {
              method: 'POST',
              body: audioBlob,
            });
            const data = await res.json();
            if (res.ok) {
              if (data.transcript) appendUserMessage(data.transcript);
              if (data.reply) appendAssistantMessage(data.reply);
              if (data.audio_url) {
                const audio = new Audio(data.audio_url);
                audio.play().catch((e) => console.log('Audio playback prevented:', e));
              }
            } else {
              appendAssistantMessage(`⚠️ Voice interaction error: ${data.detail || 'Could not process audio'}`);
            }
          } catch (err) {
            appendAssistantMessage(`⚠️ Network error processing voice: ${err.message}`);
          } finally {
            updateAssistantState('IDLE');
          }
        }
      };

      recorder.start();
      activeMediaRecorder = recorder;
    })
    .catch((err) => {
      console.error('Microphone access failed:', err);
      appendAssistantMessage('⚠️ Microphone access denied. Please click the camera/mic icon in your browser address bar to allow microphone access.');
      stopVoiceListening();
    });
}

function stopVoiceListening() {
  isVoiceListening = false;
  setMicButtonsRecording(false);

  if (activeRecognition) {
    try {
      activeRecognition.stop();
    } catch (e) {}
    activeRecognition = null;
  }

  if (activeMediaRecorder && activeMediaRecorder.state !== 'inactive') {
    try {
      activeMediaRecorder.stop();
    } catch (e) {}
    activeMediaRecorder = null;
  }

  if (activeMediaStream) {
    activeMediaStream.getTracks().forEach((track) => track.stop());
    activeMediaStream = null;
  }

  fetch('/api/state/control', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ action: 'stop_speaking' }),
  }).catch(() => {});

  updateAssistantState('IDLE');
}

function setMicButtonsRecording(recording) {
  const micButtons = [chatMicBtn, quickVoiceBtn, cmdMicBtn, hudMicBtn];
  micButtons.forEach((btn) => {
    if (!btn) return;
    if (recording) {
      btn.classList.add('recording');
      btn.setAttribute('title', 'Listening... Click to stop');
    } else {
      btn.classList.remove('recording');
      btn.setAttribute('title', 'Click to speak');
    }
  });
}


// ==============================================================================
// EMERGENCY STOP & PRIVACY & LOCK
// ==============================================================================

async function triggerEmergencyStop() {
  try {
    const res = await fetch('/api/stop', { method: 'POST' });
    const data = await res.json();
    appendAssistantMessage(`⏹️ Emergency Stop activated: Stopped ${data.tasks_cancelled} active tasks.`);
    updateAssistantState('CANCELLED');
  } catch (err) {
    console.error('Failed to trigger emergency stop', err);
  }
}

privacyModeBtn.addEventListener('click', async () => {
  try {
    const res = await fetch('/api/state/control', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ action: 'privacy_toggle' }),
    });
    const data = await res.json();
    updatePrivacyModeUI(data.privacy_mode);
  } catch (err) {
    console.error('Error toggling privacy mode', err);
  }
});

lockAssistantBtn.addEventListener('click', async () => {
  try {
    await fetch('/api/state/control', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ action: 'lock' }),
    });
    showLockOverlay();
  } catch (err) {
    console.error('Error locking assistant', err);
  }
});

function showLockOverlay() {
  isLocked = true;
  lockOverlay.classList.remove('hidden');
  pinInput.value = '';
  pinInput.focus();
}

unlockBtn.addEventListener('click', async () => {
  const pin = pinInput.value.trim();
  try {
    const res = await fetch('/api/state/control', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ action: 'unlock', pin: pin }),
    });
    if (res.ok) {
      lockOverlay.classList.add('hidden');
      unlockError.classList.add('hidden');
      isLocked = false;
      updateAssistantState('IDLE');
    } else {
      unlockError.classList.remove('hidden');
    }
  } catch (err) {
    unlockError.classList.remove('hidden');
  }
});


// ==============================================================================
// LIVE TASKS & TIMELINE VIEW
// ==============================================================================

async function refreshTasksList() {
  const container = document.getElementById('taskCardsContainer');
  try {
    const res = await fetch('/api/tasks?limit=15');
    const tasks = await res.json();
    if (!tasks || tasks.length === 0) {
      container.innerHTML = '<div class="empty-state">No tasks recorded.</div>';
      tasksBadge.textContent = '0';
      return;
    }
    tasksBadge.textContent = tasks.length;
    container.innerHTML = tasks.map(t => `
      <div class="task-card ${t.id === currentTaskId ? 'active' : ''}" onclick="loadTaskTimeline('${t.id}')">
        <div class="task-card-header">
          <span class="task-card-query">${escapeHtml(t.user_request || '')}</span>
          <span class="status-badge ${t.status.toLowerCase()}">${t.status}</span>
        </div>
        <div class="task-progress">
          <div class="progress-fill" style="width: ${t.status === 'COMPLETED' ? '100%' : '50%'}"></div>
        </div>
      </div>
    `).join('');
  } catch (err) {
    container.innerHTML = `<div class="empty-state">Error loading tasks: ${err.message}</div>`;
  }
}

async function loadTaskTimeline(taskId) {
  currentTaskId = taskId;
  const box = document.getElementById('taskTimelineBox');
  try {
    const res = await fetch(`/api/tasks/${taskId}/timeline`);
    if (!res.ok) throw new Error('Task timeline not found');
    const data = await res.json();

    let stepsHtml = '';
    if (data.steps && data.steps.length > 0) {
      stepsHtml = data.steps.map(s => `
        <div class="timeline-step-row">
          <div class="step-indicator ${s.status === 'COMPLETED' ? 'done' : 'active'}">${s.step_index}</div>
          <div class="step-detail">
            <strong>${escapeHtml(s.description)}</strong>
            <span class="pill-tag">${escapeHtml(s.tool || '')}</span>
          </div>
        </div>
      `).join('');
    } else {
      stepsHtml = '<div class="empty-state">No steps defined yet.</div>';
    }

    box.innerHTML = `
      <div class="timeline-header">
        <h4>Task: ${escapeHtml(data.query)}</h4>
        <span class="status-badge ${data.status.toLowerCase()}">${data.status}</span>
      </div>
      <div class="steps-flow" style="margin-top: 12px;">${stepsHtml}</div>
      <div class="timeline-actions" style="margin-top: 16px;">
        <button class="btn-secondary" onclick="cancelCurrentTask('${taskId}')">Stop Task</button>
      </div>
    `;
  } catch (err) {
    box.innerHTML = `<div class="empty-state">Error loading timeline: ${err.message}</div>`;
  }
}

window.cancelCurrentTask = async function(taskId) {
  try {
    await fetch(`/api/tasks/${taskId}/cancel`, { method: 'POST' });
    loadTaskTimeline(taskId);
    refreshTasksList();
  } catch (err) {
    console.error('Error cancelling task', err);
  }
};

document.getElementById('refreshTasksBtn').addEventListener('click', refreshTasksList);


// ==============================================================================
// APPROVALS
// ==============================================================================

async function checkPendingApprovals() {
  const grid = document.getElementById('approvalsCardsGrid');
  try {
    const res = await fetch('/api/approvals');
    const approvals = await res.json();
    if (!approvals || approvals.length === 0) {
      grid.innerHTML = '<div class="empty-state">No pending approval requests.</div>';
      approvalsBadge.classList.add('hidden');
      document.getElementById('pendingApprovalsCount').textContent = '0 Pending';
      return;
    }
    approvalsBadge.textContent = approvals.length;
    approvalsBadge.classList.remove('hidden');
    document.getElementById('pendingApprovalsCount').textContent = `${approvals.length} Pending`;

    grid.innerHTML = approvals.map(a => `
      <div class="approval-card-item">
        <div class="approval-top">
          <h4>${escapeHtml(a.tool_name)}: ${escapeHtml(a.action_summary || 'Authorization Required')}</h4>
          <span class="risk-tag ${a.risk_level.toLowerCase()}">${a.risk_level}</span>
        </div>
        <p><strong>Parameters:</strong> <code>${escapeHtml(JSON.stringify(a.parameters || {}))}</code></p>
        <div class="approval-actions-row">
          <button class="btn-approve" onclick="resolveApproval('${a.id}', true)">Approve Once</button>
          <button class="btn-reject" onclick="resolveApproval('${a.id}', false)">Reject</button>
        </div>
      </div>
    `).join('');
  } catch (err) {
    grid.innerHTML = `<div class="empty-state">Error checking approvals: ${err.message}</div>`;
  }
}

window.resolveApproval = async function(reqId, approved) {
  try {
    await fetch(`/api/approvals/${reqId}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ approved, resolved_by: 'user' }),
    });
    checkPendingApprovals();
  } catch (err) {
    console.error('Error resolving approval', err);
  }
};


// ==============================================================================
// KNOWLEDGE OS VIEW
// ==============================================================================

document.getElementById('searchKnowledgeBtn').addEventListener('click', searchKnowledge);
document.getElementById('knowledgeSearchInput').addEventListener('keydown', (e) => {
  if (e.key === 'Enter') searchKnowledge();
});

async function searchKnowledge() {
  const query = document.getElementById('knowledgeSearchInput').value.trim();
  const resultsContainer = document.getElementById('knowledgeResults');
  if (!query) return;

  resultsContainer.innerHTML = '<div class="empty-state">Searching knowledge base...</div>';
  try {
    const res = await fetch(`/api/knowledge/search?q=${encodeURIComponent(query)}`);
    const results = await res.json();
    if (!results || results.length === 0) {
      resultsContainer.innerHTML = '<div class="empty-state">No matching documents or code found.</div>';
      return;
    }
    resultsContainer.innerHTML = results.map(r => `
      <div class="grid-card">
        <h4>${escapeHtml(r.title || r.path || 'Item')}</h4>
        <p>${escapeHtml((r.snippet || r.content || '').substring(0, 160))}...</p>
        <div class="grid-card-footer">
          <span>Score: ${r.score || 1.0}</span>
          <span class="pill-tag">${escapeHtml(r.category || 'Knowledge')}</span>
        </div>
      </div>
    `).join('');
  } catch (err) {
    resultsContainer.innerHTML = `<div class="empty-state">Error: ${err.message}</div>`;
  }
}

document.getElementById('addNoteForm').addEventListener('submit', async (e) => {
  e.preventDefault();
  const title = document.getElementById('noteTitleInput').value.trim();
  const content = document.getElementById('noteContentInput').value.trim();
  const tagsStr = document.getElementById('noteTagsInput').value.trim();
  const tags = tagsStr ? tagsStr.split(',').map(s => s.trim()) : [];

  try {
    const res = await fetch('/api/knowledge/notes', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ title, content, tags }),
    });
    if (res.ok) {
      alert('Note saved to Knowledge OS successfully!');
      document.getElementById('addNoteForm').reset();
    }
  } catch (err) {
    alert('Failed to save note');
  }
});


// ==============================================================================
// MEMORY VIEW
// ==============================================================================

async function refreshMemoryView() {
  const prefsBox = document.getElementById('preferencesList');
  const factsBox = document.getElementById('factsList');

  try {
    const res = await fetch('/api/memory/preferences');
    const prefs = await res.json();
    const entries = Object.entries(prefs || {});
    if (entries.length === 0) {
      prefsBox.innerHTML = '<div class="empty-state">No explicit preferences recorded.</div>';
    } else {
      prefsBox.innerHTML = entries.map(([k, v]) => `
        <div class="grid-card">
          <h4>${escapeHtml(k)}</h4>
          <p>${escapeHtml(String(v))}</p>
        </div>
      `).join('');
    }

    const factsRes = await fetch('/api/memory/facts');
    const facts = await factsRes.json();
    if (!facts || facts.length === 0) {
      factsBox.innerHTML = '<div class="empty-state">No episodic facts indexed.</div>';
    } else {
      factsBox.innerHTML = facts.map(f => `
        <div class="grid-card">
          <h4>${escapeHtml(f.entity || 'Memory')}</h4>
          <p>${escapeHtml(f.fact || '')}</p>
        </div>
      `).join('');
    }
  } catch (err) {
    prefsBox.innerHTML = `<div class="empty-state">Error: ${err.message}</div>`;
  }
}

document.getElementById('refreshMemoryBtn').addEventListener('click', refreshMemoryView);


// ==============================================================================
// UNIVERSAL SKILLS VIEW
// ==============================================================================

async function refreshSkillsView() {
  const grid = document.getElementById('skillsGrid');
  grid.innerHTML = '<div class="empty-state">Loading skills...</div>';
  try {
    const res = await fetch('/api/skills');
    const skills = await res.json();
    if (!skills || skills.length === 0) {
      grid.innerHTML = '<div class="empty-state">No dynamic skills installed.</div>';
      return;
    }
    grid.innerHTML = skills.map(s => `
      <div class="grid-card">
        <div>
          <h4>${escapeHtml(s.display_name)} (v${s.version})</h4>
          <p>${escapeHtml(s.description)}</p>
          <div style="margin-bottom: 8px;">
            <span class="pill-tag">${escapeHtml(s.category)}</span>
            <span class="status-badge ${s.state === 'ACTIVE' || s.state === 'ENABLED' ? 'completed' : 'failed'}">${s.state}</span>
          </div>
        </div>
        <div class="grid-card-footer">
          ${s.state === 'ACTIVE' || s.state === 'ENABLED' 
            ? `<button class="btn-secondary" onclick="disableSkill('${s.name}')">Disable</button>`
            : `<button class="btn-primary" onclick="enableSkill('${s.name}')">Enable</button>`
          }
        </div>
      </div>
    `).join('');
  } catch (err) {
    grid.innerHTML = `<div class="empty-state">Error: ${err.message}</div>`;
  }
}

window.enableSkill = async function(name) {
  await fetch(`/api/skills/${name}/enable`, { method: 'POST' });
  refreshSkillsView();
};

window.disableSkill = async function(name) {
  await fetch(`/api/skills/${name}/disable`, { method: 'POST' });
  refreshSkillsView();
};

document.getElementById('refreshSkillsBtn').addEventListener('click', refreshSkillsView);


// ==============================================================================
// ANDROID DEVICES VIEW
// ==============================================================================

async function refreshDevicesView() {
  const grid = document.getElementById('devicesGrid');
  try {
    const res = await fetch('/api/devices');
    const devices = await res.json();
    if (!devices || devices.length === 0) {
      grid.innerHTML = '<div class="empty-state">No paired Android devices found.</div>';
      return;
    }
    grid.innerHTML = devices.map(d => `
      <div class="grid-card">
        <div>
          <h4>📱 ${escapeHtml(d.device_name || d.device_id)}</h4>
          <p>Status: <strong>${escapeHtml(d.connection_status || 'Connected')}</strong></p>
          <p>Battery: <strong>${d.battery_level || 88}%</strong></p>
        </div>
        <div class="grid-card-footer">
          <span class="pill-tag">${escapeHtml(d.device_id)}</span>
          <button class="btn-secondary" onclick="disconnectDevice('${d.device_id}')">Disconnect</button>
        </div>
      </div>
    `).join('');
  } catch (err) {
    grid.innerHTML = `<div class="empty-state">Error: ${err.message}</div>`;
  }
}

window.disconnectDevice = async function(id) {
  await fetch(`/api/devices/${id}/disconnect`, { method: 'POST' });
  refreshDevicesView();
};

document.getElementById('refreshDevicesBtn').addEventListener('click', refreshDevicesView);


// ==============================================================================
// CONNECTORS & ACCOUNTS VIEW
// ==============================================================================

async function refreshConnectorsView() {
  const grid = document.getElementById('connectorsGrid');
  try {
    const res = await fetch('/api/connectors');
    const conns = await res.json();
    const accRes = await fetch('/api/accounts');
    const accounts = await accRes.json();

    if (!conns || conns.length === 0) {
      grid.innerHTML = '<div class="empty-state">No connectors configured.</div>';
      return;
    }

    grid.innerHTML = conns.map(c => `
      <div class="grid-card">
        <div>
          <h4>🔗 ${escapeHtml(c.name)} (${escapeHtml(c.provider)})</h4>
          <p>Status: <span class="status-badge ${c.status === 'CONNECTED' ? 'completed' : 'waiting'}">${c.status}</span></p>
          <p>Active Account: <strong>${escapeHtml(c.account || 'None')}</strong></p>
        </div>
        <div class="grid-card-footer">
          <span>Rate Limit: ${c.rate_limit_remaining !== null ? c.rate_limit_remaining : 'Unlimited'}</span>
        </div>
      </div>
    `).join('');
  } catch (err) {
    grid.innerHTML = `<div class="empty-state">Error: ${err.message}</div>`;
  }
}

document.getElementById('refreshConnectorsBtn').addEventListener('click', refreshConnectorsView);


// ==============================================================================
// ARTIFACTS VIEW & MODAL
// ==============================================================================

const artifactModal = document.getElementById('artifactModal');
const artifactModalTitle = document.getElementById('artifactModalTitle');
const artifactModalBody = document.getElementById('artifactModalBody');
const artifactModalClose = document.getElementById('artifactModalClose');

artifactModalClose.addEventListener('click', closeArtifactModal);

function closeArtifactModal() {
  artifactModal.classList.add('hidden');
}

async function refreshArtifactsList() {
  const grid = document.getElementById('artifactsGrid');
  try {
    const res = await fetch('/api/artifacts');
    const arts = await res.json();
    if (!arts || arts.length === 0) {
      grid.innerHTML = '<div class="empty-state">No artifacts generated yet.</div>';
      return;
    }
    grid.innerHTML = arts.map(a => `
      <div class="grid-card" onclick="previewArtifact('${a.id}')">
        <div>
          <h4>📄 ${escapeHtml(a.name || a.id)}</h4>
          <p>${escapeHtml(a.summary || a.description || 'Artifact payload')}</p>
        </div>
        <div class="grid-card-footer">
          <span class="pill-tag">${escapeHtml(a.artifact_type || 'File')}</span>
          <button class="btn-secondary">Preview</button>
        </div>
      </div>
    `).join('');
  } catch (err) {
    grid.innerHTML = `<div class="empty-state">Error: ${err.message}</div>`;
  }
}

window.previewArtifact = async function(id) {
  artifactModal.classList.remove('hidden');
  artifactModalBody.innerHTML = '<div class="empty-state">Loading artifact preview...</div>';
  try {
    const res = await fetch(`/api/artifacts/${id}`);
    const data = await res.json();
    artifactModalTitle.textContent = data.metadata.name || 'Artifact Preview';
    artifactModalBody.innerHTML = `<pre style="white-space: pre-wrap; font-family: var(--font-mono);">${escapeHtml(data.preview || JSON.stringify(data.metadata, null, 2))}</pre>`;
  } catch (err) {
    artifactModalBody.innerHTML = `<div class="empty-state">Error loading preview: ${err.message}</div>`;
  }
};

document.getElementById('refreshArtifactsBtn').addEventListener('click', refreshArtifactsList);


// ==============================================================================
// NOTIFICATIONS VIEW
// ==============================================================================

async function refreshNotificationsView() {
  const list = document.getElementById('notificationsList');
  try {
    const res = await fetch('/api/notifications');
    const notifs = await res.json();
    if (!notifs || notifs.length === 0) {
      list.innerHTML = '<div class="empty-state">No new notifications.</div>';
      notifBadge.textContent = '0';
      return;
    }
    notifBadge.textContent = notifs.length;
    list.innerHTML = notifs.map(n => `
      <div class="grid-card" style="margin-bottom: 8px;">
        <div style="display: flex; justify-content: space-between;">
          <h4>${escapeHtml(n.title)}</h4>
          <button class="btn-tool" onclick="dismissNotif('${n.id}')">✕</button>
        </div>
        <p>${escapeHtml(n.message)}</p>
      </div>
    `).join('');
  } catch (err) {
    list.innerHTML = `<div class="empty-state">Error: ${err.message}</div>`;
  }
}

window.dismissNotif = async function(id) {
  await fetch(`/api/notifications/${id}/dismiss`, { method: 'POST' });
  refreshNotificationsView();
};

document.getElementById('clearNotifsBtn').addEventListener('click', async () => {
  await fetch('/api/notifications/clear', { method: 'POST' });
  refreshNotificationsView();
});


// ==============================================================================
// SECURITY & PRIVACY VIEW
// ==============================================================================

async function refreshSecurityView() {
  const cards = document.getElementById('securityStatusCards');
  const auditBox = document.getElementById('auditLogBox');

  try {
    const res = await fetch('/api/security/status');
    const data = await res.json();

    cards.innerHTML = `
      <div class="grid-card">
        <h4>Permission Policy: <strong>${data.permission_policy}</strong></h4>
        <p>Command Sandbox: <strong>Active (Restricted)</strong></p>
        <p>DPAPI Storage: <strong>Active</strong></p>
        <p>Privacy Mode: <strong>${data.privacy_mode ? 'ENABLED' : 'STANDARD'}</strong></p>
      </div>
    `;

    const logs = data.recent_security_events || [];
    if (logs.length === 0) {
      auditBox.innerHTML = '<div class="empty-state">No security incidents logged.</div>';
    } else {
      auditBox.innerHTML = logs.map(l => `
        <div style="padding: 6px 0; border-bottom: 1px solid var(--border-color); font-family: var(--font-mono); font-size: 0.75rem;">
          [${l.timestamp || 'LOG'}] ${escapeHtml(l.event_type || 'SECURITY')}: ${escapeHtml(JSON.stringify(l.details || {}))}
        </div>
      `).join('');
    }
  } catch (err) {
    cards.innerHTML = `<div class="empty-state">Error: ${err.message}</div>`;
  }
}

document.getElementById('refreshSecurityBtn').addEventListener('click', refreshSecurityView);


// ==============================================================================
// DIAGNOSTICS VIEW
// ==============================================================================

document.getElementById('runQuickDoctorBtn').addEventListener('click', () => runDoctor(false));
document.getElementById('runFullDoctorBtn').addEventListener('click', () => runDoctor(true));

async function runDoctor(full) {
  const box = document.getElementById('diagnosticsResultsBox');
  box.innerHTML = '<div class="empty-state">Running diagnostics checks...</div>';
  try {
    const res = await fetch(`/api/diagnostics/run?full=${full}`);
    const data = await res.json();
    box.innerHTML = `
      <div style="margin-bottom: 12px; font-weight: bold; color: ${data.passed ? 'var(--color-success)' : 'var(--color-danger)'};">
        ${data.passed ? '✓ ALL DIAGNOSTIC CHECKS PASSED' : '⚠️ ATTENTION REQUIRED'}
      </div>
      <div>
        ${data.items.map(i => `
          <div style="padding: 6px 0; border-bottom: 1px solid var(--border-color); display: flex; justify-content: space-between;">
            <span>${escapeHtml(i.name)}: ${escapeHtml(i.message)}</span>
            <span class="status-badge ${i.passed ? 'completed' : 'failed'}">${i.severity}</span>
          </div>
        `).join('')}
      </div>
    `;
  } catch (err) {
    box.innerHTML = `<div class="empty-state">Error: ${err.message}</div>`;
  }
}


// ==============================================================================
// SETTINGS & PERSONA VIEW
// ==============================================================================

async function refreshSettingsView() {
  try {
    const res = await fetch('/api/settings');
    const data = await res.json();
    const p = data.persona || {};
    if (p.language) document.getElementById('settingLang').value = p.language;
    if (p.tone) document.getElementById('settingTone').value = p.tone;
    if (p.response_style) document.getElementById('settingStyle').value = p.response_style;
    if (p.speaking_speed) {
      document.getElementById('settingSpeed').value = p.speaking_speed;
      document.getElementById('speedValueLabel').textContent = `${p.speaking_speed}x`;
    }
  } catch (err) {
    console.error('Error fetching settings', err);
  }
}

document.getElementById('settingSpeed').addEventListener('input', (e) => {
  document.getElementById('speedValueLabel').textContent = `${e.target.value}x`;
});

document.getElementById('settingsForm').addEventListener('submit', async (e) => {
  e.preventDefault();
  const payload = {
    persona: {
      language: document.getElementById('settingLang').value,
      tone: document.getElementById('settingTone').value,
      response_style: document.getElementById('settingStyle').value,
      speaking_speed: parseFloat(document.getElementById('settingSpeed').value),
    }
  };
  try {
    await fetch('/api/settings', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    });
    alert('Settings saved successfully!');
  } catch (err) {
    alert('Failed to save settings');
  }
});


// ==============================================================================
// THEME & UTILITIES
// ==============================================================================

function setupTheme() {
  themeSelect.addEventListener('change', (e) => {
    appBody.className = e.target.value;
    localStorage.setItem('shivani_theme', e.target.value);
  });
  const saved = localStorage.getItem('shivani_theme');
  if (saved) {
    themeSelect.value = saved;
    appBody.className = saved;
  }
}

async function fetchInitialData() {
  try {
    const res = await fetch('/api/status');
    const data = await res.json();
    footToolCount.textContent = data.registered_tools_count;
    updateAssistantState(data.assistant_state || 'IDLE');
    if (data.privacy_mode) updatePrivacyModeUI(true);
    if (data.locked) showLockOverlay();
    checkPendingApprovals();
  } catch (err) {
    console.error('Initial data fetch failed', err);
  }
}

function escapeHtml(str) {
  if (!str) return '';
  return String(str)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#039;');
}


// ==============================================================================
// AUTOMATIONS CENTER (PHASE 15)
// ==============================================================================

async function loadAutomations() {
  const grid = document.getElementById('automationsGrid');
  if (!grid) return;
  try {
    const res = await fetch('/api/automations');
    const automations = await res.json();
    if (!automations || automations.length === 0) {
      grid.innerHTML = '<div class="empty-state">No automations registered. Use the prompt box above or safe templates.</div>';
      return;
    }
    grid.innerHTML = automations.map(a => `
      <div class="card" style="background: var(--bg-secondary); border: 1px solid var(--border-color); border-radius: 8px; padding: 16px; margin-bottom: 12px;">
        <div style="display: flex; justify-content: space-between; align-items: flex-start;">
          <div>
            <span class="badge ${a.enabled ? 'badge-success' : 'badge-warning'}" style="font-size: 11px; padding: 2px 8px; border-radius: 12px; background: ${a.enabled ? 'rgba(16, 185, 129, 0.2)' : 'rgba(245, 158, 11, 0.2)'}; color: ${a.enabled ? '#10b981' : '#f59e0b'};">
              ${a.status} (v${a.version})
            </span>
            <h4 style="margin: 8px 0 4px 0; font-size: 16px; color: var(--text-primary);">${escapeHtml(a.name)}</h4>
            <p style="font-size: 13px; color: var(--text-secondary); margin: 0 0 8px 0;">${escapeHtml(a.description || 'No description')}</p>
          </div>
          <div style="display: flex; gap: 6px;">
            <button class="btn-secondary auto-run-btn" data-id="${a.id}" style="padding: 4px 10px; font-size: 12px;">▶ Run</button>
            ${a.enabled 
              ? `<button class="btn-secondary auto-pause-btn" data-id="${a.id}" style="padding: 4px 10px; font-size: 12px;">⏸ Pause</button>` 
              : `<button class="btn-secondary auto-resume-btn" data-id="${a.id}" style="padding: 4px 10px; font-size: 12px;">▶ Resume</button>`}
            <button class="btn-secondary auto-delete-btn" data-id="${a.id}" style="padding: 4px 10px; font-size: 12px; color: #ef4444;">🗑 Delete</button>
          </div>
        </div>
        <div style="display: flex; gap: 16px; font-size: 12px; color: var(--text-muted); border-top: 1px solid var(--border-color); padding-top: 8px; margin-top: 8px;">
          <span>Trigger: <strong>${a.trigger.type}</strong></span>
          <span>Next Run: <strong>${a.next_run ? new Date(a.next_run).toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'}) : 'N/A'}</strong></span>
          <span>Executions: <strong>${a.run_count}</strong></span>
          <span>Steps: <strong>${a.steps.length}</strong></span>
        </div>
      </div>
    `).join('');

    // Wire action buttons
    grid.querySelectorAll('.auto-run-btn').forEach(btn => {
      btn.addEventListener('click', async () => {
        const id = btn.getAttribute('data-id');
        btn.textContent = 'Running...';
        await fetch(`/api/automations/${id}/run`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ dry_run: false }) });
        alert('Automation dispatched!');
        loadAutomations();
        loadAutomationAnalytics();
      });
    });

    grid.querySelectorAll('.auto-pause-btn').forEach(btn => {
      btn.addEventListener('click', async () => {
        const id = btn.getAttribute('data-id');
        await fetch(`/api/automations/${id}/pause`, { method: 'POST' });
        loadAutomations();
        loadAutomationAnalytics();
      });
    });

    grid.querySelectorAll('.auto-resume-btn').forEach(btn => {
      btn.addEventListener('click', async () => {
        const id = btn.getAttribute('data-id');
        await fetch(`/api/automations/${id}/resume`, { method: 'POST' });
        loadAutomations();
        loadAutomationAnalytics();
      });
    });

    grid.querySelectorAll('.auto-delete-btn').forEach(btn => {
      btn.addEventListener('click', async () => {
        if (!confirm('Are you sure you want to delete this automation?')) return;
        const id = btn.getAttribute('data-id');
        await fetch(`/api/automations/${id}`, { method: 'DELETE' });
        loadAutomations();
        loadAutomationAnalytics();
      });
    });

  } catch (err) {
    grid.innerHTML = '<div class="empty-state">Failed to load automations.</div>';
  }
}

async function loadAutomationTemplates() {
  const grid = document.getElementById('templatesGrid');
  if (!grid) return;
  try {
    const res = await fetch('/api/automations/templates');
    const templates = await res.json();
    grid.innerHTML = templates.map(t => `
      <div class="card" style="background: var(--bg-secondary); border: 1px solid var(--border-color); border-radius: 8px; padding: 16px; margin-bottom: 12px;">
        <h4 style="margin: 0 0 6px 0; font-size: 15px; color: var(--accent-cyan);">${escapeHtml(t.name)}</h4>
        <p style="font-size: 13px; color: var(--text-secondary); margin: 0 0 10px 0;">${escapeHtml(t.description)}</p>
        <div style="font-size: 12px; color: var(--text-muted); margin-bottom: 10px;">
          Steps: <strong>${t.steps.map(s => s.name || s.action).join(' → ')}</strong>
        </div>
        <button class="btn-primary auto-use-template-btn" data-id="${t.id}" style="padding: 4px 12px; font-size: 12px;">Use Template</button>
      </div>
    `).join('');

    grid.querySelectorAll('.auto-use-template-btn').forEach(btn => {
      btn.addEventListener('click', async () => {
        const id = btn.getAttribute('data-id');
        const tpl = templates.find(t => t.id === id);
        if (tpl) {
          await fetch('/api/automations', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(tpl) });
          alert(`Template '${tpl.name}' activated!`);
          document.getElementById('subtabActiveBtn').click();
        }
      });
    });
  } catch (err) {
    grid.innerHTML = '<div class="empty-state">Failed to load templates.</div>';
  }
}

async function loadAutomationHistory() {
  const list = document.getElementById('autoHistoryList');
  if (!list) return;
  try {
    const res = await fetch('/api/automations/history');
    const runs = await res.json();
    if (!runs || runs.length === 0) {
      list.innerHTML = '<div class="empty-state">No execution runs recorded yet.</div>';
      return;
    }
    list.innerHTML = runs.map(r => `
      <div style="background: var(--bg-secondary); border: 1px solid var(--border-color); border-radius: 6px; padding: 10px; margin-bottom: 8px;">
        <div style="display: flex; justify-content: space-between; font-size: 13px;">
          <span><strong>${escapeHtml(r.automation_name)}</strong> (Run: ${r.id.slice(0, 8)})</span>
          <span style="color: ${r.status === 'COMPLETED' ? '#10b981' : '#ef4444'}; font-weight: bold;">${r.status}</span>
        </div>
        <div style="font-size: 11px; color: var(--text-muted); margin-top: 4px;">
          Started: ${new Date(r.started_at).toLocaleString()} | Steps: ${r.steps.length}
        </div>
        ${r.errors && r.errors.length > 0 ? `<div style="color: #ef4444; font-size: 11px; margin-top: 4px;">Errors: ${escapeHtml(r.errors.join('; '))}</div>` : ''}
      </div>
    `).join('');
  } catch (err) {
    list.innerHTML = '<div class="empty-state">Failed to load history.</div>';
  }
}

async function loadAutomationAnalytics() {
  try {
    const res = await fetch('/api/automations/analytics');
    const data = await res.json();
    const elActive = document.getElementById('metricActiveAutomations');
    const elSuccess = document.getElementById('metricSuccessRate');
    const elRuns = document.getElementById('metricTotalRuns');
    const elReview = document.getElementById('metricNeedsAttention');
    if (elActive) elActive.textContent = data.active || 0;
    if (elSuccess) elSuccess.textContent = (data.success_rate || 100) + '%';
    if (elRuns) elRuns.textContent = data.total_runs || 0;
    if (elReview) elReview.textContent = data.needs_attention || 0;
  } catch (err) {
    console.error('Analytics load error', err);
  }
}

// Wire Automations UI Buttons
document.getElementById('refreshAutomationsBtn')?.addEventListener('click', () => {
  loadAutomations();
  loadAutomationAnalytics();
});

document.getElementById('submitAutoPromptBtn')?.addEventListener('click', async () => {
  const input = document.getElementById('autoPromptInput');
  const prompt = input?.value.trim();
  if (!prompt) return;
  input.disabled = true;
  try {
    const res = await fetch('/api/automations/create_prompt', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ prompt }),
    });
    const data = await res.json();
    if (data.success) {
      alert(`Automation '${data.automation.name}' created and scheduled!`);
      input.value = '';
      loadAutomations();
      loadAutomationAnalytics();
    }
  } catch (err) {
    alert('Failed to compile automation prompt');
  } finally {
    input.disabled = false;
  }
});

// Subtabs
document.getElementById('subtabActiveBtn')?.addEventListener('click', () => {
  document.getElementById('subtabActiveBtn').classList.add('active');
  document.getElementById('subtabTemplatesBtn').classList.remove('active');
  document.getElementById('subtabHistoryBtn').classList.remove('active');
  document.getElementById('automationsGrid').classList.remove('hidden');
  document.getElementById('templatesGrid').classList.add('hidden');
  document.getElementById('autoHistoryList').classList.add('hidden');
  loadAutomations();
});

document.getElementById('subtabTemplatesBtn')?.addEventListener('click', () => {
  document.getElementById('subtabTemplatesBtn').classList.add('active');
  document.getElementById('subtabActiveBtn').classList.remove('active');
  document.getElementById('subtabHistoryBtn').classList.remove('active');
  document.getElementById('templatesGrid').classList.remove('hidden');
  document.getElementById('automationsGrid').classList.add('hidden');
  document.getElementById('autoHistoryList').classList.add('hidden');
  loadAutomationTemplates();
});

document.getElementById('subtabHistoryBtn')?.addEventListener('click', () => {
  document.getElementById('subtabHistoryBtn').classList.add('active');
  document.getElementById('subtabActiveBtn').classList.remove('active');
  document.getElementById('subtabTemplatesBtn').classList.remove('active');
  document.getElementById('autoHistoryList').classList.remove('hidden');
  document.getElementById('automationsGrid').classList.add('hidden');
  document.getElementById('templatesGrid').classList.add('hidden');
  loadAutomationHistory();
});


// ==============================================================================
// PHASE 16: PRODUCTIVITY OS UI
// ==============================================================================

async function loadProductivityDashboard() {
  try {
    const res = await fetch('/api/productivity/dashboard');
    if (!res.ok) return;
    const data = await res.json();
    const activeTasksEl = document.getElementById('prodMetricActiveTasks');
    const criticalEl = document.getElementById('prodMetricCritical');
    const overdueEl = document.getElementById('prodMetricOverdue');
    const projectsEl = document.getElementById('prodMetricProjects');
    const goalsEl = document.getElementById('prodMetricGoals');

    if (activeTasksEl) activeTasksEl.textContent = data.active_tasks_count || 0;
    if (criticalEl) criticalEl.textContent = data.critical_tasks_count || 0;
    if (overdueEl) overdueEl.textContent = data.overdue_count || 0;
    if (projectsEl) projectsEl.textContent = (data.active_projects || []).length;
    if (goalsEl) goalsEl.textContent = (data.active_goals || []).length;
  } catch (err) {
    console.error('Error loading productivity dashboard', err);
  }
}

async function loadProductivityTasks() {
  const container = document.getElementById('prodTasksContainer');
  if (!container) return;
  try {
    const res = await fetch('/api/tasks');
    if (!res.ok) throw new Error('Failed to fetch tasks');
    const tasks = await res.json();
    if (!tasks || tasks.length === 0) {
      container.innerHTML = '<div class="empty-state">No tasks found. Use the input bar above to create one.</div>';
      return;
    }

    container.innerHTML = tasks.map(t => `
      <div class="card" style="margin-bottom: 8px; display: flex; align-items: center; justify-content: space-between; padding: 12px; background: var(--bg-secondary); border: 1px solid var(--border-color); border-radius: 6px;">
        <div style="flex: 1;">
          <div style="font-weight: 600; color: var(--text-primary);">${escapeHtml(t.title)}</div>
          <div style="font-size: 11px; color: var(--text-secondary); margin-top: 4px;">
            <span class="badge ${t.status === 'COMPLETED' ? 'badge-green' : t.status === 'BLOCKED' ? 'badge-red' : 'badge-cyan'}">${t.status}</span>
            <span style="margin-left: 8px;">Priority: <strong>${t.priority}</strong></span>
            ${t.due_date ? `<span style="margin-left: 8px;">Due: <strong>${t.due_date}</strong></span>` : ''}
          </div>
        </div>
        <div>
          ${t.status !== 'COMPLETED' ? `<button class="btn-primary" style="padding: 4px 10px; font-size: 11px;" onclick="completeTaskUI('${t.id}')">✓ Complete</button>` : ''}
          <button class="btn-danger" style="padding: 4px 8px; font-size: 11px; margin-left: 6px;" onclick="deleteTaskUI('${t.id}')">🗑️</button>
        </div>
      </div>
    `).join('');
  } catch (err) {
    container.innerHTML = `<div class="empty-state error-text">Error loading tasks: ${err.message}</div>`;
  }
}

async function loadProductivityProjects() {
  const container = document.getElementById('prodProjectsContainer');
  if (!container) return;
  try {
    const res = await fetch('/api/projects');
    if (!res.ok) throw new Error('Failed to fetch projects');
    const projects = await res.json();
    if (!projects || projects.length === 0) {
      container.innerHTML = '<div class="empty-state">No projects found.</div>';
      return;
    }

    container.innerHTML = projects.map(p => `
      <div class="card" style="margin-bottom: 10px; padding: 14px; background: var(--bg-secondary); border: 1px solid var(--border-color); border-radius: 6px;">
        <div style="display: flex; justify-content: space-between; align-items: center;">
          <h4 style="margin: 0; font-size: 15px; color: var(--accent-cyan);">${escapeHtml(p.name)}</h4>
          <span class="badge ${p.status === 'ACTIVE' ? 'badge-green' : 'badge-amber'}">${p.status}</span>
        </div>
        <p style="font-size: 12px; color: var(--text-secondary); margin: 6px 0;">${escapeHtml(p.description || 'No description provided.')}</p>
        <div style="display: flex; gap: 8px; margin-top: 8px;">
          <button class="btn-secondary" style="padding: 4px 8px; font-size: 11px;" onclick="showProjectContext('${p.id}')">Continuity Context</button>
        </div>
      </div>
    `).join('');
  } catch (err) {
    container.innerHTML = `<div class="empty-state error-text">Error loading projects: ${err.message}</div>`;
  }
}

async function loadProductivityGoals() {
  const container = document.getElementById('prodGoalsContainer');
  if (!container) return;
  try {
    const res = await fetch('/api/goals');
    if (!res.ok) throw new Error('Failed to fetch goals');
    const goals = await res.json();
    if (!goals || goals.length === 0) {
      container.innerHTML = '<div class="empty-state">No strategic goals created yet.</div>';
      return;
    }

    container.innerHTML = goals.map(g => `
      <div class="card" style="margin-bottom: 10px; padding: 14px; background: var(--bg-secondary); border: 1px solid var(--border-color); border-radius: 6px;">
        <div style="display: flex; justify-content: space-between;">
          <h4 style="margin: 0; font-size: 14px; color: var(--text-primary);">${escapeHtml(g.title)}</h4>
          <span style="font-size: 12px; font-weight: bold; color: var(--accent-purple);">${Math.round((g.progress || 0) * 100)}%</span>
        </div>
        <div style="margin: 8px 0; background: var(--bg-tertiary); border-radius: 4px; height: 6px; overflow: hidden;">
          <div style="width: ${Math.round((g.progress || 0) * 100)}%; background: var(--accent-purple); height: 100%;"></div>
        </div>
        <div style="font-size: 11px; color: var(--text-secondary);">
          <span>Category: ${escapeHtml(g.category)}</span>
          ${g.target_date ? `<span style="margin-left: 12px;">Target: ${g.target_date}</span>` : ''}
        </div>
      </div>
    `).join('');
  } catch (err) {
    container.innerHTML = `<div class="empty-state error-text">Error loading goals: ${err.message}</div>`;
  }
}

async function loadProductivityPlan() {
  const container = document.getElementById('prodPlanContainer');
  if (!container) return;
  try {
    const res = await fetch('/api/planning/daily', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ available_hours: 8.0 }),
    });
    if (!res.ok) throw new Error('Failed to generate daily plan');
    const data = await res.json();
    const plan = data.plan;

    container.innerHTML = `
      <div style="margin-bottom: 12px;">
        <h4 style="margin: 0 0 4px 0;">Schedule for ${plan.date} (${plan.total_planned_minutes}m planned)</h4>
        ${data.warning ? `<div style="color: var(--accent-amber); font-size: 12px; margin-bottom: 8px;">⚠️ ${escapeHtml(data.warning)}</div>` : ''}
      </div>
      <div class="timeline-blocks">
        ${plan.time_blocks.map(b => `
          <div style="display: flex; gap: 12px; padding: 8px; border-bottom: 1px solid var(--border-color); font-size: 12px;">
            <div style="font-weight: bold; width: 100px; color: var(--accent-cyan);">${b.start_time} - ${b.end_time}</div>
            <div style="flex: 1;">
              <strong>${escapeHtml(b.title)}</strong>
              <div style="color: var(--text-secondary); font-size: 11px;">${escapeHtml(b.category)}</div>
            </div>
          </div>
        `).join('')}
      </div>
    `;
  } catch (err) {
    container.innerHTML = `<div class="empty-state error-text">Error: ${err.message}</div>`;
  }
}

async function completeTaskUI(taskId) {
  try {
    const res = await fetch(`/api/tasks/${taskId}/complete`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ notes: 'Completed from Web UI' }),
    });
    if (res.ok) {
      loadProductivityTasks();
      loadProductivityDashboard();
    } else {
      const err = await res.json();
      alert(`Could not complete task: ${err.detail || 'Failed'}`);
    }
  } catch (err) {
    alert('Network error completing task');
  }
}

async function deleteTaskUI(taskId) {
  if (!confirm('Are you sure you want to delete this task?')) return;
  try {
    const res = await fetch(`/api/tasks/${taskId}`, { method: 'DELETE' });
    if (res.ok) {
      loadProductivityTasks();
      loadProductivityDashboard();
    }
  } catch (err) {
    alert('Error deleting task');
  }
}

async function showProjectContext(projectId) {
  try {
    const res = await fetch(`/api/projects/${projectId}/context`);
    if (!res.ok) return;
    const ctx = await res.json();
    alert(`PROJECT CONTEXT: ${ctx.project_name}\nActive Milestone: ${ctx.active_milestone}\nOpen Tasks: ${ctx.open_tasks_count}\nBlockers: ${ctx.blocked_tasks_count}`);
  } catch (err) {
    alert('Error loading project context');
  }
}

// Subtab buttons
document.getElementById('subtabTasksBtn')?.addEventListener('click', () => {
  document.getElementById('subtabTasksBtn').classList.add('active');
  document.getElementById('subtabProjectsBtn').classList.remove('active');
  document.getElementById('subtabGoalsBtn').classList.remove('active');
  document.getElementById('subtabDayPlanBtn').classList.remove('active');
  document.getElementById('prodTasksContainer').classList.remove('hidden');
  document.getElementById('prodProjectsContainer').classList.add('hidden');
  document.getElementById('prodGoalsContainer').classList.add('hidden');
  document.getElementById('prodPlanContainer').classList.add('hidden');
  loadProductivityTasks();
});

document.getElementById('subtabProjectsBtn')?.addEventListener('click', () => {
  document.getElementById('subtabProjectsBtn').classList.add('active');
  document.getElementById('subtabTasksBtn').classList.remove('active');
  document.getElementById('subtabGoalsBtn').classList.remove('active');
  document.getElementById('subtabDayPlanBtn').classList.remove('active');
  document.getElementById('prodProjectsContainer').classList.remove('hidden');
  document.getElementById('prodTasksContainer').classList.add('hidden');
  document.getElementById('prodGoalsContainer').classList.add('hidden');
  document.getElementById('prodPlanContainer').classList.add('hidden');
  loadProductivityProjects();
});

document.getElementById('subtabGoalsBtn')?.addEventListener('click', () => {
  document.getElementById('subtabGoalsBtn').classList.add('active');
  document.getElementById('subtabTasksBtn').classList.remove('active');
  document.getElementById('subtabProjectsBtn').classList.remove('active');
  document.getElementById('subtabDayPlanBtn').classList.remove('active');
  document.getElementById('prodGoalsContainer').classList.remove('hidden');
  document.getElementById('prodTasksContainer').classList.add('hidden');
  document.getElementById('prodProjectsContainer').classList.add('hidden');
  document.getElementById('prodPlanContainer').classList.add('hidden');
  loadProductivityGoals();
});

document.getElementById('subtabDayPlanBtn')?.addEventListener('click', () => {
  document.getElementById('subtabDayPlanBtn').classList.add('active');
  document.getElementById('subtabTasksBtn').classList.remove('active');
  document.getElementById('subtabProjectsBtn').classList.remove('active');
  document.getElementById('subtabGoalsBtn').classList.remove('active');
  document.getElementById('prodPlanContainer').classList.remove('hidden');
  document.getElementById('prodTasksContainer').classList.add('hidden');
  document.getElementById('prodProjectsContainer').classList.add('hidden');
  document.getElementById('prodGoalsContainer').classList.add('hidden');
  loadProductivityPlan();
});

document.getElementById('refreshProductivityBtn')?.addEventListener('click', () => {
  loadProductivityDashboard();
  loadProductivityTasks();
});

document.getElementById('prodAddTaskBtn')?.addEventListener('click', async () => {
  const input = document.getElementById('prodTaskInput');
  const title = input.value.trim();
  if (!title) return;
  try {
    const res = await fetch('/api/tasks', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ title: title }),
    });
    if (res.ok) {
      input.value = '';
      loadProductivityTasks();
      loadProductivityDashboard();
    }
  } catch (err) {
    alert('Error creating task');
  }
});

document.getElementById('prodPlanDayBtn')?.addEventListener('click', () => {
  document.getElementById('subtabDayPlanBtn').click();
});

