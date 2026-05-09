// ═══════════════════════════════════════════════
// DASH AI — Dynamic Space Backdrop + Agent Logic
// ═══════════════════════════════════════════════

const brandIcons = [
    'fa-brands fa-amazon',
    'fa-brands fa-gitlab',
    'fa-brands fa-apple',
    'fa-brands fa-google',
    'fa-brands fa-paypal',
    'fa-brands fa-stripe',
    'fa-brands fa-shopify',
    'fa-brands fa-airbnb',
    'fa-brands fa-twitter',
    'fa-brands fa-facebook',
    'fa-brands fa-spotify',
    'fa-brands fa-github',
    'fa-brands fa-slack',
    'fa-brands fa-dropbox',
    'fa-brands fa-figma'
];

const floatClasses = ['float-a', 'float-b', 'float-c', 'float-d'];

function initSpaceBackdrop() {
    const container = document.getElementById('space-backdrop');
    if (!container) return;

    // Shuffle and pick a random subset each load
    const shuffled = [...brandIcons].sort(() => Math.random() - 0.5);
    const count = 12 + Math.floor(Math.random() * 6); // 12–17 icons

    for (let i = 0; i < count; i++) {
        const el = document.createElement('i');
        const iconClass = shuffled[i % shuffled.length];
        const floatClass = floatClasses[Math.floor(Math.random() * floatClasses.length)];

        el.className = `${iconClass} floating-icon ${floatClass}`;

        // Scatter across the full viewport
        el.style.top = `${5 + Math.random() * 90}%`;
        el.style.left = `${5 + Math.random() * 90}%`;

        // Varied sizes for depth
        const size = 50 + Math.random() * 120;
        el.style.fontSize = `${size}px`;

        // Stagger start so they don't all move in sync
        el.style.animationDelay = `${-(Math.random() * 30).toFixed(1)}s`;

        // Slightly varied opacity for parallax depth
        el.style.color = `rgba(255,255,255,${(0.04 + Math.random() * 0.08).toFixed(3)})`;

        container.appendChild(el);
    }
}

// ═══════════════════════════════════
// AUTH → MAIN TRANSITION
// ═══════════════════════════════════

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

document.getElementById('continue-btn').addEventListener('click', enterDash);

// Enter key on email input
document.querySelector('.auth-input').addEventListener('keydown', (e) => {
    if (e.key === 'Enter') { e.preventDefault(); enterDash(); }
});

// ═══════════════════════════════════
// COMMAND EXECUTION
// ═══════════════════════════════════

const textarea = document.getElementById('command-input');
const thread = document.getElementById('message-thread');
const statusArea = document.getElementById('status-area');
const statusText = document.getElementById('status-text');

// Auto-expand textarea
textarea.addEventListener('input', function () {
    this.style.height = 'auto';
    this.style.height = this.scrollHeight + 'px';
});

textarea.addEventListener('keydown', (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        executeCommand();
    }
});

document.getElementById('execute-btn').addEventListener('click', executeCommand);

function addMessage(text, type) {
    const msg = document.createElement('div');
    msg.className = `message ${type}`;
    msg.innerHTML = text;
    thread.appendChild(msg);
    thread.scrollTop = thread.scrollHeight;
    return msg;
}

function executeCommand() {
    const raw = textarea.value.trim();
    if (!raw) return;

    addMessage(raw, 'user');
    textarea.value = '';
    textarea.style.height = 'auto';

    // Show status
    statusArea.style.display = 'flex';
    statusText.textContent = 'Analyzing mission parameters…';

    setTimeout(() => {
        statusText.textContent = 'Orchestrating sub-agents…';

        setTimeout(() => {
            statusArea.style.display = 'none';

            const lower = raw.toLowerCase();
            let response;

            if (lower.includes('flight') || lower.includes('travel') || lower.includes('book')) {
                response = `<strong>Mission locked.</strong> Deploying browser agents to Expedia, Skiplagged, and Google Flights. I'll surface the best options and confirm before booking.`;
            } else if (lower.includes('ship') || lower.includes('send') || lower.includes('gift')) {
                response = `<strong>Logistics pipeline activated.</strong> Evaluating TriniBox, Amazon Global, and FedEx rates for your destination. Stand by for quotes.`;
            } else if (lower.includes('register') || lower.includes('sign up') || lower.includes('account')) {
                response = `<strong>Provisioning initiated.</strong> I'll handle the registration flow autonomously. If a CAPTCHA appears, I'll hand control to you.`;
            } else {
                response = `<strong>Copy.</strong> Breaking down the task now. I'll report back with a plan before executing.`;
            }

            addMessage(response, 'agent');
        }, 1800);
    }, 1200);
}

// ═══════════════════════════════════
// INIT
// ═══════════════════════════════════

document.addEventListener('DOMContentLoaded', initSpaceBackdrop);
