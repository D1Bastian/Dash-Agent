(function () {
  const API_BASE = window.location.protocol.startsWith("http")
    ? window.location.origin
    : "http://127.0.0.1:8000";

  // ── Authentication & Routing ──────────────────────────────────────────
  const hash = window.location.hash.substring(1);
  const params = new URLSearchParams(hash);
  const searchParams = new URLSearchParams(window.location.search);

  if (searchParams.get("logout") === "1" || searchParams.get("reset") === "1") {
    localStorage.removeItem("dash-token");
    localStorage.removeItem("dash-state-v1");
    localStorage.removeItem("dash-partner-config");
    localStorage.removeItem("dash-gemini-key");
    window.history.replaceState(null, null, window.location.pathname);
  }

  // Generic authentication handling
  const provider = params.get("provider") || "google";
  const token = params.get("access_token");
  const user_id = params.get("user_id");
  const name = params.get("name");
  const email = params.get("email");
  if (token) {
    // Store token
    localStorage.setItem("dash-token", token);
    // Save user info
    const saved = JSON.parse(localStorage.getItem("dash-state-v1") || "null");
    const newState = saved || { user: {} };
    newState.user = { id: user_id, name: name, email: email, country: "United States", currency: "USD", homeAirport: "SFO" };
    localStorage.setItem("dash-state-v1", JSON.stringify(newState));
    // Load persistent memory from MongoDB Vault if provider is not demo
    if (provider !== "demo") {
      fetch(`${API_BASE}/api/vault/load?user_id=${encodeURIComponent(user_id || "anonymous")}`, { headers: { "Authorization": `Bearer ${token}` } })
        .then(res => res.json())
        .then(data => {
          // Merge loaded memory into state
          state.user = { ...state.user, ...data.user };
          state.memory = data.memory || {};
          persist();
        })
        .catch(console.error);
    }
    // Clean up URL
    window.history.replaceState(null, null, window.location.pathname);
  } else if (searchParams.get("auth") === "demo") {
    const saved = JSON.parse(localStorage.getItem("dash-state-v1") || "null");
    const newState = saved || { user: {} };
    newState.user = { id: "demo-authorized", name: "Sarah K.", email: "sarah@example.com", country: "United States", currency: "USD", homeAirport: "SFO" };
    localStorage.setItem("dash-state-v1", JSON.stringify(newState));
    // Clean up URL
    window.history.replaceState(null, null, window.location.pathname);
  }

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

  async function pollHealth() {
    try {
      const res = await fetch(`${API_BASE}/health/partners`);
      const data = await res.json();
      const allUp = Object.values(data).some(i => i.status === "up");
      const dot = document.getElementById("nav-health-dot");
      if (dot) dot.style.backgroundColor = allUp ? "var(--ok)" : "var(--danger)";
    } catch {
      const dot = document.getElementById("nav-health-dot");
      if (dot) dot.style.backgroundColor = "var(--danger)";
    }
  }
  setTimeout(pollHealth, 1000);
  setInterval(pollHealth, 60000);

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
      id: "require-login",
      name: "",
      email: "",
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
      { id: "microsoft", name: "Microsoft", status: "needs consent", scopes: "Identity, calendar, Graph API" },
      { id: "anthropic", name: "Anthropic", status: "needs consent", scopes: "Identity and Claude model access" },
      { id: "openai", name: "OpenAI", status: "needs consent", scopes: "Identity and GPT model access" },
      { id: "mongodb", name: "MongoDB Vault", status: "available", scopes: "Preferences, consent, mission state" },
      { id: "apple", name: "Apple", status: "planned", scopes: "Identity and private relay-friendly profile context" },
      { id: "amazon", name: "Amazon", status: "session handoff", scopes: "Shopping only after user approval" },
      { id: "expedia", name: "Expedia", status: "web action", scopes: "Travel search and booking prep" },
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
    const geminiKey = localStorage.getItem('dash-gemini-key') || '';
    const finalHeaders = { "Content-Type": "application/json", ...(geminiKey ? {'X-Gemini-Key': geminiKey} : {}), ...(options.headers || {}) };
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
      partners: renderPartners,
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
    const partnerConfig = JSON.parse(localStorage.getItem('dash-partner-config') || '{}');
    setWorkspace("Preferences", "Settings", `
      <button class="primary-btn" type="button" data-action="save-settings">Save</button>
    `);
    els.workspaceContent.innerHTML = `
      <div class="content-stack">
        <div class="vault-section" style="background:rgba(99,102,241,0.08);border:1px solid rgba(99,102,241,0.25);border-radius:12px;padding:1.2rem 1.4rem;margin-bottom:0.5rem;">
          <h3 style="margin:0 0 0.4rem;"><i class="fa-solid fa-key"></i> API Keys <span class="tag-pill" style="background:var(--ok);color:#000;font-size:0.7rem;margin-left:8px;padding:2px 8px;border-radius:99px;font-weight:600;">Judge Setup</span></h3>
          <p style="color:var(--muted);font-size:0.9rem;margin-bottom:1rem;">Paste your Gemini API key to activate AI features. Partner keys can be added below for live integrations.</p>
          <div style="display:flex;gap:0.5rem;align-items:center;flex-wrap:wrap;">
            <input id="gemini-key-input" type="password" class="input-field" placeholder="Gemini API key" style="flex:1;min-width:220px;font-family:monospace;background:rgba(255,255,255,0.05);border:1px solid rgba(255,255,255,0.15);border-radius:8px;padding:0.55rem 0.9rem;color:var(--text);font-size:0.95rem;" value="${localStorage.getItem('dash-gemini-key') || ''}">
            <button class="primary-btn" onclick="saveGeminiKey()" style="white-space:nowrap;"><i class="fa-solid fa-check"></i> Validate &amp; Save</button>
          </div>
          <p id="gemini-key-status" style="font-size:0.82rem;margin-top:0.5rem;color:var(--muted);"></p>
        </div>
        <div class="vault-section" style="background:rgba(16,185,129,0.08);border:1px solid rgba(16,185,129,0.25);border-radius:12px;padding:1.2rem 1.4rem;margin-bottom:0.5rem;">
          <h3 style="margin:0 0 0.4rem;"><i class="fa-solid fa-plug"></i> Partner Keys</h3>
          <p style="color:var(--muted);font-size:0.9rem;margin-bottom:1rem;">Paste any live partner service keys you want Dash to use for this session. These values are stored locally in your browser and sent to the backend for temporary use.</p>
          <div class="grid-2" style="gap:0.75rem;">
            <label class="field">Elastic Cloud ID
              <input id="elastic-cloud-id" value="${escapeHTML(partnerConfig.elastic_cloud_id || '')}" placeholder="cloud-id:...">
            </label>
            <label class="field">Elastic API Key
              <input id="elastic-api-key" value="${escapeHTML(partnerConfig.elastic_api_key || '')}" placeholder="base64 key...">
            </label>
            <label class="field">Arize API Key
              <input id="arize-api-key" value="${escapeHTML(partnerConfig.arize_api_key || '')}" placeholder="arize key...">
            </label>
            <label class="field">Arize Space ID
              <input id="arize-space-id" value="${escapeHTML(partnerConfig.arize_space_id || '')}" placeholder="space id...">
            </label>
            <label class="field">Fivetran API Key
              <input id="fivetran-api-key" value="${escapeHTML(partnerConfig.fivetran_api_key || '')}" placeholder="fivetran key...">
            </label>
            <label class="field">Fivetran API Secret
              <input id="fivetran-api-secret" value="${escapeHTML(partnerConfig.fivetran_api_secret || '')}" placeholder="fivetran secret...">
            </label>
            <label class="field">GitLab Token
              <input id="gitlab-token" value="${escapeHTML(partnerConfig.gitlab_token || '')}" placeholder="gitlab token...">
            </label>
            <label class="field">Dynatrace URL
              <input id="dynatrace-api-url" value="${escapeHTML(partnerConfig.dynatrace_api_url || '')}" placeholder="https://...">
            </label>
            <label class="field">Dynatrace Token
              <input id="dynatrace-api-token" value="${escapeHTML(partnerConfig.dynatrace_api_token || '')}" placeholder="dynatrace token...">
            </label>
            <label class="field">Mongo URI
              <input id="mongo-uri" value="${escapeHTML(partnerConfig.mongo_uri || '')}" placeholder="mongodb+srv://...">
            </label>
          </div>
          <button class="primary-btn" type="button" onclick="savePartnerConfig()" style="margin-top:1rem;white-space:nowrap;"><i class="fa-solid fa-floppy-disk"></i> Save Partner Keys</button>
          <p id="partner-key-status" style="font-size:0.82rem;margin-top:0.5rem;color:var(--muted);"></p>
        </div>
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
        <div class="detail-card">
          <h3>Superpowers</h3>
          <p>Test your GitLab configuration by creating a new repository for your mission scripts.</p>
          <button class="primary-btn" type="button" data-action="test-gitlab" style="margin-top: 10px;">Test GitLab Sync</button>
        </div>
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

  async function renderPartners() {
    setWorkspace("Superpowers", "Partner Integrations", `
      <button class="subtle-btn" type="button" onclick="renderWorkspace('partners')"><i class="fa-solid fa-rotate"></i> Refresh Pings</button>
    `);
    els.workspaceContent.innerHTML = `<div class="empty-state"><i class="fa-solid fa-spinner fa-spin"></i><p>Pinging partners...</p></div>`;
    
    try {
      const res = await fetch(`${API_BASE}/health/partners`);
      const data = await res.json();
      
      const cards = Object.entries(data).map(([name, info]) => {
        const isUp = info.status === "up";
        const isDryRun = info.status === "dry-run";
        const statusClass = isUp ? "ok" : isDryRun ? "warn" : "down";
        const statusText = isUp ? "Connected" : isDryRun ? "Dry-run mode" : "Error";
        const msText = info.latency_ms ? `${info.latency_ms}ms` : "--";
        
        return `
          <div class="detail-card">
            <span class="status-tag ${statusClass}">${statusText}</span>
            <h3 style="text-transform: capitalize;">${name}</h3>
            <p>${escapeHTML(info.role)}</p>
            <footer><span>Latency</span><strong>${msText}</strong></footer>
          </div>
        `;
      }).join("");
      
      els.workspaceContent.innerHTML = `<div class="grid-3">${cards}</div>`;
      
      const dot = document.getElementById("nav-health-dot");
      if (dot) {
        const allUp = Object.values(data).some(i => i.status === "up");
        dot.style.backgroundColor = allUp ? "var(--color-success)" : "var(--color-warning)";
      }
    } catch (err) {
      els.workspaceContent.innerHTML = `<div class="empty-state"><h3>Ping Failed</h3><p>${escapeHTML(err.message)}</p></div>`;
    }
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
    await executeMission(type, summary, payload);
  }

  // ── Conversation history (persists for the lifetime of the session) ──────────
  let conversationHistory = [];  // [{role:"user"|"assistant", content:"..."}]

  // The ONE function that handles all user input — no task classification needed.
  // Gemini decides what to do based on the full conversation.
  async function sendMessage(prompt) {
    if (!prompt.trim()) return;

    // Show chat panel
    els.chatSection.hidden = false;
    els.missionTitle.textContent = "Dash";

    // Add user message to history and UI
    conversationHistory.push({ role: "user", content: prompt });
    addMessage("user", escapeHTML(prompt));

    // Show thinking indicator
    const thinkingNode = addThinkingBubble();
    renderMissionPhases("find");

    const streamNode = addStreamBubble();
    let fullText = "";

    try {
      renderMissionPhases("read");
      thinkingNode.remove();
      renderMissionPhases("type");

      // Stream from /chat with full conversation history
      const geminiKey = localStorage.getItem('dash-gemini-key') || '';
      const resp = await fetch(`${API_BASE}/chat`, {
        method: "POST",
        headers: { "Content-Type": "application/json", ...(geminiKey ? {'X-Gemini-Key': geminiKey} : {}) },
        body: JSON.stringify({
          user_id: state.user.id,
          history: conversationHistory,
        }),
      });

      if (!resp.ok) {
        const txt = await resp.text();
        throw new Error(txt || `Request failed: ${resp.status}`);
      }

      const reader  = resp.body.getReader();
      const decoder = new TextDecoder();

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        const lines = decoder.decode(value, { stream: true }).split("\n");
        for (const line of lines) {
          if (line.startsWith("data:")) {
            try {
              const json = JSON.parse(line.slice(5).trim());
              if (json.text !== undefined) {
                fullText = json.text;
                streamNode.innerHTML = formatMarkdown(fullText) + `<span class="cursor-blink">▍</span>`;
                streamNode.scrollIntoView({ block: "nearest" });
              }
            } catch (_) {}
          }
        }
      }

      streamNode.innerHTML = formatMarkdown(fullText);
      renderMissionPhases("save", true);

      // Add assistant response to history so next message has context
      if (fullText.trim()) {
        conversationHistory.push({ role: "assistant", content: fullText });
      }

    } catch (err) {
      thinkingNode?.remove();
      streamNode.remove();
      renderMissionPhases("check");
      addMessage("agent", `⚠️ ${escapeHTML(err.message || String(err))}`);
    }
  }

  // Keep callMissionStream for modal-based structured missions (shopping, travel, etc)
  // but route them through /chat as well so history is maintained
  async function callMissionStream(type, prompt, payload, onChunk) {
    // Build a rich prompt from the modal payload
    const payloadSummary = Object.entries(payload || {})
      .filter(([k, v]) => v && k !== "sources" && k !== "elastic")
      .map(([k, v]) => `${k}: ${v}`)
      .join("; ");
    const fullPrompt = payloadSummary ? `${prompt} — ${payloadSummary}` : prompt;

    conversationHistory.push({ role: "user", content: fullPrompt });

    const geminiKey = localStorage.getItem('dash-gemini-key') || '';
    const resp = await fetch(`${API_BASE}/chat`, {
      method: "POST",
      headers: { "Content-Type": "application/json", ...(geminiKey ? {'X-Gemini-Key': geminiKey} : {}) },
      body: JSON.stringify({ user_id: state.user.id, history: conversationHistory }),
    });

    if (!resp.ok) throw new Error(await resp.text() || `Failed: ${resp.status}`);

    const reader  = resp.body.getReader();
    const decoder = new TextDecoder();
    let accumulated = "";

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;
      const lines = decoder.decode(value, { stream: true }).split("\n");
      for (const line of lines) {
        if (line.startsWith("data:")) {
          try {
            const json = JSON.parse(line.slice(5).trim());
            if (json.text !== undefined) { accumulated += json.text; onChunk(accumulated); }
          } catch (_) {}
        }
      }
    }
    if (accumulated.trim()) conversationHistory.push({ role: "assistant", content: accumulated });
    return { status: "ok", text: accumulated };
  }

  // Keep collectInlineProfile and executeMission for modal flows
  async function executeMission(type, prompt, payload = {}) {
    const mission = missionCatalog[type] || missionCatalog.task;
    els.chatSection.hidden = false;
    els.missionTitle.textContent = mission.label;
    renderMissionPhases("find");
    addMessage("user", formatMarkdown(prompt));
    const thinkingNode = addThinkingBubble();
    await softPause(600);
    thinkingNode.remove();
    renderMissionPhases("type");
    const streamNode = addStreamBubble();
    let finalText = "";
    try {
      await callMissionStream(type, prompt, payload, (chunk) => {
        finalText = chunk;
        streamNode.innerHTML = formatMarkdown(chunk) + `<span class="cursor-blink">▍</span>`;
        streamNode.scrollIntoView({ block: "nearest" });
      });
      streamNode.innerHTML = formatMarkdown(finalText);
      renderMissionPhases("save", true);
    } catch (err) {
      thinkingNode?.remove();
      renderMissionPhases("check");
      addMessage("agent", `⚠️ ${escapeHTML(err.message || String(err))}`);
    }
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

  function softPause(ms = 420) {
    return new Promise((resolve) => setTimeout(resolve, ms));
  }

  function formatMarkdown(text) {
    return String(text || "")
      .replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;")
      .replace(/\*\*(.+?)\*\*/g, "<strong>$1</strong>")
      .replace(/\*(.+?)\*/g, "<em>$1</em>")
      .replace(/`([^`]+)`/g, "<code>$1</code>")
      .replace(/^#{1,3}\s+(.+)$/gm, "<h4>$1</h4>")
      .replace(/^[-*]\s+(.+)$/gm, "<li>$1</li>")
      .replace(/(<li>.*<\/li>)/gs, "<ul>$1</ul>")
      .replace(/\n{2,}/g, "</p><p>")
      .replace(/\n/g, "<br>")
      .replace(/^(?!<[hul])(.+)/, "<p>$1</p>");
  }

  function addMessage(role, content) {
    const node = document.createElement("div");
    node.className = `message ${role}`;
    node.innerHTML = content;
    els.chatThread.appendChild(node);
    node.scrollIntoView({ block: "nearest" });
    // Animate in
    node.style.opacity = "0";
    node.style.transform = "translateY(10px)";
    requestAnimationFrame(() => {
      node.style.transition = "opacity 0.3s ease, transform 0.3s ease";
      node.style.opacity = "1";
      node.style.transform = "translateY(0)";
    });
    return node;
  }

  function addThinkingBubble() {
    const node = document.createElement("div");
    node.className = "message agent thinking";
    node.innerHTML = `
      <span class="dot-pulse"></span>
      <span class="dot-pulse" style="animation-delay:0.15s"></span>
      <span class="dot-pulse" style="animation-delay:0.3s"></span>
      <span style="margin-left:8px;color:var(--muted);font-size:0.85em">Thinking...</span>
    `;
    els.chatThread.appendChild(node);
    node.scrollIntoView({ block: "nearest" });
    return node;
  }

  function addStreamBubble() {
    const node = document.createElement("div");
    node.className = "message agent stream-bubble";
    node.innerHTML = "";
    els.chatThread.appendChild(node);
    node.scrollIntoView({ block: "nearest" });
    return node;
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
    const oauthProviders = ["google", "github", "microsoft", "anthropic", "openai", "apple"];
    if (oauthProviders.includes(source)) {
      window.location.href = `${API_BASE}/auth/${source}/url`;
      return;
    }
    notify("Connection staged", `${source} will use an approved OAuth, vault reference, or browser handoff flow.`, true, "marketplace");
  }

  function appConnectProvider(source) {
    connectSource(source);
  }

  function toggleCreateAccountForm() {
    const panel = document.getElementById("account-creation-panel");
    if (!panel) return;
    panel.hidden = !panel.hidden;
  }

  async function createLocalAccount() {
    const nameInput = document.getElementById("account-name");
    const emailInput = document.getElementById("account-email");
    const name = nameInput?.value?.trim() || "";
    const email = emailInput?.value?.trim() || "";

    if (!name || !email) {
      notify("Complete account details", "Please enter both your name and email to create a local account.", true, "settings");
      return;
    }

    state.user.id = state.user.id && state.user.id !== "require-login"
      ? state.user.id
      : `local-${Date.now()}`;
    state.user.name = name;
    state.user.email = email;
    persist();

    try {
      await registerUser();
      notify("Account created", "Your local account is ready. Google connect is available next.", false, "settings");
    } catch (error) {
      notify("Local account saved", "Account created locally, but backend registration could not complete.", true, "settings");
    }

    const loginOverlay = document.getElementById("login-overlay");
    const appShell = document.querySelector(".app-shell");
    if (loginOverlay && appShell) {
      loginOverlay.hidden = true;
      appShell.hidden = false;
      startApp();
    }
  }

  async function registerUser() {
    const userId = state.user.id && state.user.id !== "require-login"
      ? state.user.id
      : `local-${Date.now()}`;
    state.user.id = userId;
    persist();
    const result = await requestJSON("/users/register", {
      method: "POST",
      body: JSON.stringify({
        user_id: userId,
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

  function startApp() {
    renderSuggestions();
    bindEvents();
    renderCounters();
    renderWorkspace(state.view);
    loadArchitecture();
  }

  window.toggleCreateAccountForm = toggleCreateAccountForm;
  window.createLocalAccount = createLocalAccount;
  window.appConnectGoogle = () => connectSource("google");
  window.appConnectProvider = appConnectProvider;
  window.signOut = signOut;

  function saveSettings() {
    document.querySelectorAll("[data-setting]").forEach((input) => {
      state.user[input.dataset.setting] = input.value.trim();
    });
    persist();
    notify("Settings saved", "Preferences updated for future local missions.", false, "settings");
    renderWorkspace("settings");
  }

  function attachLoginHandlers() {
    document.getElementById("google-connect-btn")?.addEventListener("click", () => connectSource("google"));
    document.getElementById("create-account-toggle")?.addEventListener("click", toggleCreateAccountForm);
    document.getElementById("create-account-submit")?.addEventListener("click", createLocalAccount);
    document.getElementById("demo-login-btn")?.addEventListener("click", () => { window.location.href = "?auth=demo"; });
    document.getElementById("login-gemini-key-btn")?.addEventListener("click", () => window.saveGeminiKey('login-gemini-key-input','login-gemini-key-status'));
    document.querySelectorAll(".provider-icons button[data-provider]").forEach((button) => {
      const provider = button.dataset.provider;
      if (provider) button.addEventListener("click", () => appConnectProvider(provider));
    });
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
      await sendMessage(prompt);
    });

    els.modalForm.addEventListener("submit", handleModalSubmit);
    document.getElementById("modal-close").addEventListener("click", closeModal);
    document.getElementById("modal-cancel").addEventListener("click", closeModal);
    document.getElementById("notifications-btn").addEventListener("click", () => openDrawer("notifications"));
    document.getElementById("messages-btn").addEventListener("click", () => openDrawer("messages"));
    document.getElementById("drawer-close").addEventListener("click", () => { els.drawer.hidden = true; });
    document.getElementById("scroll-left").addEventListener("click", () => els.cards.scrollBy({ left: -260, behavior: "smooth" }));
    document.getElementById("scroll-right").addEventListener("click", () => els.cards.scrollBy({ left: 260, behavior: "smooth" }));
    document.getElementById("clear-mission").addEventListener("click", () => {
      els.chatSection.hidden = true;
      els.chatThread.innerHTML = "";
      conversationHistory = [];   // fresh conversation
    });
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

  async function testGitlab() {
    els.workspaceContent.innerHTML = `<div class="empty-state"><i class="fa-solid fa-spinner fa-spin"></i><p>Creating repository...</p></div>`;
    try {
      const res = await fetch(`${API_BASE}/missions/gitlab-sync`, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({}) });
      const data = await res.json();
      if (data.ok) {
        if (data.mode === "dry-run") {
          notify("GitLab Sync", data.message, false, "settings");
        } else {
          notify("GitLab Sync Success", `Repository created at ${data.repo_url}`, false, "settings");
        }
      } else {
        notify("GitLab Sync Failed", data.error, true, "settings");
      }
    } catch (err) {
      notify("GitLab Error", err.message, true, "settings");
    }
    renderSettings();
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
      "sign-out": signOut,
      "test-gitlab": testGitlab,
      "invite-member": () => notify("Invite staged", "Team invitations need an email service before sending.", true, "team"),
      "social-source": () => notify("Social source staged", "Dash will ask for consent before reading any social context.", true, "social"),
      "simulate-payment-gate": () => openCheckpoint("shopping", { status: "demo" }),
    };
    if (actions[action]) await actions[action]();
  }

  function signOut() {
    localStorage.removeItem("dash-token");
    localStorage.removeItem("dash-state-v1");
    state.user = {
      id: "require-login",
      name: "",
      email: "",
      country: "United States",
      currency: "USD",
      homeAirport: "SFO",
    };
    state.view = "agents";
    state.activeMission = null;
    state.architecture = null;
    persist();
    const loginOverlay = document.getElementById("login-overlay");
    const appShell = document.querySelector(".app-shell");
    if (loginOverlay && appShell) {
      loginOverlay.hidden = false;
      appShell.hidden = true;
    }
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
    const appShell = document.querySelector(".app-shell");
    const loginOverlay = document.getElementById("login-overlay");

    attachLoginHandlers();

    // Determine if user is authenticated:
    // - They have a real user id (from OAuth or demo login)
    // - OR they came in via ?auth=demo this very load (already processed above)
    const isAuthed = state.user && state.user.id &&
      state.user.id !== "require-login";

    if (isAuthed) {
      loginOverlay.hidden = true;
      appShell.hidden = false;
      startApp();
    } else {
      loginOverlay.hidden = false;
      appShell.hidden = true;
    }
  }

  init();
})();

// Global helper for login screen provider buttons (called from inline onclick)
window.showProviderToast = function(provider) {
  const toast = document.createElement("div");
  toast.style.cssText = [
    "position:fixed","bottom:32px","left:50%","transform:translateX(-50%)",
    "background:rgba(15,20,35,0.95)","color:#e8f0fe",
    "border:1px solid rgba(255,255,255,0.15)","border-radius:12px",
    "padding:14px 24px","font-size:0.95rem","z-index:99999",
    "backdrop-filter:blur(12px)","box-shadow:0 8px 32px rgba(0,0,0,0.5)",
    "pointer-events:none","opacity:0","transition:opacity 0.3s ease"
  ].join(";");
  toast.textContent = `${provider} connect coming soon — use Demo Login to explore Dash now.`;
  document.body.appendChild(toast);
  requestAnimationFrame(() => { toast.style.opacity = "1"; });
  setTimeout(() => {
    toast.style.opacity = "0";
    setTimeout(() => toast.remove(), 400);
  }, 3200);
};

window.saveGeminiKey = async function(inputId = 'gemini-key-input', statusId = 'gemini-key-status') {
  const key = document.getElementById(inputId)?.value?.trim();
  const status = document.getElementById(statusId);
  if (!key) {
    if (status) status.textContent = 'Please enter a key or continue with demo.';
    return;
  }
  if (status) {
    status.textContent = 'Validating...';
    status.style.color = '';
  }
  try {
    const res = await fetch(`${window.location.origin}/api/set-key`, {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({gemini_api_key: key})
    });
    const data = await res.json();
    if (data.ok) {
      localStorage.setItem('dash-gemini-key', key);
      if (status) {
        status.textContent = '✅ ' + data.message;
        status.style.color = 'var(--ok)';
      }
    } else {
      if (status) {
        status.textContent = '❌ ' + data.message;
        status.style.color = 'var(--danger)';
      }
    }
  } catch (e) {
    if (status) {
      status.textContent = '❌ Network error: ' + e.message;
      status.style.color = 'var(--danger)';
    }
  }
};

window.savePartnerConfig = async function() {
  const status = document.getElementById('partner-key-status');
  if (status) {
    status.textContent = 'Saving configuration...';
    status.style.color = '';
  }

  const payload = {
    elastic_cloud_id: document.getElementById('elastic-cloud-id')?.value?.trim() || null,
    elastic_api_key: document.getElementById('elastic-api-key')?.value?.trim() || null,
    arize_api_key: document.getElementById('arize-api-key')?.value?.trim() || null,
    arize_space_id: document.getElementById('arize-space-id')?.value?.trim() || null,
    fivetran_api_key: document.getElementById('fivetran-api-key')?.value?.trim() || null,
    fivetran_api_secret: document.getElementById('fivetran-api-secret')?.value?.trim() || null,
    gitlab_token: document.getElementById('gitlab-token')?.value?.trim() || null,
    dynatrace_api_url: document.getElementById('dynatrace-api-url')?.value?.trim() || null,
    dynatrace_api_token: document.getElementById('dynatrace-api-token')?.value?.trim() || null,
    mongo_uri: document.getElementById('mongo-uri')?.value?.trim() || null,
  };

  const savedConfig = {};
  for (const [key, value] of Object.entries(payload)) {
    if (value) savedConfig[key] = value;
  }

  if (!Object.keys(savedConfig).length) {
    if (status) {
      status.textContent = 'Enter at least one partner key to save.';
      status.style.color = 'var(--danger)';
    }
    return;
  }

  try {
    const res = await fetch(`${window.location.origin}/api/set-keys`, {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify(payload),
    });
    const data = await res.json();
    if (data.ok) {
      localStorage.setItem('dash-partner-config', JSON.stringify(savedConfig));
      if (status) {
        status.textContent = '✅ Partner configuration saved for this browser session.';
        status.style.color = 'var(--ok)';
      }
    } else {
      if (status) {
        status.textContent = '❌ ' + data.message;
        status.style.color = 'var(--danger)';
      }
    }
  } catch (e) {
    if (status) {
      status.textContent = '❌ Network error: ' + e.message;
      status.style.color = 'var(--danger)';
    }
  }
};
