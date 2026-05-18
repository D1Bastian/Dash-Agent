/* --- CONFIG ------------------------------- */
const API_BASE = window.DASH_API_BASE || 'http://localhost:8000';
const ICONS = ['fa-brands fa-gitlab','fa-brands fa-google','fa-brands fa-apple','fa-brands fa-github','fa-solid fa-database','fa-solid fa-robot','fa-solid fa-shield-halved','fa-solid fa-gift','fa-solid fa-plane','fa-brands fa-docker','fa-solid fa-magnifying-glass-chart','fa-solid fa-lock'];
const FLOAT = ['float-a','float-b','float-c','float-d'];
let currentView = 'home';

/* --- SPACE BACKDROP ----------------------- */
function initBackdrop() {
  const el = document.getElementById('space-backdrop');
  if (!el) return;
  const shuffled = [...ICONS].sort(() => Math.random() - 0.5);
  for (let i = 0; i < 14; i++) {
    const icon = document.createElement('i');
    icon.className = `${shuffled[i % shuffled.length]} floating-icon ${FLOAT[i % 4]}`;
    icon.style.cssText = `top:${5 + Math.random()*88}%;left:${5 + Math.random()*88}%;font-size:${48 + Math.random()*110}px;animation-delay:-${(Math.random()*30).toFixed(1)}s;color:rgba(255,255,255,${(0.03+Math.random()*0.07).toFixed(3)})`;
    el.appendChild(icon);
  }
}

/* --- SCREEN TRANSITIONS ------------------- */
function showScreen(id) {
  document.querySelectorAll('.screen').forEach(s => { s.classList.remove('active'); s.style.display = 'none'; });
  const s = document.getElementById(id);
  s.style.display = (id === 'screen-dashboard') ? 'flex' : 'flex';
  requestAnimationFrame(() => s.classList.add('active'));
}

/* --- AUTH --------------------------------- */
async function registerUser(provider = 'email') {
  const email = (document.getElementById('auth-input') || {}).value || '';
  try {
    await fetch(`${API_BASE}/users/register`, { method: 'POST', headers: authHeaders(),, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ user_id: 'demo-user', primary_email: email, auth_provider: provider, mission_goals: ['gift-scout','travel','account-resolver','social-manager'] })
    });
  } catch (_) {}
}

function goToConsent(provider) {
  registerUser(provider);
  showScreen('screen-consent');
}

function goToDashboard() {
  updateUserDisplay();
  showScreen('screen-dashboard');
  setTimeout(() => addMessage('<strong>Mission Vault ready.</strong> MongoDB has your context. What\'s the mission today?', 'agent'), 700);
}

document.getElementById('btn-continue').addEventListener('click', () => goToConsent('email'));
document.getElementById('auth-input').addEventListener('keydown', e => { if (e.key === 'Enter') goToConsent('email'); });
document.querySelectorAll('[data-provider]').forEach(b => b.addEventListener('click', () => { goToConsent(b.dataset.provider); setTimeout(() => { const inp = document.getElementById('auth-input'); if(inp) inp.value = `Build context from my ${b.dataset.provider} account`; }, 600); }));
document.getElementById('btn-grant-consent').addEventListener('click', startGoogleOAuth);
document.getElementById('btn-skip-consent').addEventListener('click', () => goToDashboard());

/* --- SIDEBAR NAV -------------------------- */
function switchView(viewName) {
  currentView = viewName;
  document.querySelectorAll('.view').forEach(v => v.style.display = 'none');
  document.querySelectorAll('.nav-item').forEach(n => n.classList.remove('active'));
  const view = document.getElementById(`view-${viewName}`);
  if (view) view.style.display = 'flex';
  const navBtn = document.getElementById(`nav-${viewName}`);
  if (navBtn) navBtn.classList.add('active');
}
document.querySelectorAll('[data-view]').forEach(b => b.addEventListener('click', () => switchView(b.dataset.view)));

/* --- MISSION PROFILES --------------------- */
const missions = {
  gift: {
    match: t => t.includes('gift') || t.includes('nephew') || t.includes('trinidad') || t.includes('present'),
    phases: ['Finding vendors that ship to Trinidad...','Reading product pages & stripping DOM fluff...','Comparing prices across Amazon, eBay & Etsy...','Building ranked shortlist — stopping before checkout...','Saving options to Mission Vault...'],
    responses: [
      '<strong>Gift Scout activated.</strong> I found 3 vendors that ship to Trinidad. Checking social context from vault for interest signals.',
      '<strong>Top picks ready.</strong> Ranked by interest fit, price, delivery time & seller reliability. I\'ll stop here for your approval before any purchase.',
      '<button class="inline-action" data-inline-command="Approve the top gift and proceed to checkout.">Approve Top Pick</button>'
    ]
  },
  travel: {
    match: t => t.includes('flight') || t.includes('travel') || t.includes('hotel') || t.includes('book') || t.includes('airbnb'),
    phases: ['Spawning 3 Travel Scout sub-agents...','Scout-1: reading Expedia flight DOM...','Scout-2: parsing Booking.com hotel rates...','Scout-3: checking Airbnb availability...','Synthesizing best package combinations...'],
    responses: [
      '<strong>Travel Concierge running.</strong> 3 parallel scouts launched — flights, hotels, Airbnb. Comparing real-time dates & rates.',
      '<strong>Best window found:</strong> Flights are 18% cheaper mid-week. Hotel + flight bundle saves ~$240 vs separate bookings.',
      'Ready to book? I\'ll handle checkout, passenger details & save the itinerary to your vault. <button class="inline-action" data-inline-command="Book the best travel package.">Book It</button>'
    ]
  },
  account: {
    match: t => t.includes('account') || t.includes('register') || t.includes('sign up') || t.includes('create'),
    phases: ['Checking Mission Vault for existing accounts...','Navigating to registration surface...','Mapping accessible form fields via ARIA labels...','Filling fields with browser keyboard events...','Stopping for CAPTCHA / email verification...'],
    responses: [
      '<strong>Account Resolver running.</strong> No existing account found in vault. Starting registration with accessible form mapping.',
      '?? <strong>CAPTCHA detected.</strong> Please complete it in the browser — I\'ll resume automatically after.'
    ]
  },
  social: {
    match: t => t.includes('post') || t.includes('social') || t.includes('instagram') || t.includes('twitter') || t.includes('content'),
    phases: ['Loading social context from vault...','Brainstorming content ideas with Gemini...','Drafting posts for your approval...','Scheduling approved content...','Saving workflow state to vault...'],
    responses: [
      '<strong>Social Manager activated.</strong> I\'ve drafted 3 post ideas based on your past content. Review & approve before publishing.',
      'Want to set up a <strong>permanent workflow</strong>? I can post automatically on a schedule. <button class="inline-action" data-inline-command="Create a social media workflow.">Set Up Workflow</button>'
    ]
  },
  default: {
    match: () => true,
    phases: ['Analyzing mission parameters...','Planning tool calls...','Routing to sub-agents...'],
    responses: ['<strong>Copy.</strong> Breaking down the task — I\'ll report back with the next safe action step.']
  }
};

function resolveMission(text) {
  const t = text.toLowerCase();
  return Object.values(missions).find(m => m.match(t)) || missions.default;
}

/* --- MESSAGE THREAD ----------------------- */
const thread = document.getElementById('message-thread');
function addMessage(html, type = 'agent') {
  const div = document.createElement('div');
  div.className = `message ${type}`;
  div.innerHTML = html;
  thread.appendChild(div);
  thread.scrollTop = thread.scrollHeight;
  const cards = document.getElementById('mission-cards');
  if (cards && thread.children.length > 0) cards.style.display = 'none';
  return div;
}

/* --- PHASE CYCLING ------------------------ */
const phaseIds = ['phase-find','phase-read','phase-type','phase-check','phase-save'];
function runPhases(phases, onDone) {
  const statusArea = document.getElementById('status-area');
  const statusText = document.getElementById('status-text');
  statusArea.style.display = 'flex';
  phaseIds.forEach(id => { const el = document.getElementById(id); if(el) { el.classList.remove('active','done'); } });
  document.getElementById('phase-find').classList.add('active');
  let i = 0;
  const step = () => {
    if (statusText) statusText.textContent = phases[i] || 'Working...';
    const phaseEl = document.getElementById(phaseIds[i]);
    if (phaseEl) { phaseEl.classList.remove('active'); phaseEl.classList.add('done'); }
    const next = document.getElementById(phaseIds[i + 1]);
    if (next) next.classList.add('active');
    i++;
    if (i < phases.length) { setTimeout(step, 1100); return; }
    setTimeout(() => { statusArea.style.display = 'none'; onDone(); }, 1000);
  };
  setTimeout(step, 900);
}

/* --- EXECUTE ------------------------------ */
const textarea = document.getElementById('command-input');
const executeBtn = document.getElementById('execute-btn');

function executeCommand() {
  const raw = textarea.value.trim();
  if (!raw) return;
  addMessage(raw, 'user');
  textarea.value = '';
  textarea.style.height = 'auto';
  const mission = resolveMission(raw);
  runPhases(mission.phases, () => {
    mission.responses.forEach((r, idx) => setTimeout(() => addMessage(r, 'agent'), idx * 700));
  });
}

executeBtn.addEventListener('click', executeCommand);
textarea.addEventListener('keydown', e => { if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); executeCommand(); } });
textarea.addEventListener('input', function() { this.style.height = 'auto'; this.style.height = this.scrollHeight + 'px'; });

/* --- MISSION CARD SHORTCUTS --------------- */
const missionPrompts = {
  gift: "I want to send a gift to my nephew in Trinidad. He's on social media — find suggestions and best prices.",
  travel: "Find me the best flights, hotels and Airbnb deals. I want the cheapest dates and package combos.",
  account: "Create a new account for me and save it securely to the Mission Vault.",
  social: "Draft 3 Instagram posts for me and set up an automated posting schedule."
};
document.querySelectorAll('[data-mission]').forEach(card => {
  card.addEventListener('click', () => {
    textarea.value = missionPrompts[card.dataset.mission] || '';
    textarea.dispatchEvent(new Event('input'));
    executeCommand();
  });
});

/* --- INLINE BUTTON DELEGATION ------------- */
thread.addEventListener('click', e => {
  const btn = e.target.closest('[data-inline-command]');
  if (!btn) return;
  textarea.value = btn.dataset.inlineCommand;
  executeCommand();
});

/* --- WORKFLOW MODAL ----------------------- */
const wfModal = document.getElementById('modal-workflow');
['btn-new-workflow','btn-create-workflow'].forEach(id => {
  const el = document.getElementById(id);
  if (el) el.addEventListener('click', () => { wfModal.style.display = 'flex'; });
});
['btn-close-wf-modal','btn-close-wf-modal-2'].forEach(id => {
  const el = document.getElementById(id);
  if (el) el.addEventListener('click', () => { wfModal.style.display = 'none'; });
});
const wfNext = document.getElementById('btn-wf-next');
if (wfNext) {
  wfNext.addEventListener('click', () => {
    const input = document.getElementById('wf-brainstorm-input').value.trim();
    if (!input) return;
    wfModal.style.display = 'none';
    switchView('home');
    textarea.value = input;
    executeCommand();
  });
}

/* --- HITL MODAL --------------------------- */
const hitlModal = document.getElementById('modal-hitl');
const hitlApprove = document.getElementById('btn-hitl-approve');
const hitlDeny = document.getElementById('btn-hitl-deny');
if (hitlApprove) hitlApprove.addEventListener('click', () => { hitlModal.style.display = 'none'; addMessage('<strong>Approved.</strong> Continuing mission...', 'agent'); });
if (hitlDeny) hitlDeny.addEventListener('click', () => { hitlModal.style.display = 'none'; addMessage('<strong>Mission paused.</strong> Standing by for your direction.', 'agent'); });

/* --- INIT --------------------------------- */
document.addEventListener('DOMContentLoaded', () => {
  initBackdrop();
  if (parseOAuthRedirect()) {
    goToDashboard();
  } else if (session.accessToken) {
    updateUserDisplay();
    goToDashboard();
  } else {
    showScreen('screen-auth');
  }
  switchView('home');
});

