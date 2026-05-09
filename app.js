const brandIcons = [
    'fa-brands fa-gitlab',
    'fa-brands fa-google',
    'fa-brands fa-apple',
    'fa-brands fa-github',
    'fa-brands fa-docker',
    'fa-brands fa-slack',
    'fa-solid fa-database',
    'fa-solid fa-code-branch',
    'fa-solid fa-shield-halved',
    'fa-solid fa-magnifying-glass-chart',
    'fa-solid fa-robot',
    'fa-solid fa-lock'
];

const floatClasses = ['float-a', 'float-b', 'float-c', 'float-d'];
const API_BASE = window.DASH_API_BASE || 'http://localhost:8000';

const missionProfiles = {
    context: {
        matcher: (text) => text.includes('data context') || text.includes('google account') || text.includes('apple account') || text.includes('connect google') || text.includes('connect apple'),
        command: 'Build my data context from accounts I approve, starting with Google or Apple.',
        apiPath: '/context/intake',
        apiBody: { user_id: 'demo-user', allowed_sources: [], allowed_scopes: [] },
        statuses: [
            'Preparing consent screen...',
            'Listing account connection options...',
            'Defining minimum useful scopes...',
            'Waiting for user-approved context sources...'
        ],
        responses: [
            '<strong>Context intake ready.</strong> I can use Google, Apple, GitHub, public social links, uploads, or a short questionnaire to build your Mission Vault.',
            '<strong>Privacy checkpoint.</strong> I ask for account connections or exports, not raw passwords, and every context source gets consent, expiry, and deletion metadata.'
        ]
    },
    github: {
        matcher: (text) => text.includes('github') && (text.includes('sync') || text.includes('connect') || text.includes('import')),
        command: 'Sync my GitHub repositories into GitLab after registration.',
        apiPath: '/missions/github-sync',
        apiBody: { user_id: 'demo-user', github_connection_ready: false },
        statuses: [
            'Preparing GitHub sync handoff...',
            'Checking connection options...',
            'Mapping repository import strategy...',
            'Waiting for user-approved GitHub connection...'
        ],
        responses: [
            '<strong>GitHub sync mission staged.</strong> I can connect through OAuth, a user-provided token stored in the vault, or a browser session handoff. I will not ask for a GitHub password.',
            '<strong>Next checkpoint.</strong> Once GitHub is connected, I will enumerate repositories, ask which ones to sync, then create matching GitLab projects through the GitLab partner workflow.'
        ]
    },
    account: {
        matcher: (text) => (text.includes('amazon') || text.includes('account')) && (text.includes('make') || text.includes('create') || text.includes('sign up') || text.includes('login') || text.includes('buy')),
        command: 'Resolve whether I have an Amazon account, create one if I approve, and continue the shopping mission.',
        apiPath: '/missions/account-resolver',
        apiBody: {
            user_id: 'demo-user',
            service_name: 'Amazon',
            service_url: 'https://www.amazon.com',
            account_creation_allowed: false,
            required_action: 'shopping'
        },
        statuses: [
            'Checking the Mission Vault for account context...',
            'Preparing text-only DOM deconstruction...',
            'Mapping login or registration actions...',
            'Waiting for account connection or creation approval...'
        ],
        responses: [
            '<strong>Account Resolver ready.</strong> If you already have the account, I can use a session handoff or approved vault context. If not, I can create one after you approve.',
            '<strong>Verification guardrail.</strong> I detect CAPTCHA, MFA, and email checks, pause for you, then resume when the page state changes.'
        ]
    },
    gitlab: {
        matcher: (text) => text.includes('gitlab') || text.includes('register') || text.includes('sign up') || text.includes('account'),
        command: 'Register my GitLab account, stop for human verification if needed, then provision the mission repository.',
        apiPath: '/missions/gitlab-registration',
        apiBody: { user_id: 'demo-user', verification_completed: false },
        statuses: [
            'Opening GitLab registration...',
            'Reading the live form structure...',
            'Mapping profile fields from the Mission Vault...',
            'Filling visible fields with browser events...',
            'Submitting registration and checking state...',
            'Standing by for CAPTCHA or email verification...'
        ],
        responses: [
            '<strong>GitLab registration mission started.</strong> I found the current sign-up fields and mapped them to first name, last name, username, email, and password. Secrets stay masked.',
            '<strong>Human checkpoint ready.</strong> If GitLab presents CAPTCHA, MFA, or email confirmation, finish that prompt in the browser. After verification, I resume with GitLab MCP provisioning and mission-script sync.'
        ]
    },
    travel: {
        matcher: (text) => text.includes('flight') || text.includes('travel') || text.includes('book'),
        command: 'Find and compare travel options for my next trip.',
        statuses: [
            'Analyzing travel constraints...',
            'Opening booking surfaces...',
            'Resolving calendar and autocomplete widgets...'
        ],
        responses: [
            '<strong>Travel mission locked.</strong> I will compare flight options and ask for confirmation before any booking step.'
        ]
    },
    gift: {
        matcher: (text) => text.includes('gift') || text.includes('present') || text.includes('birthday') || text.includes('friend'),
        command: 'Buy a gift for my friend using allowed context, best price, and delivery confidence.',
        statuses: [
            'Checking what friend context you allowed...',
            'Planning social, questionnaire, and shopping sub-agents...',
            'Inferring interests and confidence levels...',
            'Scouting products, price, shipping, and seller reliability...',
            'Ranking gifts by fit, cost, novelty, and delivery confidence...'
        ],
        responses: [
            '<strong>Gift Scout activated.</strong> I can use public links, exports, or a user-approved browser session. I will not store raw Instagram or Facebook passwords.',
            '<strong>Next checkpoint.</strong> If no social context is available, I will ask for age range, occasion, budget, interests, relationship, and shipping country before recommending gifts.'
        ]
    },
    default: {
        matcher: () => true,
        command: '',
        statuses: [
            'Analyzing mission parameters...',
            'Planning tool calls...',
            'Preparing a verified action path...'
        ],
        responses: [
            '<strong>Copy.</strong> I am breaking down the task and will report back with the next safe action.'
        ]
    }
};

function initSpaceBackdrop() {
    const container = document.getElementById('space-backdrop');
    if (!container) return;

    const shuffled = [...brandIcons].sort(() => Math.random() - 0.5);
    const count = 12 + Math.floor(Math.random() * 6);

    for (let i = 0; i < count; i++) {
        const el = document.createElement('i');
        const iconClass = shuffled[i % shuffled.length];
        const floatClass = floatClasses[Math.floor(Math.random() * floatClasses.length)];

        el.className = `${iconClass} floating-icon ${floatClass}`;
        el.style.top = `${5 + Math.random() * 90}%`;
        el.style.left = `${5 + Math.random() * 90}%`;
        el.style.fontSize = `${50 + Math.random() * 120}px`;
        el.style.animationDelay = `${-(Math.random() * 30).toFixed(1)}s`;
        el.style.color = `rgba(255,255,255,${(0.04 + Math.random() * 0.08).toFixed(3)})`;

        container.appendChild(el);
    }
}

function enterDash() {
    const auth = document.getElementById('auth-screen');
    const main = document.getElementById('main-screen');

    auth.style.transition = 'opacity 0.4s ease';
    auth.style.opacity = '0';

    setTimeout(() => {
        auth.style.display = 'none';
        main.style.display = 'flex';
        main.style.opacity = '0';
        requestAnimationFrame(() => {
            main.style.transition = 'opacity 0.4s ease';
            main.style.opacity = '1';
        });
    }, 400);
}

async function registerUserContext(authProvider = 'email', authorizedSources = []) {
    const primaryEmail = authInput.value.trim() || null;
    const sourceSet = new Set(authorizedSources);
    if (authProvider === 'google') sourceSet.add('google');
    if (authProvider === 'apple') sourceSet.add('apple');

    try {
        const response = await fetch(`${API_BASE}/users/register`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                user_id: 'demo-user',
                primary_email: primaryEmail,
                auth_provider: authProvider,
                authorized_sources: [...sourceSet],
                mission_goals: ['gitlab-registration', 'gift-scout', 'travel', 'account-resolver']
            })
        });

        if (!response.ok) {
            throw new Error(`HTTP ${response.status}`);
        }

        return await response.json();
    } catch (error) {
        return { status: 'api_unavailable', error: error.message };
    }
}

async function registerAndEnter(authProvider = 'email', authorizedSources = []) {
    const result = await registerUserContext(authProvider, authorizedSources);
    enterDash();

    setTimeout(() => {
        if (result.status === 'registered') {
            addMessage(
                '<strong>Mission Vault ready.</strong> MongoDB registered your user context and Dash-1 can now route work to lightweight sub-agents.',
                'agent'
            );
        } else if (result.status === 'api_unavailable') {
            addMessage(
                '<strong>Local mode.</strong> The API is not connected, but the UI can still demonstrate the mission flow.',
                'agent'
            );
        }
    }, 650);
}

const continueBtn = document.getElementById('continue-btn');
const authInput = document.querySelector('.auth-input');
const textarea = document.getElementById('command-input');
const thread = document.getElementById('message-thread');
const statusArea = document.getElementById('status-area');
const statusText = document.getElementById('status-text');

continueBtn.addEventListener('click', () => registerAndEnter('email'));

authInput.addEventListener('keydown', (event) => {
    if (event.key === 'Enter') {
        event.preventDefault();
        registerAndEnter('email');
    }
});

textarea.addEventListener('input', function () {
    this.style.height = 'auto';
    this.style.height = `${this.scrollHeight}px`;
});

textarea.addEventListener('keydown', (event) => {
    if (event.key === 'Enter' && !event.shiftKey) {
        event.preventDefault();
        executeCommand();
    }
});

document.getElementById('execute-btn').addEventListener('click', executeCommand);

document.querySelectorAll('[data-command]').forEach((button) => {
    button.addEventListener('click', () => {
        textarea.value = button.dataset.command;
        textarea.dispatchEvent(new Event('input'));
        textarea.focus();
    });
});

document.querySelectorAll('[data-context-source]').forEach((button) => {
    button.addEventListener('click', async () => {
        const source = button.dataset.contextSource === 'apple' ? 'Apple account' : 'Google account';
        await registerAndEnter(button.dataset.contextSource, [button.dataset.contextSource]);
        setTimeout(() => {
            textarea.value = `Build my data context from my ${source} using only scopes I approve.`;
            textarea.dispatchEvent(new Event('input'));
            executeCommand();
        }, 520);
    });
});

thread.addEventListener('click', (event) => {
    const button = event.target.closest('[data-inline-command]');
    if (!button) return;
    textarea.value = button.dataset.inlineCommand;
    textarea.dispatchEvent(new Event('input'));
    executeCommand();
});

function addMessage(text, type, options = { html: true }) {
    const msg = document.createElement('div');
    msg.className = `message ${type}`;
    if (options.html) {
        msg.innerHTML = text;
    } else {
        msg.textContent = text;
    }
    thread.appendChild(msg);
    thread.scrollTop = thread.scrollHeight;
    return msg;
}

function resolveMission(raw) {
    const lower = raw.toLowerCase();
    return Object.values(missionProfiles).find((profile) => profile.matcher(lower)) || missionProfiles.default;
}

function runStatusSequence(statuses, onDone) {
    statusArea.style.display = 'flex';
    let index = 0;

    const advance = () => {
        statusText.textContent = statuses[index];
        index += 1;

        if (index < statuses.length) {
            setTimeout(advance, index === 1 ? 900 : 1200);
            return;
        }

        setTimeout(() => {
            statusArea.style.display = 'none';
            onDone();
        }, 1200);
    };

    advance();
}

async function callMissionApi(mission) {
    if (!mission.apiPath) return null;

    try {
        const response = await fetch(`${API_BASE}${mission.apiPath}`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(mission.apiBody || { user_id: 'demo-user' })
        });

        if (!response.ok) {
            throw new Error(`HTTP ${response.status}`);
        }

        return await response.json();
    } catch (error) {
        return { status: 'api_unavailable', error: error.message };
    }
}

function renderApiResult(mission, result) {
    if (!result) return;

    if (result.status === 'api_unavailable') {
        addMessage('<strong>API not connected.</strong> Start the backend on port 8000 before recording the integrated flow.', 'agent');
        return;
    }

    if (result.status === 'verification_required') {
        addMessage(
            '<strong>API orchestration checkpoint.</strong> The backend registered the mission state and is waiting for GitLab verification. After you complete it, I can continue into GitHub sync. <button class="inline-action" data-inline-command="Sync my GitHub repositories into GitLab after registration.">Sync GitHub</button>',
            'agent'
        );
        return;
    }

    if (result.status === 'needs_github_connection') {
        addMessage(
            '<strong>GitHub connection needed.</strong> Choose OAuth, a vault-stored token, or browser session handoff. Then I can list repositories and ask which ones to import into GitLab.',
            'agent'
        );
        return;
    }

    if (result.status === 'needs_repository_selection') {
        addMessage(
            '<strong>Repository selection needed.</strong> I found authorized GitHub repositories and will ask which ones to sync into GitLab.',
            'agent'
        );
        return;
    }

    if (result.status === 'needs_consent') {
        addMessage(
            '<strong>Consent needed.</strong> Choose Google, Apple, GitHub, public social links, uploads, or manual preferences. I will store only approved context in the Mission Vault.',
            'agent'
        );
        return;
    }

    if (result.status === 'needs_account_permission') {
        addMessage(
            '<strong>Account decision needed.</strong> Tell me whether to use an existing account session or create a new account for this service.',
            'agent'
        );
        return;
    }

    if (result.status === 'account_context_available' || result.status === 'ready_to_create_account') {
        addMessage(
            '<strong>Account path ready.</strong> I will use text, labels, roles, and semantic fields to operate the form, with human checkpoints for verification.',
            'agent'
        );
        return;
    }

    if (result.status === 'success' || result.status === 'ready_to_sync' || result.status === 'context_ready') {
        addMessage('<strong>Mission ready.</strong> The backend API accepted the mission and prepared the next action.', 'agent');
    }
}

function executeCommand() {
    const raw = textarea.value.trim();
    if (!raw) return;

    const mission = resolveMission(raw);

    addMessage(raw, 'user', { html: false });
    textarea.value = '';
    textarea.style.height = 'auto';

    runStatusSequence(mission.statuses, async () => {
        const result = await callMissionApi(mission);
        mission.responses.forEach((response, index) => {
            setTimeout(() => addMessage(response, 'agent'), index * 650);
        });
        setTimeout(() => renderApiResult(mission, result), mission.responses.length * 650 + 250);
    });
}

document.addEventListener('DOMContentLoaded', initSpaceBackdrop);
