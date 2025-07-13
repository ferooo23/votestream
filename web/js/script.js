const $ = sel => document.querySelector(sel);
const api = async (url, m = "GET", body) => {
    try {
        const response = await fetch(url, {
            method: m,
            headers: { 'Content-Type': 'application/json' },
            body: body && JSON.stringify(body)
        });
        
        if (response.status === 429) {
            throw new Error('Rate limit exceeded');
        }
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        return await response.json();
    } catch (error) {
        console.error('API Error:', error);
        throw error;
    }
};

// Global variables for optimization
let currentWebSocket = null;
let votingInProgress = false;
let pollCache = new Map();
let lastVoteTime = 0;
let pollingInterval = null;

// Mock data organized by themes
const mockThemes = {
    "OnTrend": {
        name: "#OnTrend",
        slug: "on-trend",
        description: "The hottest topics of the moment. From technology and social media to the latest releases everyone's talking about. Vote and discover if you think like the majority!",
        color: "#ff6b6b",
        icon: "🔥",
        polls: [
            // ... (poll data remains the same)
        ]
    },
    "MoralDilemmas": {
        name: "Moral Dilemmas",
        slug: "moral-dilemmas",
        description: "Difficult questions with no right answer. Test your principles and discover how the world would react to these extreme situations.",
        color: "#4ecdc4",
        icon: "🤔",
        polls: [
             // ... (poll data remains the same)
        ]
    },
    "Sports": {
        name: "⚽ Sports",
        slug: "sports",
        description: "The boldest predictions from the world of sports. Will you nail your forecasts?",
        color: "#45b7d1",
        icon: "⚽",
        polls: [
             // ... (poll data remains the same)
        ]
    }
};

// Convert themes to flat array of polls for compatibility
const mockPolls = [];
Object.values(mockThemes).forEach(theme => {
    mockPolls.push(...theme.polls);
});

let currentTheme = null;
let currentView = 'themes'; // 'themes', 'polls', 'vote'

// Function to load themes (new main view)
async function loadThemes() {
    try {
        const themes = await api('/themes');
        renderThemes(themes);
    } catch (error) {
        console.log('Backend not available, using mock themes');
        renderThemes(mockThemes);
    }
}

// Function to render themes view
function renderThemes(themes) {
    currentView = 'themes';
    const container = document.getElementById('main-content');
    
    container.innerHTML = `
        <div class="hero-section">
            <h1 class="hero-title">
                <span class="gradient-text">Vote</span><span class="highlight">Stream</span>
            </h1>
            <p class="hero-subtitle">An honest corner to share opinions and discover perspectives</p>
        </div>
        
        <div class="themes-grid">
            ${Object.entries(themes).map(([key, theme]) => `
                <div class="theme-card" data-theme="${key}" style="--theme-color: ${theme.color}">
                    <div class="theme-icon">${theme.icon}</div>
                    <h3 class="theme-name">${theme.name}</h3>
                    <p class="theme-description">${theme.description}</p>
                    <div class="theme-stats">
                        ${theme.poll_count || theme.polls?.length || 0} active polls
                    </div>
                    <div class="theme-overlay">
                        <button class="explore-btn">Explore theme</button>
                    </div>
                </div>
            `).join('')}
        </div>
    `;
}

// Function to load polls for a specific theme
async function loadThemePolls(themeKey) {
    currentView = 'polls';
    currentTheme = themeKey;
    
    try {
        const polls = await api(`/themes/${themeKey}/polls`);
        const themes = await api('/themes');
        const theme = themes[themeKey] || mockThemes[themeKey];
        
        renderThemePolls(theme, polls);
    } catch (error) {
        console.log('Backend not available, using mock polls');
        const theme = mockThemes[themeKey];
        renderThemePolls(theme, theme.polls);
    }
}

// Function to render theme polls
function renderThemePolls(theme, polls) {
    const container = document.getElementById('main-content');
    container.innerHTML = `
        <div class="theme-header" style="--theme-color: ${theme.color}">
            <button class="back-btn" onclick="loadThemes()">← Back to themes</button>
            <div class="theme-info">
                <span class="theme-icon-large">${theme.icon}</span>
                <div>
                    <h2 class="theme-title">${theme.name}</h2>
                    <p class="theme-desc">${theme.description}</p>
                </div>
            </div>
        </div>
        
        <div class="polls-grid">
            ${polls.map((poll, index) => `
                <div class="poll-card-modern" data-id="${poll.id}" style="--delay: ${index * 0.1}s">
                    <div class="poll-number">#${index + 1}</div>
                    <h3 class="poll-question">${poll.question}</h3>
                    <div class="poll-options-preview">
                        ${poll.options.map(opt => `<span class="option-chip">${opt.text}</span>`).join('')}
                    </div>
                    <button class="vote-btn-modern">
                        <span>Vote now</span>
                        <div class="btn-particles"></div>
                    </button>
                </div>
            `).join('')}
        </div>
    `;
}

async function loadPolls() {
    loadThemes();
}

function updateOptionFields() {
    const selectElement = document.getElementById('option-count');
    const count = parseInt(selectElement.value);
    
    const container = document.getElementById('options-container');
    if (!container) return;
    
    container.innerHTML = '';
    
    for (let i = 0; i < count; i++) {
        const div = document.createElement('div');
        div.innerHTML = `
            <label for="option-${i}">Option ${i + 1}</label>
            <input id="option-${i}" placeholder="Option ${String.fromCharCode(65 + i)}" required>
        `;
        container.appendChild(div);
    }
}

function startPollingResults(pollId) {
    if (pollingInterval) clearInterval(pollingInterval);
    
    pollingInterval = setInterval(async () => {
        try {
            const results = await api(`/polls/${pollId}/results`);
            const resultsElem = $('#results');
            if (resultsElem) {
                resultsElem.textContent = JSON.stringify(results, null, 2);
                resultsElem.classList.add('results-updated');
                setTimeout(() => resultsElem.classList.remove('results-updated'), 300);
            }
        } catch (error) {
            // If rate limited, just skip this poll and try again later
            if (error.message && error.message.includes('Rate limit')) {
                console.log('Rate limited, skipping poll cycle');
                return;
            }
            console.error('Error polling results:', error);
        }
    }, 10000); // Increased from 3000ms to 10000ms (10 seconds)
}

function stopPolling() {
    if (pollingInterval) {
        clearInterval(pollingInterval);
        pollingInterval = null;
    }
}

function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

document.addEventListener('DOMContentLoaded', function() {
    updateOptionFields();
    loadPolls();
    
    const form = document.getElementById('new');
    if (form) {
        form.addEventListener('submit', async (e) => {
            e.preventDefault();
            const q = document.getElementById('q').value.trim();
            const theme = document.getElementById('theme-select').value;
            const count = parseInt(document.getElementById('option-count').value);
            
            if (!q) return showToast('Question is required', 'error');
            if (!theme) return showToast('Select a theme for the poll', 'error');
            
            const options = [];
            for (let i = 0; i < count; i++) {
                const optionInput = document.getElementById(`option-${i}`);
                if (!optionInput) return showToast(`Field for option ${i + 1} not found`, 'error');
                const optionText = optionInput.value.trim();
                if (!optionText) return showToast(`Option ${i + 1} is required`, 'error');
                options.push({ text: optionText });
            }
            
            const submitBtn = document.getElementById('submit-btn');
            if (submitBtn.disabled) return;
            
            submitBtn.disabled = true;
            submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Creating...';
            
            try {
                await api('/polls','POST',{question:q,theme:theme,options:options});
                form.reset();
                updateOptionFields();
                
                if (currentView === 'polls' && currentTheme === theme) {
                    loadThemePolls(theme);
                } else {
                    loadThemes();
                }
                
                showToast('Poll created successfully!');
            } catch (error) {
                console.error('Error creating poll:', error);
                showToast('Error creating poll', 'error');
            } finally {
                submitBtn.disabled = false;
                submitBtn.innerHTML = 'Create';
            }
        });
    }
    
    const mainContent = document.getElementById('main-content');
    if (mainContent) {
        mainContent.addEventListener('click', async (e) => {
            const themeCard = e.target.closest('.theme-card');
            if (themeCard) {
                const themeKey = themeCard.dataset.theme;
                loadThemePolls(themeKey);
                return;
            }
            
            const pollCard = e.target.closest('.poll-card-modern');
            if (pollCard) {
                const id = parseInt(pollCard.dataset.id);
                showVotingInterface(id);
                return;
            }
        });
    }
});

function closeCurrentWebSocket() {
    if (currentWebSocket) {
        currentWebSocket.close();
        currentWebSocket = null;
    }
    stopPolling();
}

const mockResults = {
    1: { "React": 25, "Vue.js": 18, "Angular": 12 },
    2: { "PostgreSQL": 30, "MongoDB": 22, "MySQL": 15, "SQLite": 8 }
};

let votedPolls = new Set();

const handleVote = debounce(async (pollId, choiceIndex) => {
    if (votingInProgress) return;
    
    const now = Date.now();
    if (now - lastVoteTime < 1000) {
        return showToast('Wait a moment before voting again', 'warning');
    }
    
    votingInProgress = true;
    lastVoteTime = now;
    
    try {
        await api(`/polls/${pollId}/vote`, 'POST', {choice: choiceIndex});
        showToast('Vote registered!');
        
        try {
            const updatedResults = await api(`/polls/${pollId}/results`);
            const resultsElem = document.getElementById('results');
            resultsElem.textContent = JSON.stringify(updatedResults, null, 2);
            resultsElem.classList.add('results-updated');
            setTimeout(() => resultsElem.classList.remove('results-updated'), 300);
        } catch (error) {
            console.error('Error updating results after vote:', error);
        }
        
    } catch (error) {
        console.log('Backend not available, simulating vote');
        
        if (votedPolls.has(pollId)) {
            return showToast('You have already voted on this poll (demo)', 'warning');
        }
        
        votedPolls.add(pollId);
        
        const button = document.getElementById(`opt${choiceIndex}`);
        if (button) {
            button.classList.add('voted');
            button.textContent += ' ✓';
        }
        
        const results = mockResults[pollId];
        if (results) {
            const poll = mockPolls.find(p => p.id == pollId);
            if (poll && poll.options[choiceIndex]) {
                const optionText = poll.options[choiceIndex].text;
                results[optionText] = (results[optionText] || 0) + 1;
            }
            
            const resultsElem = document.getElementById('results');
            resultsElem.textContent = JSON.stringify(results, null, 2);
            resultsElem.classList.add('results-updated');
            setTimeout(() => resultsElem.classList.remove('results-updated'), 300);
        }
        
        showToast('Vote registered! (demo mode)');
    } finally {
        votingInProgress = false;
    }
}, 300);

function createVoteButtons(poll) {
    const container = $('#options-container-vote');
    container.innerHTML = '';
    
    poll.options.forEach((option, index) => {
        const button = document.createElement('button');
        button.className = 'vote-option-btn';
        button.id = `opt${index}`;
        button.textContent = option.text;
        button.onclick = () => handleVote(poll.id, index);
        container.appendChild(button);
    });
}

async function showVotingInterface(pollId) {
    currentView = 'vote';
    let poll;

    try {
        poll = await api(`/polls/${pollId}`);
    } catch (error) {
        poll = mockPolls.find(p => p.id == pollId);
        if (!poll) {
            showToast('Poll not found', 'error');
            return;
        }
    }
    
    const theme = Object.values(mockThemes).find(t => t.polls.some(p => p.id == pollId));
    const container = document.getElementById('main-content');
    
    container.innerHTML = `
        <div class="vote-header" style="--theme-color: ${theme?.color || '#4361ee'}">
            <button class="back-btn" onclick="loadThemePolls('${currentTheme}')">← Back to ${theme?.name || 'polls'}</button>
            <div class="vote-progress">
                <div class="progress-bar">
                    <div class="progress-fill" style="width: 33%"></div>
                </div>
                <span class="progress-text">Step 1 of 3</span>
            </div>
        </div>
        
        <div class="vote-container">
            <div class="vote-question-card">
                <h2 class="vote-question">${poll.question}</h2>
                <p class="vote-instruction">Select your answer:</p>
            </div>
            
            <div class="vote-options-modern" id="vote-options-container">
                ${poll.options.map((option, index) => `
                    <div class="vote-option-modern" data-index="${index}" style="--delay: ${index * 0.1}s">
                        <div class="option-content">
                            <span class="option-letter">${String.fromCharCode(65 + index)}</span>
                            <span class="option-text">${option.text}</span>
                        </div>
                        <div class="option-hover-effect"></div>
                    </div>
                `).join('')}
            </div>
            
            <div class="vote-results-container" id="vote-results" style="display: none;">
                <h3>Real-time results:</h3>
                <div id="results-chart"></div>
                <pre id="results-data"></pre>
            </div>
        </div>
    `;
    
    setupVoteOptionListeners(poll);
    loadVoteResults(pollId);
}

function setupVoteOptionListeners(poll) {
    const container = document.getElementById('vote-options-container');
    container.addEventListener('click', (e) => {
        const option = e.target.closest('.vote-option-modern');
        if (option) {
            const index = parseInt(option.dataset.index);
            handleModernVote(poll.id, index, poll.options[index].text);
        }
    });
}

async function handleModernVote(pollId, choiceIndex, optionText) {
    if (votingInProgress) return;
    
    if (votedPolls.has(pollId)) {
        return showToast('You have already voted on this poll', 'warning');
    }
    
    votingInProgress = true;
    votedPolls.add(pollId);
    
    const selectedOption = document.querySelector(`[data-index="${choiceIndex}"]`);
    selectedOption.classList.add('selected');
    
    document.querySelectorAll('.vote-option-modern').forEach(opt => {
        if (opt !== selectedOption) {
            opt.classList.add('disabled');
        }
    });
    
    try {
        await api(`/polls/${pollId}/vote`, 'POST', {choice: choiceIndex});
        showToast('Vote registered!');
    } catch (error) {
        console.log('Backend not available, simulating vote');
        
        const results = mockResults[pollId] || {};
        results[optionText] = (results[optionText] || 0) + 1;
        mockResults[pollId] = results;
        
        showToast('Vote registered! (demo mode)');
    }
    
    setTimeout(() => {
        document.getElementById('vote-results').style.display = 'block';
        document.getElementById('vote-results').scrollIntoView({behavior: 'smooth'});
        loadVoteResults(pollId);
    }, 1000);
    
    votingInProgress = false;
}

async function loadVoteResults(pollId) {
    try {
        const results = await api(`/polls/${pollId}/results`);
        displayResults(results);
    } catch (error) {
        const results = mockResults[pollId] || {};
        displayResults(results);
    }
}

function displayResults(results) {
    const total = Object.values(results).reduce((sum, count) => sum + count, 0);
    const chartContainer = document.getElementById('results-chart');
    const dataContainer = document.getElementById('results-data');
    
    if (total === 0) {
        chartContainer.innerHTML = '<p class="no-votes">Be the first to vote!</p>';
        return;
    }
    
    chartContainer.innerHTML = Object.entries(results).map(([option, count]) => {
        const percentage = ((count / total) * 100).toFixed(1);
        return `
            <div class="result-bar">
                <div class="result-label">
                    <span>${option}</span>
                    <span>${count} votes (${percentage}%)</span>
                </div>
                <div class="result-progress">
                    <div class="result-fill" style="width: ${percentage}%"></div>
                </div>
            </div>
        `;
    }).join('');
    
    dataContainer.textContent = JSON.stringify(results, null, 2);
}

function showToast(message, type = 'success') {
    const toast = document.createElement('div');
    toast.className = `toast ${type}`;
    toast.textContent = message;
    document.body.appendChild(toast);
    setTimeout(() => {
        toast.classList.add('show');
        setTimeout(() => {
            toast.classList.remove('show');
            setTimeout(() => toast.remove(), 300);
        }, 2000);
    }, 100);
}

window.addEventListener('beforeunload', () => {
    closeCurrentWebSocket();
    stopPolling();
});

// Logic for the create poll form toggle
let createFormVisible = false;

function toggleCreateForm() {
    const form = document.getElementById('create-form');
    const button = document.querySelector('.create-poll-toggle');
    
    createFormVisible = !createFormVisible;
    
    if (createFormVisible) {
        form.classList.add('active');
        button.textContent = '✕ Close form';
    } else {
        form.classList.remove('active');
        button.textContent = '✨ Create new poll';
    }
}