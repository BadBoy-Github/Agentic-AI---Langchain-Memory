/**
 * Gemini ReAct Agentic AI - Clean & Modern Frontend Controller
 */

// State
let currentSessionId = localStorage.getItem("gemini_react_session") || "session_" + Math.random().toString(36).substring(2, 8);
let isProcessing = false;
let sessionTurnCount = 0;

// DOM Elements
const chatMessagesEl = document.getElementById("chat-messages");
const chatFormEl = document.getElementById("chat-form");
const userInputEl = document.getElementById("user-input");
const btnSendEl = document.getElementById("btn-send");
const btnNewSessionEl = document.getElementById("btn-new-session");
const btnClearMemoryEl = document.getElementById("btn-clear-current-memory");
const btnExportChatEl = document.getElementById("btn-export-chat");
const activeSessionTitleEl = document.getElementById("active-session-title");
const activeTurnsBadgeEl = document.getElementById("active-turns-badge");
const sessionListEl = document.getElementById("session-list");
const welcomeHeroEl = document.getElementById("welcome-hero");
const headerModelNameEl = document.getElementById("header-model-name");

// Mobile & Sidebar elements
const sidebarEl = document.getElementById("sidebar");
const sidebarOverlayEl = document.getElementById("sidebar-overlay");
const btnToggleSidebarEl = document.getElementById("btn-toggle-sidebar");
const btnCloseSidebarEl = document.getElementById("btn-close-sidebar");

// Configure Markdown Parser
marked.setOptions({
  breaks: true,
  gfm: true,
  highlight: function (code, lang) {
    if (lang && hljs.getLanguage(lang)) {
      try {
        return hljs.highlight(code, { language: lang }).value;
      } catch (e) {}
    }
    return hljs.highlightAuto(code).value;
  }
});

// Initialize on DOM load
document.addEventListener("DOMContentLoaded", () => {
  setupEventListeners();
  loadServerStatus();
  switchSession(currentSessionId);
  adjustTextareaHeight();
});

function setupEventListeners() {
  // Chat form submit
  chatFormEl.addEventListener("submit", (e) => {
    e.preventDefault();
    handleSendMessage();
  });

  // Enter to send, Shift+Enter for newline
  userInputEl.addEventListener("keydown", (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  });

  // Global Ctrl+K / Cmd+K shortcut for New Chat
  document.addEventListener("keydown", (e) => {
    if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === "k") {
      e.preventDefault();
      createNewSession();
    }
  });

  userInputEl.addEventListener("input", adjustTextareaHeight);

  // New Chat buttons
  btnNewSessionEl.addEventListener("click", createNewSession);

  // Clear memory
  btnClearMemoryEl.addEventListener("click", async () => {
    if (confirm("Reset conversation memory for this chat?")) {
      try {
        await fetch("/api/sessions/clear", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ session_id: currentSessionId })
        });
        chatMessagesEl.innerHTML = "";
        if (welcomeHeroEl) chatMessagesEl.appendChild(welcomeHeroEl);
        sessionTurnCount = 0;
        updateTurnsBadge(0);
      } catch (err) {
        console.error("Failed to clear memory:", err);
      }
    }
  });

  // Quick Prompt buttons
  document.querySelectorAll(".quick-prompt").forEach(btn => {
    btn.addEventListener("click", () => {
      const span = btn.querySelector("span:last-child");
      const text = span ? span.innerText.trim() : btn.innerText.trim();
      userInputEl.value = text;
      adjustTextareaHeight();
      handleSendMessage();
    });
  });

  // Copy chat transcript
  btnExportChatEl.addEventListener("click", () => {
    const text = chatMessagesEl.innerText;
    navigator.clipboard.writeText(text).then(() => {
      btnExportChatEl.innerHTML = '<i class="fa-solid fa-check text-emerald-400"></i>';
      setTimeout(() => {
        btnExportChatEl.innerHTML = '<i class="fa-regular fa-copy"></i>';
      }, 1500);
    });
  });

  // Sidebar toggles
  if (btnToggleSidebarEl) {
    btnToggleSidebarEl.addEventListener("click", () => {
      sidebarEl.classList.toggle("-translate-x-full");
      sidebarOverlayEl.classList.toggle("hidden");
    });
  }

  if (btnCloseSidebarEl) {
    btnCloseSidebarEl.addEventListener("click", () => {
      sidebarEl.classList.add("-translate-x-full");
      sidebarOverlayEl.classList.add("hidden");
    });
  }

  if (sidebarOverlayEl) {
    sidebarOverlayEl.addEventListener("click", () => {
      sidebarEl.classList.add("-translate-x-full");
      sidebarOverlayEl.classList.add("hidden");
    });
  }
}

function createNewSession() {
  const newId = "session_" + Math.random().toString(36).substring(2, 8);
  switchSession(newId);
  if (window.innerWidth < 768) {
    sidebarEl.classList.add("-translate-x-full");
    sidebarOverlayEl.classList.add("hidden");
  }
}

function adjustTextareaHeight() {
  userInputEl.style.height = "auto";
  userInputEl.style.height = Math.min(userInputEl.scrollHeight, 140) + "px";
}

async function loadServerStatus() {
  try {
    const res = await fetch("/api/status");
    const data = await res.json();
    if (data.model) headerModelNameEl.innerText = data.model;
  } catch (err) {
    console.error("Failed to load server status:", err);
  }
}

async function switchSession(sessionId) {
  currentSessionId = sessionId;
  localStorage.setItem("gemini_react_session", sessionId);
  activeSessionTitleEl.innerText = sessionId;

  chatMessagesEl.innerHTML = "";
  renderSessionList();

  try {
    const res = await fetch(`/api/history/${sessionId}`);
    const data = await res.json();
    const messages = data.messages || [];
    sessionTurnCount = messages.length;
    updateTurnsBadge(sessionTurnCount);

    if (messages.length === 0) {
      if (welcomeHeroEl) chatMessagesEl.appendChild(welcomeHeroEl);
    } else {
      messages.forEach(msg => {
        if (msg.role === "human" || msg.role === "user") {
          appendUserMessage(msg.content);
        } else if (msg.role === "ai" && msg.content) {
          appendSavedAgentMessage(msg.content);
        }
      });
      scrollToBottom();
    }
  } catch (err) {
    console.error("History fetch error:", err);
    if (welcomeHeroEl) chatMessagesEl.appendChild(welcomeHeroEl);
  }
}

function updateTurnsBadge(count) {
  activeTurnsBadgeEl.innerText = `${count} msg${count === 1 ? '' : 's'}`;
}

function renderSessionList() {
  let sessions = JSON.parse(localStorage.getItem("gemini_sessions_list") || "[]");
  if (!sessions.includes(currentSessionId)) {
    sessions.unshift(currentSessionId);
    if (sessions.length > 10) sessions.pop();
    localStorage.setItem("gemini_sessions_list", JSON.stringify(sessions));
  }

  sessionListEl.innerHTML = "";
  sessions.forEach(sid => {
    const isActive = sid === currentSessionId;
    const item = document.createElement("div");
    item.className = `group flex items-center justify-between px-2.5 py-1.5 rounded-lg text-xs transition cursor-pointer ${
      isActive
        ? "bg-zinc-800 text-white font-medium"
        : "text-zinc-400 hover:bg-zinc-800/50 hover:text-zinc-200"
    }`;
    item.innerHTML = `
      <span class="truncate flex items-center gap-2">
        <i class="fa-regular fa-message text-[10px] ${isActive ? "text-indigo-400" : "text-zinc-500"}"></i>
        <span class="truncate">${sid}</span>
      </span>
      <button class="btn-del-session opacity-0 group-hover:opacity-100 hover:text-rose-400 text-zinc-500 p-0.5 transition" title="Delete">
        <i class="fa-solid fa-xmark text-[10px]"></i>
      </button>
    `;

    item.addEventListener("click", (e) => {
      if (e.target.closest(".btn-del-session")) return;
      switchSession(sid);
      if (window.innerWidth < 768) {
        sidebarEl.classList.add("-translate-x-full");
        sidebarOverlayEl.classList.add("hidden");
      }
    });

    const delBtn = item.querySelector(".btn-del-session");
    delBtn.addEventListener("click", (e) => {
      e.stopPropagation();
      let list = JSON.parse(localStorage.getItem("gemini_sessions_list") || "[]");
      list = list.filter(s => s !== sid);
      localStorage.setItem("gemini_sessions_list", JSON.stringify(list));
      if (sid === currentSessionId) {
        createNewSession();
      } else {
        renderSessionList();
      }
    });

    sessionListEl.appendChild(item);
  });
}

// User Message Bubble
function appendUserMessage(text) {
  const wrapper = document.createElement("div");
  wrapper.className = "flex justify-end max-w-2xl mx-auto message-animate";
  wrapper.innerHTML = `
    <div class="bg-zinc-800 text-zinc-100 px-4 py-2.5 rounded-2xl rounded-tr-sm text-sm leading-relaxed max-w-[85%] whitespace-pre-wrap break-words border border-zinc-700/40">
      ${escapeHtml(text)}
    </div>
  `;
  chatMessagesEl.appendChild(wrapper);
  scrollToBottom();
}

// Saved Agent Message (from history)
function appendSavedAgentMessage(content) {
  const wrapper = document.createElement("div");
  wrapper.className = "max-w-2xl mx-auto flex gap-3 text-sm message-animate";
  wrapper.innerHTML = `
    <div class="w-6 h-6 rounded-md bg-indigo-600/30 text-indigo-400 border border-indigo-500/20 flex items-center justify-center shrink-0 text-xs mt-0.5">
      <i class="fa-solid fa-sparkles text-[10px]"></i>
    </div>
    <div class="flex-1 min-w-0 markdown-body">
      ${marked.parse(content)}
    </div>
  `;
  wrapper.querySelectorAll("pre code").forEach(block => hljs.highlightElement(block));
  chatMessagesEl.appendChild(wrapper);
}

// Live Chat Turn Handling
async function handleSendMessage() {
  const query = userInputEl.value.trim();
  if (!query || isProcessing) return;

  const hero = document.getElementById("welcome-hero");
  if (hero) hero.remove();

  appendUserMessage(query);
  userInputEl.value = "";
  adjustTextareaHeight();

  isProcessing = true;
  btnSendEl.disabled = true;

  // Create clean agent turn container
  const agentWrapper = document.createElement("div");
  agentWrapper.className = "max-w-2xl mx-auto flex gap-3 text-sm message-animate w-full";
  agentWrapper.innerHTML = `
    <div class="w-6 h-6 rounded-md bg-indigo-600/30 text-indigo-400 border border-indigo-500/20 flex items-center justify-center shrink-0 text-xs mt-0.5">
      <i class="fa-solid fa-sparkles text-[10px]"></i>
    </div>

    <div class="flex-1 min-w-0 space-y-2">
      <!-- Steps Container (clean pills) -->
      <div class="react-pills-container flex flex-wrap gap-1.5 items-center"></div>

      <!-- Thinking indicator -->
      <div class="live-thinking flex items-center gap-2 text-xs text-zinc-500 thinking-pulse py-1">
        <span class="w-1.5 h-1.5 rounded-full bg-indigo-400 animate-ping"></span>
        <span>Thinking & reasoning...</span>
      </div>

      <!-- Answer container -->
      <div class="answer-box markdown-body hidden"></div>
    </div>
  `;
  chatMessagesEl.appendChild(agentWrapper);
  scrollToBottom();

  const pillsContainer = agentWrapper.querySelector(".react-pills-container");
  const liveThinkingEl = agentWrapper.querySelector(".live-thinking");
  const answerBoxEl = agentWrapper.querySelector(".answer-box");

  let activeActions = {};

  try {
    const response = await fetch("/api/chat/stream", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        message: query,
        session_id: currentSessionId
      })
    });

    if (!response.ok) throw new Error(`HTTP ${response.status}`);

    const reader = response.body.getReader();
    const decoder = new TextDecoder();
    let buffer = "";

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;

      buffer += decoder.decode(value, { stream: true });
      const blocks = buffer.split("\n\n");
      buffer = blocks.pop();

      for (const block of blocks) {
        if (!block.trim().startsWith("data: ")) continue;
        const jsonStr = block.trim().substring(6);
        try {
          const data = JSON.parse(jsonStr);

          if (data.type === "action") {
            const toolName = data.tool || "tool";
            const callId = data.id || Math.random().toString();
            
            // Create sleek trace pill
            const pill = document.createElement("details");
            pill.className = "react-trace-pill group";
            pill.innerHTML = `
              <summary class="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-zinc-900 hover:bg-zinc-800 border border-zinc-800 hover:border-zinc-700 cursor-pointer text-[11px] text-zinc-400 select-none transition">
                <span class="text-[10px] text-indigo-400">${getToolIconEmoji(toolName)}</span>
                <span>Used <strong>${escapeHtml(toolName)}</strong></span>
                <i class="fa-solid fa-chevron-down text-[9px] text-zinc-500 group-open:rotate-180 transition-transform ml-1"></i>
              </summary>
              <div class="mt-1.5 p-2 rounded-xl bg-zinc-900 border border-zinc-800 text-[11px] font-mono text-zinc-300 space-y-1">
                <div class="text-zinc-500 text-[10px] uppercase font-semibold">Input:</div>
                <div class="bg-surface-950 p-1.5 rounded overflow-x-auto text-[10px]">${escapeHtml(JSON.stringify(data.args))}</div>
                <div class="obs-container hidden mt-1">
                  <div class="text-zinc-500 text-[10px] uppercase font-semibold">Output:</div>
                  <div class="obs-result bg-surface-950 p-1.5 rounded overflow-x-auto text-[10px] text-zinc-400"></div>
                </div>
              </div>
            `;
            pillsContainer.appendChild(pill);
            activeActions[callId] = pill;
            scrollToBottom();

          } else if (data.type === "observation") {
            const pill = activeActions[data.tool_call_id] || pillsContainer.lastElementChild;
            if (pill) {
              const obsContainer = pill.querySelector(".obs-container");
              const obsResult = pill.querySelector(".obs-result");
              if (obsContainer && obsResult) {
                let text = data.result || "";
                if (text.length > 300) text = text.substring(0, 297) + "...";
                obsResult.innerText = text;
                obsContainer.classList.remove("hidden");
              }
            }
            scrollToBottom();

          } else if (data.type === "answer") {
            liveThinkingEl.classList.add("hidden");
            answerBoxEl.classList.remove("hidden");
            answerBoxEl.innerHTML = marked.parse(data.content);
            answerBoxEl.querySelectorAll("pre code").forEach(b => hljs.highlightElement(b));
            scrollToBottom();

          } else if (data.type === "error") {
            liveThinkingEl.classList.add("hidden");
            answerBoxEl.classList.remove("hidden");
            answerBoxEl.innerHTML = `
              <div class="text-rose-400 text-xs py-1 flex items-center gap-1.5">
                <i class="fa-solid fa-circle-exclamation"></i>
                <span>${escapeHtml(data.message)}</span>
              </div>
            `;
            scrollToBottom();
          }

        } catch (e) {
          console.error("SSE parse error:", e);
        }
      }
    }

    liveThinkingEl.classList.add("hidden");
    sessionTurnCount += 2;
    updateTurnsBadge(sessionTurnCount);

  } catch (err) {
    console.error("Turn error:", err);
    liveThinkingEl.classList.add("hidden");
    answerBoxEl.classList.remove("hidden");
    answerBoxEl.innerHTML = `<span class="text-rose-400 text-xs">Error: ${escapeHtml(err.message)}</span>`;
  } finally {
    isProcessing = false;
    btnSendEl.disabled = false;
    userInputEl.focus();
    scrollToBottom();
  }
}

function getToolIconEmoji(tool) {
  if (tool === "calculator") return "🧮";
  if (tool === "web_search") return "🌐";
  if (tool === "local_date_time") return "🕒";
  return "⚡";
}

function scrollToBottom() {
  chatMessagesEl.scrollTop = chatMessagesEl.scrollHeight;
}

function escapeHtml(text) {
  if (!text) return "";
  return String(text)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#039;");
}
