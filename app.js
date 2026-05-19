(function () {
  const API_BASE = window.location.protocol.startsWith("http")
    ? window.location.origin
    : "http://127.0.0.1:8000";

  function setAmbientMode(date = new Date()) {
    const hour = date.getHours();
    const mode = hour >= 6 && hour < 18
      ? "day"
      : hour >= 5 && hour < 21
        ? "dusk"
        : "night";

    document.body.classList.remove("time-day", "time-dusk", "time-night");
    document.body.classList.add(`time-${mode}`);
    document.body.dataset.ambientMode = mode;
  }

  setAmbientMode();
  setInterval(setAmbientMode, 5 * 60 * 1000);

  const phases = [
    ["find", "Find"],
    ["read", "Read"],
    ["type", "Prepare"],
    ["check", "Check"],
    ["save", "Save"],
  ];

  const missionCatalog = {
    workflow: {
      label: "Workflow",
      icon: "fa-solid fa-rotate",
      endpoint: "/missions/social-manager",
      title: "Do you want a permanent agent task?",
      body: "Give Dash a rough outcome. It can infer cadence, tools, checkpoints, and what should stay manual.",
      tag: "Open-ended",
      cta: "Shape workflow",
      prompt: "Create a durable workflow from this goal:",
      fields: [
        ["goal", "What outcome should keep happening?", "textarea", "Keep my launch channels warm without publishing anything unapproved."],
        ["cadence", "How often should Dash check in?", "select", ["Daily", "Weekly", "When something changes", "Let Dash suggest it"]],
        ["approval", "Autonomy level", "select", ["Draft only", "Prepare and ask", "Run low-risk steps", "Let Dash suggest it"]],
      ],
    },
    task: {
      label: "Task",
      icon: "fa-solid fa-bolt",
      endpoint: "/auth/gemini/generate",
      title: "Want a one-off task handled?",
      body: "Drop the messy version. Dash will decide whether it needs browsing, context, or a checkpoint.",
      tag: "Fast start",
      cta: "Brief task",
      prompt: "Handle this one-off task:",
      fields: [
        ["name", "Name this task", "text", "E.g. Ray bans search"],
        ["task", "What should happen?", "textarea", "Compare three options and tell me what to do next."],
        ["deadline", "Timing", "text", "No rush, today, tomorrow, or exact date"],
      ],
    },
    shopping: {
      label: "Shopping",
      icon: "fa-solid fa-bag-shopping",
      endpoint: "/missions/shopping-scout",
      title: "Should I compare products or just find the right thing?",
      body: "Dash can start vague: price, fit, delivery risk, seller trust, and checkout stay separated.",
      tag: "Stops before payment",
      cta: "Scout options",
      prompt: "Scout a purchase with these constraints:",
      fields: [
        ["item", "Item, category, or rough need", "text", "A reliable carry-on, noise cancelling headphones, desk chair..."],
        ["budget", "Budget", "text", "$300 or flexible"],
        ["shipping_country", "Ship to", "text", "United States"],
        ["constraints", "Other constraints", "textarea", "International shipping, warranty, returns, size, brand, must arrive by..."],
        ["preference", "What matters most?", "select", ["Best overall", "Lowest landed cost", "Fastest delivery", "Let Dash decide"]],
      ],
    },
    travel: {
      label: "Travel",
      icon: "fa-solid fa-plane",
      endpoint: "/missions/travel-concierge",
      title: "Want me to suggest a destination or find the best dates?",
      body: "Start with a mood, a city, or a constraint. Dash can fan out flights, stays, and package timing.",
      tag: "Flexible brief",
      cta: "Plan trip",
      prompt: "Plan travel from this brief:",
      fields: [
        ["origin", "Leaving from", "text", "Toronto, New York, SFO, or use my vault"],
        ["destination", "Destination or vibe", "text", "Tokyo, beach, food trip, surprise me..."],
        ["dates", "Dates or window", "text", "Flexible in October, 5 nights, long weekend..."],
        ["budget", "Budget", "text", "Best value, under $1500, flexible"],
      ],
    },
    gifts: {
      label: "Gift",
      icon: "fa-solid fa-gift",
      endpoint: "/missions/gift-scout",
      title: "Need gift direction or a ranked shortlist?",
      body: "Dash can ask just enough: relationship, occasion, budget, interests, shipping country, and social context by consent.",
      tag: "Consent-first",
      cta: "Scout gifts",
      prompt: "Find gift ideas using this context:",
      fields: [
        ["friend_name", "Recipient", "text", "Nephew, partner, client, friend..."],
        ["occasion", "Occasion", "text", "Birthday, thank you, holiday, just because"],
        ["age_range", "Age range", "text", "Teen, 20s, 30s, kid, adult, unknown"],
        ["budget", "Budget", "text", "$50, $100, flexible"],
        ["shipping_country", "Ship to", "text", "Canada, Trinidad, United States..."],
        ["interests", "Known interests", "textarea", "Gaming, cooking, design, sneakers, no idea yet..."],
      ],
    },
    social: {
      label: "Social",
      icon: "fa-solid fa-share-nodes",
      endpoint: "/missions/social-manager",
      title: "Want drafts, a calendar, or a standing social agent?",
      body: "Dash can infer tone and cadence from approved links or start with a simple campaign goal.",
      tag: "Approval before posting",
      cta: "Shape campaign",
      prompt: "Build social support for this goal:",
      fields: [
        ["goal", "Campaign goal", "textarea", "Launch a product, revive LinkedIn, prep a content calendar..."],
        ["platforms", "Platforms", "text", "LinkedIn, Instagram, X, TikTok"],
        ["cadence", "Cadence", "select", ["One draft set", "Weekly calendar", "Permanent workflow", "Let Dash suggest it"]],
      ],
    },
  };

  const defaultState = {
    view: "agents",
    user: {
      id: "demo-user",
      name: "Sarah K.",
      email: "sarah@example.com",
      country: "United States",
      currency: "USD",
      homeAirport: "SFO",
    },
    architecture: null,
    activeMission: null,
    missions: [
      { id: "wf-sales", label: "Nexus Sales Agent", type: "workflow", status: "active", next: "Waiting for approved lead sources" },
      { id: "task-competitors", label: "ResearchCompetitors", type: "task", status: "running", next: "Summarizing high-level findings" },
    ],
    notifications: [
      { id: "n1", title: "Payment gate armed", body: "Purchases and billing changes require explicit confirmation.", unread: true, view: "payments" },
      { id: "n2", title: "Vault first", body: "New missions will check approved context before asking repeat questions.", unread: true, view: "vault" },
    ],
    messages: [
      { id: "m1", from: "Dash-1", subject: "Mission lifecycle updated", body: "Find, Read, Prepare, Check, Save is wired into the local command surface.", unread: true },
      { id: "m2", from: "Observability", subject: "Silent mode", body: "Telemetry stays behind the curtain; only high-level outcomes are shown.", unread: false },
    ],
    connectors: [
      { id: "google", name: "Google", status: "available", scopes: "Identity, calendar, Gemini on behalf of user" },
      { id: "github", name: "GitHub", status: "needs consent", scopes: "Repository selection and sync references" },
      { id: "apple", name: "Apple", status: "planned", scopes: "Identity and private relay-friendly profile context" },
      { id: "amazon", name: "Amazon", status: "session handoff", scopes: "Shopping only after user approval" },
      { id: "expedia", name: "Expedia", status: "web action", scopes: "Travel search and booking prep" },
      { id: "mongodb", name: "MongoDB Vault", status: "local demo", scopes: "Preferences, consent, mission state" },
    ],
  };

  const state = hydrateState();

  const els = {
    cards: document.getElementById("suggestion-cards"),
    workspaceKicker: document.getElementById("workspace-kicker"),
    workspaceTitle: document.getElementById("workspace-title"),
    workspaceActions: document.getElementById("workspace-actions"),
    workspaceContent: document.getElementById("workspace-content"),
    modal: document.getElementById("dynamic-modal"),
    modalKicker: document.getElementById("modal-kicker"),
    modalIcon: document.getElementById("modal-icon"),
    modalTitle: document.getElementById("modal-title"),
    modalBody: document.getElementById("modal-body-content"),
    modalForm: document.getElementById("modal-form"),
    chatSection: document.getElementById("chat-section"),
    missionTitle: document.getElementById("mission-title"),
    missionPhases: document.getElementById("mission-phases"),
    chatThread: document.getElementById("chat-thread"),
    drawer: document.getElementById("side-drawer"),
    drawerKicker: document.getElementById("drawer-kicker"),
    drawerTitle: document.getElementById("drawer-title"),
    drawerContent: document.getElementById("drawer-content"),
    notificationCount: document.getElementById("notification-count"),
    messageCount: document.getElementById("message-count"),
    profileBtn: document.getElementById("user-profile-btn"),
    profileDropdown: document.getElementById("profile-dropdown"),
    hitl: document.getElementById("modal-hitl"),
    hitlBody: document.getElementById("hitl-body"),
    toastRoot: document.getElementById("toast-root"),
  };

  function hydrateState() {
    try {
      const saved = JSON.parse(localStorage.getItem("dash-state-v1") || "null");
      return saved ? { ...defaultState, ...saved } : structuredClone(defaultState);
    } catch (_) {
      return structuredClone(defaultState);
    }
  }

  function persist() {
    const safeState = {
      user: state.user,
      missions: state.missions,
      notifications: state.notifications,
      messages: state.messages,
      connectors: state.connectors,
      view: state.view,
    };
    localStorage.setItem("dash-state-v1", JSON.stringify(safeState));
  }

  function escapeHTML(value) {
    return String(value ?? "")
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;")
      .replace(/'/g, "&#039;");
  }

  async function requestJSON(path, options = {}) {
    const finalHeaders = { "Content-Type": "application/json", ...(options.headers || {}) };
    const finalOptions = { ...options, headers: finalHeaders };
    const response = await fetch(`${API_BASE}${path}`, finalOptions);
    if (!response.ok) {
      const text = await response.text();
      throw new Error(text || `Request failed: ${response.status}`);
    }
    return response.json();
  }

  function renderSuggestions() {
    els.cards.innerHTML = Object.entries(missionCatalog).map(([key, item]) => `
      <button class="suggestion-card" type="button" data-mission="${key}">
        <span class="card-topline">
          <span class="card-icon"><i class="${item.icon}"></i></span>
          <span class="intent-tag">${escapeHTML(item.tag)}</span>
        </span>
        <h3>${escapeHTML(item.title)}</h3>
        <p>${escapeHTML(item.body)}</p>
        <span class="card-cta">${escapeHTML(item.cta)} <i class="fa-solid fa-arrow-right"></i></span>
      </button>
    `).join("");
  }

  function renderCounters() {
    const unreadNotifications = state.notifications.filter((item) => item.unread).length;
    const unreadMessages = state.messages.filter((item) => item.unread).length;
    updateCount(els.notificationCount, unreadNotifications);
    updateCount(els.messageCount, unreadMessages);
  }

  function updateCount(el, count) {
    el.textContent = count;
    el.classList.toggle("has-items", count > 0);
  }

  function setView(view) {
    state.view = view;
    document.querySelectorAll(".nav-link").forEach((btn) => {
      btn.classList.toggle("is-active", btn.dataset.view === view);
    });
    renderWorkspace(view);
    persist();
  }

  function setWorkspace(kicker, title, actions = "") {
    els.workspaceKicker.textContent = kicker;
    els.workspaceTitle.textContent = title;
    els.workspaceActions.innerHTML = actions;
  }

  function renderWorkspace(view = state.view) {
    const views = {
      home: renderAgents,
      agents: renderAgents,
      workflows: renderWorkflows,
      analytics: renderAnalytics,
      team: renderTeam,
      marketplace: renderMarketplace,
      settings: renderSettings,
      vault: renderVault,
      social: renderSocial,
      payments: renderPayments,
      messages: renderMessagesPage,
    };
    (views[view] || renderAgents)();
  }

  function architectureAgents() {
    const missions = state.architecture?.missions || {};
    return Object.entries(missions).flatMap(([mission, agents]) =>
      agents.map((agent) => ({ ...agent, mission }))
    );
  }

  function renderAgents() {
    const agents = architectureAgents();
    setWorkspace("Overview", "My Agents", `
      <button class="subtle-btn" type="button" data-action="refresh-architecture"><i class="fa-solid fa-rotate"></i> Refresh</button>
      <button class="primary-btn" type="button" data-mission="task">New task</button>
    `);

    const body = agents.length ? `
      <div class="content-stack">
        <div class="grid-3">
          ${metric("Active", state.missions.filter((m) => m.status === "active" || m.status === "running").length, "Work currently in motion")}
          ${metric("Sub-agents", agents.length, "Loaded from the local orchestrator")}
          ${metric("Gates", "3", "Payment, MFA, irreversible changes")}
        </div>
        <div class="grid-2">
          ${agents.slice(0, 8).map((agent, index) => agentCard(agent, index)).join("")}
        </div>
      </div>
    ` : `
      <div class="empty-state">
        <h3>Local orchestrator not loaded yet</h3>
        <p>Dash can still run demo missions. Refresh to load backend mission plans.</p>
      </div>
    `;
    els.workspaceContent.innerHTML = body;
  }

  function agentCard(agent, index) {
    const needsConsent = agent.consent_required ? "warn" : "ok";
    return `
      <button class="detail-card" type="button" data-agent-index="${index}">
        <span class="status-tag ${needsConsent}">${agent.consent_required ? "Consent gate" : "Autonomous"}</span>
        <h3>${escapeHTML(agent.name)}</h3>
        <p>${escapeHTML(agent.responsibility)}</p>
        <footer>
          <span class="source-tag">${escapeHTML(agent.mission)}</span>
          <i class="fa-solid fa-arrow-right"></i>
        </footer>
      </button>
    `;
  }

  function renderWorkflows() {
    setWorkspace("Operations", "Workflows", `
      <button class="primary-btn" type="button" data-mission="workflow">Create workflow</button>
    `);
    els.workspaceContent.innerHTML = `
      <div class="content-stack">
        ${state.missions.map((mission) => `
          <button class="list-row" type="button" data-open-mission="${escapeHTML(mission.id)}">
            <header>
              <span class="status-tag ${mission.status === "running" ? "warn" : "ok"}">${escapeHTML(mission.status)}</span>
              <h3>${escapeHTML(mission.label)}</h3>
            </header>
            <p>${escapeHTML(mission.next)}</p>
            <footer><span>${escapeHTML(mission.type)}</span><i class="fa-solid fa-arrow-right"></i></footer>
          </button>
        `).join("")}
        <div class="empty-state">
          <h3>Workflow design stays light</h3>
          <p>Dash asks for an outcome first, then infers cadence, tools, and where human approval belongs.</p>
        </div>
      </div>
    `;
  }

  function renderAnalytics() {
    setWorkspace("Signals", "Analytics", `
      <button class="subtle-btn" type="button" data-action="open-drawer-notifications">Alerts</button>
    `);
    els.workspaceContent.innerHTML = `
      <div class="content-stack">
        <div class="grid-3">
          ${metric("96%", "96%", "Form-fill confidence target")}
          ${metric("2", "2", "Open human checkpoints")}
          ${metric("0", "0", "Raw secrets shown to user")}
        </div>
        <div class="detail-card">
          <h3>Silent telemetry</h3>
          <p>Elastic, Arize, Fivetran, GitLab, and MongoDB are represented as mission outputs, not noisy logs. The user sees status, blockers, and approval requests.</p>
        </div>
        <div class="grid-2">
          ${["Mission routing", "DOM deconstruction", "Partner sync", "Context freshness"].map((name, index) => `
            <div class="detail-card">
              <span class="status-tag ${index === 1 ? "warn" : "ok"}">${index === 1 ? "Watch" : "Healthy"}</span>
              <h3>${name}</h3>
              <p>${index === 1 ? "Requires live browser state when a mission enters a form." : "Ready in local demo mode."}</p>
            </div>
          `).join("")}
        </div>
      </div>
    `;
  }

  function renderTeam() {
    setWorkspace("People", "Team", `
      <button class="primary-btn" type="button" data-action="invite-member">Invite</button>
    `);
    els.workspaceContent.innerHTML = `
      <div class="content-stack">
        <div class="list-row">
          <h3>Sarah K.</h3>
          <p>Owner. Can approve payment, account creation, social publishing, and context retention.</p>
          <footer><span class="status-tag ok">Owner</span><span>Full control</span></footer>
        </div>
        <div class="list-row">
          <h3>Dash-1</h3>
          <p>Master agent. Can plan and prepare, but must pause at MFA, CAPTCHA, payment, and irreversible changes.</p>
          <footer><span class="status-tag warn">Approval-bound</span><span>No raw passwords</span></footer>
        </div>
        <div class="detail-card">
          <h3>Delegation model</h3>
          <p>Specialist agents are loaded only when useful. The interface keeps orchestration quiet unless a decision belongs to the human.</p>
        </div>
      </div>
    `;
  }

  function renderMarketplace() {
    setWorkspace("Connections", "Marketplace", `
      <button class="subtle-btn" type="button" data-view="vault">Review consent</button>
    `);
    els.workspaceContent.innerHTML = `
      <div class="content-stack">
        <div class="grid-2">
          ${state.connectors.map((connector) => `
            <div class="detail-card">
              <span class="status-tag ${connector.status.includes("needs") ? "warn" : "ok"}">${escapeHTML(connector.status)}</span>
              <h3>${escapeHTML(connector.name)}</h3>
              <p>${escapeHTML(connector.scopes)}</p>
              <footer>
                <span class="source-tag">Context source</span>
                <button class="subtle-btn" type="button" data-connect="${escapeHTML(connector.id)}">Connect</button>
              </footer>
            </div>
          `).join("")}
        </div>
      </div>
    `;
  }

  function renderSettings() {
    setWorkspace("Preferences", "Settings", `
      <button class="primary-btn" type="button" data-action="save-settings">Save</button>
    `);
    els.workspaceContent.innerHTML = `
      <div class="content-stack">
        <div class="grid-2">
          <label class="field">Display name
            <input data-setting="name" value="${escapeHTML(state.user.name)}">
          </label>
          <label class="field">Primary email
            <input data-setting="email" value="${escapeHTML(state.user.email)}">
          </label>
          <label class="field">Default country
            <input data-setting="country" value="${escapeHTML(state.user.country)}">
          </label>
          <label class="field">Preferred currency
            <input data-setting="currency" value="${escapeHTML(state.user.currency)}">
          </label>
        </div>
        <div class="detail-card">
          <h3>Safety defaults</h3>
          <p>Dash prepares carts, account flows, posts, and sync plans, but stops before payment, CAPTCHA/MFA, verification, publishing, or irreversible account changes.</p>
        </div>
      </div>
    `;
  }

  function renderVault() {
    setWorkspace("Memory", "Mission Vault", `
      <button class="primary-btn" type="button" data-action="register-user">Register local user</button>
    `);
    els.workspaceContent.innerHTML = `
      <div class="content-stack">
        <div class="grid-2">
          ${vaultItem("Home airport", state.user.homeAirport, "Used for travel scouts")}
          ${vaultItem("Country", state.user.country, "Used for shipping and marketplace filtering")}
          ${vaultItem("Currency", state.user.currency, "Used for price comparison")}
          ${vaultItem("Connected sources", state.connectors.filter((c) => c.status === "available").map((c) => c.name).join(", "), "Only user-approved references")}
        </div>
        <div class="detail-card">
          <h3>Context by consent</h3>
          <p>Dash stores non-secret preferences and source references. Raw account passwords, tokens, payment data, and recovery codes stay out of the visible interface.</p>
        </div>
      </div>
    `;
  }

  function renderSocial() {
    setWorkspace("Context", "Social Links", `
      <button class="primary-btn" type="button" data-mission="social">New social mission</button>
    `);
    els.workspaceContent.innerHTML = `
      <div class="content-stack">
        <div class="detail-card">
          <h3>Consent-first social context</h3>
          <p>Dash can use OAuth where available, public links, user exports, or a browser handoff. It will not ask for raw Instagram, Facebook, or marketplace passwords.</p>
        </div>
        <div class="grid-2">
          ${["Public profile link", "User export", "Browser handoff", "Fallback questionnaire"].map((item) => `
            <button class="detail-card" type="button" data-action="social-source">
              <h3>${item}</h3>
              <p>Attach this source only for missions where it helps.</p>
            </button>
          `).join("")}
        </div>
      </div>
    `;
  }

  function renderPayments() {
    setWorkspace("Approvals", "Payments", "");
    els.workspaceContent.innerHTML = `
      <div class="content-stack">
        <div class="detail-card">
          <span class="status-tag warn">Always gated</span>
          <h3>No payment happens silently</h3>
          <p>Dash may compare prices and prepare checkout, but explicit confirmation is required before purchase, payment setup, billing changes, or irreversible commitments.</p>
        </div>
        <button class="list-row" type="button" data-action="simulate-payment-gate">
          <h3>Test approval checkpoint</h3>
          <p>Open the same high-level checkpoint used by shopping, travel, account, and social publishing flows.</p>
          <footer><span>Human-in-the-loop</span><i class="fa-solid fa-arrow-right"></i></footer>
        </button>
      </div>
    `;
  }

  function renderMessagesPage() {
    setWorkspace("Inbox", "Messages", `
      <button class="subtle-btn" type="button" data-action="mark-messages-read">Mark read</button>
    `);
    els.workspaceContent.innerHTML = messageList();
  }

  function metric(label, value, body) {
    return `
      <div class="metric-card">
        <strong>${escapeHTML(value)}</strong>
        <h3>${escapeHTML(label)}</h3>
        <p>${escapeHTML(body)}</p>
      </div>
    `;
  }

  function vaultItem(title, value, body) {
    return `
      <div class="detail-card">
        <span class="source-tag">${escapeHTML(body)}</span>
        <h3>${escapeHTML(title)}</h3>
        <p>${escapeHTML(value || "Not set")}</p>
      </div>
    `;
  }

  function openMissionModal(type) {
    const mission = missionCatalog[type];
    if (!mission) return;
    els.modalKicker.textContent = mission.label;
    els.modalTitle.textContent = mission.title;
    els.modalIcon.innerHTML = `<i class="${mission.icon}"></i>`;
    els.modalBody.innerHTML = `
      <p>${escapeHTML(mission.body)}</p>
      ${mission.fields.map(renderField).join("")}
      <div class="field">
        <label>Helpful context sources</label>
        <div class="option-row">
          ${["Mission Vault", "Public links", "Browser handoff", "Ask me first"].map((label, index) => `
            <label class="check-option">
              <input type="checkbox" name="sources" value="${escapeHTML(label)}" ${index === 0 ? "checked" : ""}>
              ${escapeHTML(label)}
            </label>
          `).join("")}
        </div>
      </div>
    `;
    els.modal.dataset.missionType = type;
    els.modal.hidden = false;
  }

  function renderField(field) {
    const [name, label, type, placeholder] = field;
    if (type === "textarea") {
      return `<label class="field">${escapeHTML(label)}<textarea name="${name}" placeholder="${escapeHTML(placeholder)}"></textarea></label>`;
    }
    if (type === "select") {
      return `
        <label class="field">${escapeHTML(label)}
          <select name="${name}">
            ${placeholder.map((option) => `<option>${escapeHTML(option)}</option>`).join("")}
          </select>
        </label>
      `;
    }
    return `<label class="field">${escapeHTML(label)}<input name="${name}" type="text" placeholder="${escapeHTML(placeholder)}"></label>`;
  }

  function closeModal() {
    els.modal.hidden = true;
    els.modalForm.reset();
    document.getElementById("modal-confirm").textContent = "Start quietly";
  }

  async function handleModalSubmit(event) {
    event.preventDefault();
    const type = els.modal.dataset.missionType;
    const mission = missionCatalog[type];
    if (!mission) {
      closeModal();
      return;
    }
    const formData = new FormData(els.modalForm);
    const payload = Object.fromEntries(formData.entries());
    payload.sources = formData.getAll("sources");
    closeModal();
    const summary = Object.entries(payload)
      .filter(([, value]) => value && !Array.isArray(value))
      .map(([key, value]) => `${key}: ${value}`)
      .join("; ");
    await executeMission(type, `${mission.prompt} ${summary || "Let Dash infer the next question."}`, payload);
  }

  function classifyPrompt(prompt) {
    const text = prompt.toLowerCase();
    if (/(flight|hotel|airbnb|travel|trip|destination|dates)/.test(text)) return "travel";
    if (/(gift|birthday|present|occasion)/.test(text)) return "gifts";
    if (/(shop|buy|price|deal|shipping|amazon|product)/.test(text)) return "shopping";
    if (/(social|post|linkedin|instagram|campaign|content)/.test(text)) return "social";
    if (/(workflow|recurring|every week|automate|permanent)/.test(text)) return "workflow";
    return "task";
  }

  async function executeMission(type, prompt, payload = {}) {
    const mission = missionCatalog[type] || missionCatalog.task;
    const missionId = `${type}-${Date.now()}`;
    state.activeMission = { id: missionId, type, prompt };
    els.chatSection.hidden = false;
    els.missionTitle.textContent = mission.label;
    els.chatThread.innerHTML = "";
    renderMissionPhases("find");
    addMessage("user", prompt);
    addMessage("agent", "Mission received. I will keep the work quiet and surface only decisions, blockers, and outcomes.");

    try {
      await softPause();
      renderMissionPhases("read");
      addMessage("agent", "Checking approved context and selecting the lightest useful agents.");
      const result = await callMissionEndpoint(type, prompt, payload);

      await softPause();
      renderMissionPhases("type");
      addMessage("agent", summarizeResult(result));

      const needsHuman = shouldGate(type, result);
      await softPause();
      renderMissionPhases(needsHuman ? "check" : "save");

      if (needsHuman) {
        addMessage("agent", "A human checkpoint is required before Dash takes the next consequential step.");
        openCheckpoint(type, result);
      } else {
        completeMission(type, result);
      }
    } catch (error) {
      renderMissionPhases("check");
      addMessage("agent", `I hit a local blocker: ${escapeHTML(error.message || error)}.`);
      notify("Mission paused", "A local endpoint or dependency needs attention before this mission can continue.", true, "analytics");
    }
  }

  async function callMissionEndpoint(type, prompt, payload) {
    const user_id = state.user.id;
    if (type === "travel") {
      return requestJSON("/missions/travel-concierge", {
        method: "POST",
        body: JSON.stringify({ user_id, prompt, ...payload }),
      });
    }
    if (type === "shopping") {
      return requestJSON("/missions/shopping-scout", {
        method: "POST",
        body: JSON.stringify({
          user_id,
          item: payload.item || prompt,
          budget: payload.budget || null,
          shipping_country: payload.shipping_country || state.user.country,
          preference: payload.preference || null,
          constraints: splitList(payload.constraints),
        }),
      });
    }
    if (type === "gifts") {
      return requestJSON("/missions/gift-scout", {
        method: "POST",
        body: JSON.stringify({
          user_id,
          friend_name: payload.friend_name || null,
          occasion: payload.occasion || "general",
          budget: payload.budget || null,
          age_range: payload.age_range || null,
          interests: splitList(payload.interests || payload.preference || payload.item),
          shipping_country: payload.shipping_country || state.user.country,
          public_social_links: [],
          connected_social_session: false,
        }),
      });
    }
    if (type === "social" || type === "workflow") {
      return requestJSON("/missions/social-manager", {
        method: "POST",
        body: JSON.stringify({ user_id, prompt, ...payload }),
      });
    }
    return requestJSON("/auth/gemini/generate", {
      method: "POST",
      body: JSON.stringify({ user_id, prompt, mission: type }),
      headers: { Authorization: "Bearer demo-token" },
    });
  }

  function splitList(value) {
    return String(value || "")
      .split(/[,;]+/)
      .map((item) => item.trim())
      .filter(Boolean);
  }

  function summarizeResult(result) {
    if (result.questions?.length) {
      return `I need a little more context before recommending: ${result.questions.map(escapeHTML).join(" ")}`;
    }
    if (result.next_action) {
      return escapeHTML(result.next_action);
    }
    if (result.text) {
      return escapeHTML(result.text);
    }
    if (result.status) {
      return `Status: ${escapeHTML(result.status)}.`;
    }
    return "The mission is staged and ready for the next step.";
  }

  function shouldGate(type, result) {
    if (result.questions?.length) return false;
    return ["travel", "gifts", "shopping", "social", "workflow"].includes(type);
  }

  function openCheckpoint(type, result) {
    els.hitlBody.textContent = checkpointText(type, result);
    els.hitl.dataset.type = type;
    els.hitl.hidden = false;
    notify("Approval needed", "Dash paused before a consequential step.", true, "payments");
  }

  function checkpointText(type) {
    const copy = {
      travel: "Dash can prepare booking options, but needs approval before reserving flights, stays, or packages.",
      gifts: "Dash can prepare recommendations and carts, but needs approval before checkout or payment.",
      shopping: "Dash can compare products and prepare a cart, but needs approval before checkout or payment.",
      social: "Dash can draft and schedule, but needs approval before publishing.",
      workflow: "Dash can create the workflow plan, but needs approval before enabling recurring autonomous actions.",
    };
    return copy[type] || "Dash needs your confirmation before continuing.";
  }

  function completeMission(type, result) {
    renderMissionPhases("save", true);
    addMessage("agent", "Done. I saved the high-level outcome and left sensitive details out of the visible thread.");
    state.missions.unshift({
      id: `${type}-${Date.now()}`,
      label: `${missionCatalog[type]?.label || "Task"} mission`,
      type,
      status: "active",
      next: result.next_action || result.status || "Ready for review",
    });
    message("Dash-1", "Mission update", `${missionCatalog[type]?.label || "Task"} mission reached a stable state.`);
    persist();
    renderWorkspace(state.view);
  }

  function renderMissionPhases(active, allDone = false) {
    const activeIndex = phases.findIndex(([key]) => key === active);
    els.missionPhases.innerHTML = phases.map(([key, label], index) => {
      const cls = allDone || index < activeIndex ? "done" : key === active ? "active" : "";
      return `<div class="phase-step ${cls}">${index + 1}. ${label}</div>`;
    }).join("");
  }

  function addMessage(role, content) {
    const node = document.createElement("div");
    node.className = `message ${role}`;
    node.innerHTML = content;
    els.chatThread.appendChild(node);
    node.scrollIntoView({ block: "nearest" });
  }

  function notify(title, body, unread = true, view = "messages") {
    state.notifications.unshift({ id: `n-${Date.now()}`, title, body, unread, view });
    renderCounters();
    persist();
    toast(title, body);
  }

  function message(from, subject, body) {
    state.messages.unshift({ id: `m-${Date.now()}`, from, subject, body, unread: true });
    renderCounters();
    persist();
  }

  function toast(title, body) {
    const node = document.createElement("div");
    node.className = "toast";
    node.innerHTML = `<strong>${escapeHTML(title)}</strong><p>${escapeHTML(body)}</p>`;
    els.toastRoot.appendChild(node);
    setTimeout(() => node.remove(), 4200);
  }

  function openDrawer(kind) {
    if (kind === "messages") {
      els.drawerKicker.textContent = "Inbox";
      els.drawerTitle.textContent = "Messages";
      els.drawerContent.innerHTML = messageList();
    } else {
      els.drawerKicker.textContent = "Inbox";
      els.drawerTitle.textContent = "Notifications";
      els.drawerContent.innerHTML = notificationList();
    }
    els.drawer.hidden = false;
  }

  function notificationList() {
    return `
      <div class="content-stack">
        ${state.notifications.map((item) => `
          <button class="list-row" type="button" data-notification="${escapeHTML(item.id)}">
            <span class="status-tag ${item.unread ? "warn" : "ok"}">${item.unread ? "Unread" : "Read"}</span>
            <h3>${escapeHTML(item.title)}</h3>
            <p>${escapeHTML(item.body)}</p>
            <footer><span>${escapeHTML(item.view)}</span><i class="fa-solid fa-arrow-right"></i></footer>
          </button>
        `).join("") || `<div class="empty-state"><h3>Quiet inbox</h3><p>No notifications right now.</p></div>`}
      </div>
    `;
  }

  function messageList() {
    return `
      <div class="content-stack">
        ${state.messages.map((item) => `
          <button class="list-row" type="button" data-message="${escapeHTML(item.id)}">
            <span class="status-tag ${item.unread ? "warn" : "ok"}">${item.unread ? "Unread" : "Read"}</span>
            <h3>${escapeHTML(item.subject)}</h3>
            <p>${escapeHTML(item.from)}: ${escapeHTML(item.body)}</p>
          </button>
        `).join("") || `<div class="empty-state"><h3>No messages</h3><p>Mission summaries will appear here.</p></div>`}
      </div>
    `;
  }

  function softPause() {
    return new Promise((resolve) => setTimeout(resolve, 420));
  }

  async function loadArchitecture() {
    try {
      state.architecture = await requestJSON("/architecture");
      persist();
      renderWorkspace(state.view);
    } catch (error) {
      notify("Architecture unavailable", "Dash could not load the local orchestrator plan.", true, "analytics");
    }
  }

  async function connectSource(source) {
    if (source === "google") {
      const result = await requestJSON("/auth/google/url");
      if (result.demo_mode || !result.url) {
        notify("Google demo mode", "OAuth is not configured locally, so Dash staged a consent reference only.", true, "vault");
        return;
      }
      window.open(result.url, "_blank", "noopener,noreferrer");
      return;
    }
    notify("Connection staged", `${source} will use an approved OAuth, vault reference, or browser handoff flow.`, true, "marketplace");
  }

  async function registerUser() {
    const result = await requestJSON("/users/register", {
      method: "POST",
      body: JSON.stringify({
        user_id: state.user.id,
        display_name: state.user.name,
        primary_email: state.user.email,
        auth_provider: "local-demo",
        authorized_sources: state.connectors.filter((c) => c.status === "available").map((c) => c.id),
        default_country: state.user.country,
        preferred_currency: state.user.currency,
        mission_goals: ["gift-scout", "travel", "account-resolver", "social-manager"],
      }),
    });
    notify("User registered", result.next_action || "Mission Vault profile is ready.", true, "vault");
  }

  function saveSettings() {
    document.querySelectorAll("[data-setting]").forEach((input) => {
      state.user[input.dataset.setting] = input.value.trim();
    });
    persist();
    notify("Settings saved", "Preferences updated for future local missions.", false, "settings");
    renderWorkspace("settings");
  }

  function bindEvents() {
    document.addEventListener("click", async (event) => {
      const target = event.target.closest("button");
      if (!target) return;

      if (target.dataset.view) {
        els.profileDropdown.hidden = true;
        setView(target.dataset.view);
      }
      if (target.dataset.mission) openMissionModal(target.dataset.mission);
      if (target.dataset.connect) await connectSource(target.dataset.connect);
      if (target.dataset.notification) {
        const item = state.notifications.find((n) => n.id === target.dataset.notification);
        if (item) {
          item.unread = false;
          renderCounters();
          persist();
          setView(item.view || "messages");
          els.drawer.hidden = true;
        }
      }
      if (target.dataset.message) {
        const item = state.messages.find((m) => m.id === target.dataset.message);
        if (item) item.unread = false;
        renderCounters();
        persist();
        if (!els.drawer.hidden) openDrawer("messages");
        if (state.view === "messages") renderMessagesPage();
      }
      if (target.dataset.agentIndex) {
        const agent = architectureAgents()[Number(target.dataset.agentIndex)];
        if (agent) openAgentDetail(agent);
      }
      if (target.dataset.action) await handleAction(target.dataset.action);
    });

    document.getElementById("prompt-form").addEventListener("submit", async (event) => {
      event.preventDefault();
      const input = document.getElementById("main-input");
      const prompt = input.value.trim();
      if (!prompt) return;
      input.value = "";
      await executeMission(classifyPrompt(prompt), prompt);
    });

    els.modalForm.addEventListener("submit", handleModalSubmit);
    document.getElementById("modal-close").addEventListener("click", closeModal);
    document.getElementById("modal-cancel").addEventListener("click", closeModal);
    document.getElementById("notifications-btn").addEventListener("click", () => openDrawer("notifications"));
    document.getElementById("messages-btn").addEventListener("click", () => openDrawer("messages"));
    document.getElementById("drawer-close").addEventListener("click", () => { els.drawer.hidden = true; });
    document.getElementById("scroll-left").addEventListener("click", () => els.cards.scrollBy({ left: -260, behavior: "smooth" }));
    document.getElementById("scroll-right").addEventListener("click", () => els.cards.scrollBy({ left: 260, behavior: "smooth" }));
    document.getElementById("clear-mission").addEventListener("click", () => { els.chatSection.hidden = true; });
    document.getElementById("btn-hitl-deny").addEventListener("click", () => {
      els.hitl.hidden = true;
      renderMissionPhases("check");
      addMessage("agent", "Checkpoint denied. I paused the mission and did not continue.");
      notify("Mission paused", "The human checkpoint was denied.", true, "messages");
    });
    document.getElementById("btn-hitl-approve").addEventListener("click", () => {
      const type = els.hitl.dataset.type || "task";
      els.hitl.hidden = true;
      renderMissionPhases("save", true);
      addMessage("agent", "Approved. I can continue with the prepared next step and will keep confirmation boundaries intact.");
      completeMission(type, { status: "approved" });
    });
    els.profileBtn.addEventListener("click", (event) => {
      event.stopPropagation();
      els.profileDropdown.hidden = !els.profileDropdown.hidden;
      els.profileBtn.setAttribute("aria-expanded", String(!els.profileDropdown.hidden));
    });
    document.addEventListener("click", (event) => {
      if (!event.target.closest("#profile-dropdown") && !event.target.closest("#user-profile-btn")) {
        els.profileDropdown.hidden = true;
        els.profileBtn.setAttribute("aria-expanded", "false");
      }
    });
  }

  async function handleAction(action) {
    const actions = {
      "refresh-architecture": loadArchitecture,
      "open-drawer-notifications": () => openDrawer("notifications"),
      "mark-messages-read": () => {
        state.messages.forEach((messageItem) => { messageItem.unread = false; });
        renderCounters();
        persist();
        renderMessagesPage();
      },
      "save-settings": saveSettings,
      "register-user": registerUser,
      "connect-google": () => connectSource("google"),
      "invite-member": () => notify("Invite staged", "Team invitations need an email service before sending.", true, "team"),
      "social-source": () => notify("Social source staged", "Dash will ask for consent before reading any social context.", true, "social"),
      "simulate-payment-gate": () => openCheckpoint("shopping", { status: "demo" }),
    };
    if (actions[action]) await actions[action]();
  }

  function openAgentDetail(agent) {
    els.modalKicker.textContent = agent.mission;
    els.modalTitle.textContent = agent.name;
    els.modalIcon.innerHTML = `<i class="fa-solid fa-diagram-project"></i>`;
    els.modalBody.innerHTML = `
      <p>${escapeHTML(agent.responsibility)}</p>
      <div class="detail-card">
        <h3>Tools</h3>
        <p>${agent.tools.map(escapeHTML).join(", ")}</p>
      </div>
      <div class="detail-card">
        <h3>Control</h3>
        <p>${agent.consent_required ? "This agent pauses for human consent before sensitive action." : "This agent can prepare low-risk work autonomously."}</p>
      </div>
    `;
    els.modal.dataset.missionType = "";
    document.getElementById("modal-confirm").textContent = "Done";
    els.modal.hidden = false;
  }

  function init() {
    renderSuggestions();
    bindEvents();
    renderCounters();
    renderWorkspace(state.view);
    loadArchitecture();
  }

  init();
})();
