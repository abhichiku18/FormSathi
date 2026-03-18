const FORM_SATHI_API = "http://127.0.0.1:8000";
const CHAT_STORAGE_KEY = "formsathiChatHistory";
const CHAT_LANGUAGE_KEY = "formsathiChatLanguage";

function createChatbotShell() {
  const shell = document.createElement("div");
  shell.className = "chatbot-shell";
  shell.innerHTML = `
    <div id="chatbotPanel" class="chatbot-panel hidden">
      <div class="chatbot-header">
        <div>
          <p class="eyebrow">Friendly AI Assistant</p>
          <h3 style="margin-bottom: 4px;">Ask FormSathi</h3>
          <p class="chatbot-subtitle">Fast help for forms, schemes, documents, and everyday questions.</p>
        </div>
        <button id="chatbotClose" class="chatbot-close" type="button">x</button>
      </div>
      <div id="chatbotBody" class="chatbot-body"></div>
      <form id="chatbotForm" class="chatbot-form">
        <label class="chatbot-language">
          <span>Reply Language</span>
          <select id="chatbotLanguage">
            <option value="English">English</option>
            <option value="Hindi">Hindi</option>
            <option value="Bengali">Bengali</option>
            <option value="Tamil">Tamil</option>
            <option value="Marathi">Marathi</option>
          </select>
        </label>
        <textarea id="chatbotInput" class="chatbot-input" placeholder="Ask anything. For example: How to apply for driving licence in India?"></textarea>
        <div class="chatbot-actions">
          <button class="primary-button" type="submit">Send</button>
        </div>
      </form>
    </div>
    <button id="chatbotToggle" class="chatbot-toggle" type="button" aria-label="Open chatbot">
      <span class="robot-icon">
        <span class="robot-antenna"></span>
        <span class="robot-head">
          <span class="robot-eyes"></span>
        </span>
      </span>
    </button>
  `;
  document.body.appendChild(shell);
  return shell;
}

function getChatHistory() {
  return JSON.parse(localStorage.getItem(CHAT_STORAGE_KEY) || "[]");
}

function setChatHistory(history) {
  localStorage.setItem(CHAT_STORAGE_KEY, JSON.stringify(history));
}

function getChatLanguage() {
  return localStorage.getItem(CHAT_LANGUAGE_KEY) || "English";
}

function setChatLanguage(language) {
  localStorage.setItem(CHAT_LANGUAGE_KEY, language || "English");
}

function renderMessages(body, history) {
  body.innerHTML = "";
  const starter = history.length
    ? history
    : [
        {
          role: "assistant",
          content:
            "Namaste! I can help with schemes, Aadhaar, PAN, certificates, required documents, and application processes.",
        },
      ];

  starter.forEach((message) => {
      const bubble = document.createElement("div");
      bubble.className = `chat-message ${message.role === "user" ? "user" : "bot"}`;
      bubble.textContent = message.content;
      body.appendChild(bubble);
  });

  body.scrollTop = body.scrollHeight;
}

async function sendMessage(question, history, language) {
  const response = await fetch(`${FORM_SATHI_API}/chat`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      question,
      history,
      language,
    }),
  });

  if (!response.ok) {
    throw new Error("Government help desk is unavailable right now.");
  }

  const payload = await response.json();
  if (payload.source === "fallback" && payload.error) {
    throw new Error(`Live model failed: ${payload.error}`);
  }
  return payload.answer;
}

(function initChatbot() {
  const shell = createChatbotShell();
  const toggle = shell.querySelector("#chatbotToggle");
  const panel = shell.querySelector("#chatbotPanel");
  const closeButton = shell.querySelector("#chatbotClose");
  const form = shell.querySelector("#chatbotForm");
  const input = shell.querySelector("#chatbotInput");
  const body = shell.querySelector("#chatbotBody");
  const languageSelector = shell.querySelector("#chatbotLanguage");

  function resizeInput() {
    input.style.height = "0px";
    input.style.height = `${Math.min(input.scrollHeight, 132)}px`;
  }

  let history = getChatHistory();
  languageSelector.value = getChatLanguage();
  renderMessages(body, history);

  function openPanel() {
    panel.classList.remove("hidden");
  }

  function closePanel() {
    panel.classList.add("hidden");
  }

  toggle.addEventListener("click", () => {
    panel.classList.toggle("hidden");
  });

  closeButton.addEventListener("click", closePanel);

  input.addEventListener("input", resizeInput);
  languageSelector.addEventListener("change", () => {
    setChatLanguage(languageSelector.value);
  });
  resizeInput();

  form.addEventListener("submit", async (event) => {
    event.preventDefault();
    const question = input.value.trim();
    if (!question) {
      return;
    }

    openPanel();
    history.push({ role: "user", content: question });
    renderMessages(body, history);
    input.value = "";

    try {
      const answer = await sendMessage(question, history, languageSelector.value);
      history.push({ role: "assistant", content: answer });
    } catch (error) {
      history.push({ role: "assistant", content: error.message || "Unable to answer right now." });
    }

    setChatHistory(history.slice(-12));
    history = getChatHistory();
    renderMessages(body, history);
  });
})();
