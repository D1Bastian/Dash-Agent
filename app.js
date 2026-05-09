document.getElementById('continue-btn').addEventListener('click', () => {
    document.getElementById('auth-screen').style.display = 'none';
    document.getElementById('main-screen').style.display = 'flex';
});

function addMessage(text, side) {
    const thread = document.getElementById('message-thread');
    
    // Remove typing indicator if exists
    const existingTyping = document.querySelector('.typing-indicator');
    if (existingTyping) existingTyping.remove();

    const msg = document.createElement('div');
    msg.className = `message-bubble ${side}`;
    msg.textContent = text;
    thread.appendChild(msg);
    thread.scrollTop = thread.scrollHeight;
}

function showTyping() {
    const thread = document.getElementById('message-thread');
    const typing = document.createElement('div');
    typing.className = 'message-bubble agent typing-indicator';
    typing.innerHTML = '<span class="dot"></span><span class="dot"></span><span class="dot"></span>';
    thread.appendChild(typing);
    thread.scrollTop = thread.scrollHeight;
}

document.getElementById('execute-btn').addEventListener('click', () => {
    const input = document.getElementById('command-input');
    const query = input.value.trim();
    if (!query) return;

    addMessage(query, 'user');
    input.value = '';
    
    if (threadState === 'initial') {
        handleClarification(query);
    } else if (threadState === 'clarified') {
        handleConfirmation(query);
    }
});

function handleClarification(query) {
    threadState = 'processing';
    showTyping();
    
    setTimeout(() => {
        if (query.includes('trinidad') || query.includes('book')) {
            addMessage("Gemini: I see you want to send a book to Trinidad. My Elastic Search engine indicates that while Amazon is available, 'Aeropost' or 'TriniBox' offer 30% faster delivery and lower customs rates for this region. Would you like to use your Amazon account or should I create an optimized account on TriniBox for you?", 'agent');
            threadState = 'platform_choice';
        } else if (query.includes('flight') || query.includes('tokyo')) {
            addMessage("Gemini: Searching for optimized flight paths to Tokyo. I've found a deal on 'Expedia' for $842, but 'Skiplagged' has a hidden-city fare for $610. Which platform would you like me to execute the booking on?", 'agent');
            threadState = 'platform_choice';
        } else {
            addMessage("Gemini: I've analyzed your request. To fulfill this mission with zero-failure, I'm spinning up a specialized subagent to deconstruct the relevant web service. Please stand by while I map the DOM...", 'agent');
            setTimeout(() => {
                addMessage("Subagent 01-WK: Target identified. Requesting clarification on your preferred budget constraints.", 'agent');
                threadState = 'clarified';
            }, 2000);
        }
    }, 1500);
}

function handleConfirmation(query) {
    threadState = 'processing';
    const useAmazon = query.toLowerCase().includes('amazon');
    const platform = useAmazon ? 'Amazon Global' : 'TriniBox (Optimized)';
    
    setTimeout(() => {
        const thread = document.getElementById('message-thread');
        const card = document.createElement('div');
        card.className = 'confirmation-card';
        card.innerHTML = `
            <h4>MISSION PLAN: LOGISTICS-TRINIDAD</h4>
            <div class="plan-item"><span class="plan-icon">◈</span> ${useAmazon ? 'Accessing Amazon Vault' : 'Provisioning New TriniBox Account'}</div>
            <div class="plan-item"><span class="plan-icon">◈</span> Sourcing 'The Alchemist' via ${platform}</div>
            <div class="plan-item"><span class="plan-icon">◈</span> Auto-calculating Customs & Duties (Fivetran Pipeline)</div>
            <button class="auth-btn primary" id="final-confirm" style="margin-top: 10px;">Execute Mission</button>
        `;
        thread.appendChild(card);
        thread.scrollTop = thread.scrollHeight;

        document.getElementById('final-confirm').addEventListener('click', () => {
            card.innerHTML = `<div class="status-indicator" style="margin: 0;"><div class="spinner"></div><span>ORCHESTRA is executing background form-filling on ${platform}...</span></div>`;
            setTimeout(() => {
                card.innerHTML = `<span style="color: #0071e3; font-weight: 600;">✓ Mission Complete.</span> Account created/accessed and items shipped. Syncing results to MongoDB.`;
            }, 5000);
        });
    }, 1500);
}

document.getElementById('command-input').addEventListener('input', function() {
    this.style.height = 'auto';
    this.style.height = (this.scrollHeight) + 'px';
});

document.getElementById('command-input').addEventListener('keydown', (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        document.getElementById('execute-btn').click();
    }
});

// Quick action chips
document.querySelectorAll('.action-chip').forEach(chip => {
    chip.addEventListener('click', () => {
        const text = chip.textContent.split(' ').slice(1).join(' ');
        document.getElementById('command-input').value = `I want to ${text.toLowerCase()}...`;
        document.getElementById('command-input').focus();
    });
});
