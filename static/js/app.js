// Initialize Telegram WebApp
const tg = window.Telegram.WebApp;
tg.expand();

// API endpoints
const API_BASE_URL = 'http://localhost:8000/api';

// User state
let userState = {
    telegramId: null,
    username: null,
    profilePicture: null,
    walletAddress: null,
    walletTag: null,
    totalTokens: 0,
    checkInStreak: 0,
    referralCode: null,
    tasksCompleted: 0,
    totalReferrals: 0,
    leaderboardRank: 0,
    joinDate: null
};

// Project wallet info
let projectWallet = {
    address: '',
    tag: ''
};

// Initialize the app
async function initApp() {
    // Get user data from Telegram WebApp
    if (tg.initDataUnsafe?.user) {
        userState.telegramId = tg.initDataUnsafe.user.id.toString();
        userState.username = tg.initDataUnsafe.user.username;
        userState.profilePicture = tg.initDataUnsafe.user.photo_url;
        await loadUserData();
        await loadTasks();
        await loadLeaderboard();
        await loadProjectWallet();
    }

    // Setup event listeners
    setupEventListeners();
    updateUI();
}

// Load project wallet info
async function loadProjectWallet() {
    try {
        const response = await fetch(`${API_BASE_URL}/project-wallet`);
        const data = await response.json();
        projectWallet = data;
        
        // Update UI
        document.getElementById('project-wallet').textContent = projectWallet.address;
        document.getElementById('wallet-tag-display').textContent = projectWallet.tag || 'N/A';
    } catch (error) {
        console.error('Error loading project wallet:', error);
    }
}

// Load user data from backend
async function loadUserData() {
    try {
        const response = await fetch(`${API_BASE_URL}/user/${userState.telegramId}`);
        const userData = await response.json();
        
        userState = { ...userState, ...userData };
        updateUI();
    } catch (error) {
        console.error('Error loading user data:', error);
    }
}

// Load tasks
async function loadTasks() {
    try {
        const response = await fetch(`${API_BASE_URL}/tasks`);
        const tasks = await response.json();
        updateTasksUI(tasks);
    } catch (error) {
        console.error('Error loading tasks:', error);
    }
}

// Load leaderboard
async function loadLeaderboard() {
    try {
        const response = await fetch(`${API_BASE_URL}/leaderboard`);
        const leaderboard = await response.json();
        
        const leaderboardHtml = leaderboard.map((user, index) => `
            <div class="leaderboard-item rounded-xl p-4 flex items-center">
                <div class="flex-shrink-0 w-8 text-center">
                    <span class="font-bold">#${index + 1}</span>
                </div>
                <div class="flex-grow ml-4">
                    <p class="font-bold">${user.username || 'Anonymous'}</p>
                    <p class="text-gray-400 text-sm">${user.total_tokens.toLocaleString()} tokens</p>
                </div>
                ${index < 3 ? `<i class="fas fa-crown text-${index === 0 ? 'yellow' : index === 1 ? 'gray' : 'orange'}-500"></i>` : ''}
            </div>
        `).join('');
        
        document.getElementById('leaderboard-list').innerHTML = leaderboardHtml;
    } catch (error) {
        console.error('Error loading leaderboard:', error);
    }
}

// Submit wallet address
async function submitWallet(event) {
    event.preventDefault();
    const address = document.getElementById('wallet-address').value.trim();
    const tag = document.getElementById('wallet-tag').value.trim();
    
    try {
        const response = await fetch(`${API_BASE_URL}/submit-wallet`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                telegram_id: userState.telegramId,
                wallet_address: address,
                wallet_tag: tag
            })
        });
        
        if (response.ok) {
            userState.walletAddress = address;
            userState.walletTag = tag;
            updateUI();
            tg.showAlert('Wallet information saved successfully!');
        }
    } catch (error) {
        console.error('Error saving wallet:', error);
        tg.showAlert('Failed to save wallet information. Please try again.');
    }
}

// Copy project wallet address
function copyWalletAddress() {
    const textToCopy = projectWallet.tag ? 
        `Address: ${projectWallet.address}\nTag/Memo: ${projectWallet.tag}` : 
        projectWallet.address;
        
    navigator.clipboard.writeText(textToCopy)
        .then(() => tg.showAlert('Wallet address copied! 🎉'))
        .catch(() => tg.showAlert('Failed to copy wallet address.'));
}

// Daily check-in
async function dailyCheckIn() {
    try {
        const response = await fetch(`${API_BASE_URL}/daily-check-in/${userState.telegramId}`, {
            method: 'POST'
        });
        
        const result = await response.json();
        
        if (response.ok) {
            // Add confetti animation
            showConfetti();
            tg.showAlert(`🎉 Check-in successful! You earned ${result.tokens_earned} tokens!`);
            await loadUserData();
        } else {
            tg.showAlert(result.detail || 'Failed to check in. Please try again later.');
        }
    } catch (error) {
        console.error('Error during check-in:', error);
        tg.showAlert('Failed to check in. Please try again.');
    }
}



// Copy referral link
function copyReferralLink() {
    const referralLink = `https://t.me/${tg.initDataUnsafe.user.username}?start=${userState.referralCode}`;
    navigator.clipboard.writeText(referralLink)
        .then(() => tg.showAlert('Referral link copied! 🎉'))
        .catch(() => tg.showAlert('Failed to copy referral link.'));
}

// Navigation
function showPage(pageId) {
    // Hide all pages
    document.querySelectorAll('.page').forEach(page => {
        page.classList.remove('active');
        page.classList.add('hidden');
    });
    
    // Show selected page
    const selectedPage = document.getElementById(`${pageId}-page`);
    selectedPage.classList.remove('hidden');
    // Small delay to trigger transition
    setTimeout(() => {
        selectedPage.classList.add('active');
    }, 10);
    
    // Update navigation buttons
    document.querySelectorAll('.nav-btn').forEach(btn => {
        btn.classList.remove('active');
        if (btn.getAttribute('onclick').includes(pageId)) {
            btn.classList.add('active');
        }
    });

    // Scroll to top
    window.scrollTo(0, 0);
}

// Update UI elements
function updateUI() {
    // Update profile
    const profilePic = document.getElementById('profile-picture');
    if (userState.profilePicture) {
        profilePic.src = userState.profilePicture;
    } else {
        profilePic.src = 'https://via.placeholder.com/80';
    }
    
    document.getElementById('profile-name').textContent = userState.username || 'Anonymous';
    document.getElementById('join-date').textContent = `Joined ${new Date(userState.joinDate).toLocaleDateString()}`;
    
    // Update stats
    document.getElementById('total-tokens').textContent = userState.totalTokens.toLocaleString();
    document.getElementById('check-in-streak').textContent = userState.checkInStreak;
    document.getElementById('tasks-completed').textContent = `${userState.tasksCompleted}/5`;
    document.getElementById('total-referrals').textContent = userState.totalReferrals;
    document.getElementById('leaderboard-rank').textContent = `#${userState.leaderboardRank}`;
    document.getElementById('referral-code').textContent = userState.referralCode;
    
    // Update wallet status
    const walletStatus = document.getElementById('wallet-status');
    if (userState.walletAddress) {
        walletStatus.innerHTML = `
            <div class="text-center">
                <i class="fas fa-check-circle text-4xl text-green-500 mb-4"></i>
                <h3 class="text-xl font-bold mb-2">Wallet Connected</h3>
                <p class="text-gray-400 break-all">${userState.walletAddress}</p>
            </div>
        `;
    }
}

// Confetti animation
function showConfetti() {
    // Add confetti animation library and implementation here
}

// Setup event listeners
function setupEventListeners() {
    // Daily check-in button
    document.getElementById('daily-checkin').addEventListener('click', dailyCheckIn);
    
    // Task buttons
    document.querySelectorAll('#tasks-list .glow-button').forEach(button => {
        button.addEventListener('click', async (e) => {
            const taskCard = e.target.closest('.task-card');
            const taskTitle = taskCard.querySelector('h3').textContent;
            try {
                const response = await fetch(`${API_BASE_URL}/complete-task`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({
                        telegram_id: userState.telegramId,
                        task_title: taskTitle
                    })
                });
                
                if (response.ok) {
                    showConfetti();
                    tg.showAlert('🎉 Task completed successfully!');
                    await loadUserData();
                } else {
                    tg.showAlert('Failed to complete task. Please try again.');
                }
            } catch (error) {
                console.error('Error completing task:', error);
                tg.showAlert('Failed to complete task. Please try again.');
            }
        });
    });

    // Wallet connect button
    document.getElementById('connect-wallet').addEventListener('click', connectWallet);
    
    // Copy referral link button
    document.getElementById('copy-referral').addEventListener('click', copyReferralLink);
    
    // Donation buttons
    const donationAmounts = [0.1, 0.5, 1, 5];
    donationAmounts.forEach(amount => {
        document.getElementById(`donate-${amount}`).addEventListener('click', donate);
    });
}

// Initialize the app when the document is ready
document.addEventListener('DOMContentLoaded', initApp);
