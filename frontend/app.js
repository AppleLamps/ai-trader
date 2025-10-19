// AI Crypto Trading Bot - Frontend JavaScript

const API_BASE = '/api';
let updateInterval = null;

// DOM Elements
const startBtn = document.getElementById('startBtn');
const stopBtn = document.getElementById('stopBtn');
const runCycleBtn = document.getElementById('runCycleBtn');
const botStatus = document.getElementById('botStatus');

// Initialize
document.addEventListener('DOMContentLoaded', () => {
    console.log('AI Crypto Trading Bot initialized');

    // Set up event listeners
    startBtn.addEventListener('click', startBot);
    stopBtn.addEventListener('click', stopBot);
    runCycleBtn.addEventListener('click', runSingleCycle);

    // Initial data fetch
    updateDashboard();

    // Start auto-update
    startAutoUpdate();
});

// API Functions
async function apiCall(endpoint, method = 'GET', body = null) {
    try {
        const options = {
            method,
            headers: {
                'Content-Type': 'application/json'
            }
        };

        if (body) {
            options.body = JSON.stringify(body);
        }

        const response = await fetch(`${API_BASE}${endpoint}`, options);
        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.detail || 'API request failed');
        }

        return data;
    } catch (error) {
        console.error(`API Error (${endpoint}):`, error);
        showNotification(`Error: ${error.message}`, 'error');
        return null;
    }
}

// Bot Control Functions
async function startBot() {
    const result = await apiCall('/bot/control', 'POST', { action: 'start' });
    if (result && result.success) {
        showNotification('Bot started successfully', 'success');
        updateBotStatus(true);
    }
}

async function stopBot() {
    const result = await apiCall('/bot/control', 'POST', { action: 'stop' });
    if (result && result.success) {
        showNotification('Bot stopped successfully', 'success');
        updateBotStatus(false);
    }
}

async function runSingleCycle() {
    runCycleBtn.disabled = true;
    runCycleBtn.textContent = '⏳ Running...';

    const result = await apiCall('/bot/run-cycle', 'POST');

    if (result && result.success) {
        showNotification('Trading cycle completed', 'success');
        await updateDashboard();
    }

    runCycleBtn.disabled = false;
    runCycleBtn.textContent = '⚡ Run Single Cycle';
}

// Update Functions
async function updateDashboard() {
    await Promise.all([
        updateStatus(),
        updateMarketData(),
        updatePortfolio(),
        updateTradeHistory(),
        updateActivityLog(),
        updateStatistics()
    ]);
}

async function updateStatus() {
    const result = await apiCall('/status');
    if (result && result.success) {
        const status = result.data;
        updateBotStatus(status.is_running);

        // Update AI decisions for all pairs
        if (status.last_decisions && Object.keys(status.last_decisions).length > 0) {
            updateAIDecisions(status.last_decisions);
        }
    }
}

async function updateMarketData() {
    const result = await apiCall('/market-data');
    if (result && result.success && result.data) {
        const marketDataByPair = result.data;
        const container = document.getElementById('marketDataContainer');

        if (!container) return;

        // Clear existing content
        container.innerHTML = '';

        // Create a card for each trading pair
        for (const [pair, data] of Object.entries(marketDataByPair)) {
            if (!data) continue;

            const card = document.createElement('div');
            card.className = 'rounded-lg border bg-white shadow-sm p-4';

            const technical = data.technical_indicators || {};
            const rsi = technical.RSI || {};
            const macd = technical.MACD || {};

            card.innerHTML = `
                <h3 class="text-lg font-bold mb-3">${pair}</h3>
                <div class="space-y-3">
                    <div>
                        <p class="text-xs font-medium text-muted-foreground">Price</p>
                        <p class="text-2xl font-bold text-success">${data.price ? '$' + formatNumber(data.price) : '$-'}</p>
                    </div>
                    <div class="grid grid-cols-2 gap-2 text-xs">
                        <div>
                            <p class="text-muted-foreground">24h Change</p>
                            <p class="font-semibold">${data.change_24h ? data.change_24h + '%' : '-'}</p>
                        </div>
                        <div>
                            <p class="text-muted-foreground">Volume</p>
                            <p class="font-semibold">${data.volume ? formatNumber(data.volume) : '-'}</p>
                        </div>
                        <div>
                            <p class="text-muted-foreground">RSI</p>
                            <p class="font-semibold">${rsi.value ? formatNumber(rsi.value, 2) : '-'}</p>
                        </div>
                        <div>
                            <p class="text-muted-foreground">MACD</p>
                            <p class="font-semibold">${macd.value ? formatNumber(macd.value, 4) : '-'}</p>
                        </div>
                    </div>
                </div>
            `;

            container.appendChild(card);
        }
    }
}

async function updatePortfolio() {
    const result = await apiCall('/portfolio');
    if (result && result.success && result.data) {
        const portfolio = result.data;

        document.getElementById('usdBalance').textContent = `$${formatNumber(portfolio.usd_balance)}`;
        document.getElementById('totalValue').textContent = `$${formatNumber(portfolio.total_value_usd)}`;

        // Update crypto balances
        const container = document.getElementById('cryptoBalancesContainer');
        if (container && portfolio.crypto_balances) {
            container.innerHTML = '';

            for (const [symbol, balance] of Object.entries(portfolio.crypto_balances)) {
                const valueUsd = portfolio.crypto_values_usd[symbol] || 0;

                const balanceDiv = document.createElement('div');
                balanceDiv.className = 'rounded-md border p-3';
                balanceDiv.innerHTML = `
                    <div class="flex justify-between items-center">
                        <div>
                            <p class="text-xs font-medium text-muted-foreground">${symbol} Balance</p>
                            <p class="text-sm font-bold mt-1">${formatNumber(balance, 8)} ${symbol}</p>
                        </div>
                        <div class="text-right">
                            <p class="text-xs font-medium text-muted-foreground">Value</p>
                            <p class="text-sm font-bold mt-1">$${formatNumber(valueUsd)}</p>
                        </div>
                    </div>
                `;
                container.appendChild(balanceDiv);
            }
        }
    }
}

async function updateTradeHistory() {
    const result = await apiCall('/trades?limit=20');
    if (result && result.success) {
        const trades = result.data;
        const tbody = document.getElementById('tradeTableBody');

        if (trades.length === 0) {
            tbody.innerHTML = '<tr><td colspan="7" class="px-4 py-8 text-center text-sm text-muted-foreground">No trades yet</td></tr>';
            return;
        }

        tbody.innerHTML = trades.map(trade => {
            const typeClass = trade.trade_type === 'BUY'
                ? 'inline-flex items-center rounded-md px-2 py-1 text-xs font-medium bg-success/10 text-success'
                : 'inline-flex items-center rounded-md px-2 py-1 text-xs font-medium bg-destructive/10 text-destructive';

            return `
                <tr class="hover:bg-muted/50 transition-colors">
                    <td class="px-4 py-3 text-sm">${formatTime(trade.timestamp)}</td>
                    <td class="px-4 py-3 text-sm font-medium">${trade.pair || '-'}</td>
                    <td class="px-4 py-3"><span class="${typeClass}">${trade.trade_type}</span></td>
                    <td class="px-4 py-3 text-sm font-medium">$${formatNumber(trade.price)}</td>
                    <td class="px-4 py-3 text-sm">${formatNumber(trade.amount, 8)}</td>
                    <td class="px-4 py-3 text-sm font-medium">$${formatNumber(trade.usd_value)}</td>
                    <td class="px-4 py-3 text-sm text-muted-foreground">${truncate(trade.reasoning, 50)}</td>
                </tr>
            `;
        }).join('');
    }
}

async function updateActivityLog() {
    const result = await apiCall('/activity-log?limit=20');
    if (result && result.success) {
        const logs = result.data;
        const container = document.getElementById('activityLog');

        if (logs.length === 0) {
            container.innerHTML = '<div class="text-muted-foreground"><span class="font-semibold">--:--:--</span><span class="ml-2">Waiting for activity...</span></div>';
            return;
        }

        container.innerHTML = logs.reverse().map(log => {
            let typeColor = 'text-primary';
            if (log.type === 'DATA_FETCH') typeColor = 'text-blue-600';
            else if (log.type === 'AI_DECISION') typeColor = 'text-purple-600';
            else if (log.type === 'TRADE') typeColor = 'text-success';
            else if (log.type === 'ERROR') typeColor = 'text-destructive';

            return `
                <div class="text-sm">
                    <span class="font-semibold text-muted-foreground">${formatTime(log.timestamp)}</span>
                    <span class="ml-2 font-semibold ${typeColor}">[${log.type}]</span>
                    <span class="ml-2">${log.message}</span>
                </div>
            `;
        }).join('');
    }
}

async function updateStatistics() {
    const result = await apiCall('/statistics');
    if (result && result.success && result.data) {
        const stats = result.data;

        document.getElementById('totalTrades').textContent = stats.total_trades || 0;
        document.getElementById('buyTrades').textContent = stats.buy_trades || 0;
        document.getElementById('sellTrades').textContent = stats.sell_trades || 0;
    }
}

function updateBotStatus(isRunning) {
    if (isRunning) {
        botStatus.textContent = 'Running';
        botStatus.className = 'inline-flex items-center rounded-full px-3 py-1 text-xs font-medium bg-success/10 text-success';
        startBtn.disabled = true;
        stopBtn.disabled = false;
    } else {
        botStatus.textContent = 'Stopped';
        botStatus.className = 'inline-flex items-center rounded-full px-3 py-1 text-xs font-medium bg-destructive/10 text-destructive';
        startBtn.disabled = false;
        stopBtn.disabled = true;
    }
}

function updateAIDecisions(decisions) {
    const container = document.getElementById('decisionsContainer');
    if (!container) return;

    container.innerHTML = '';

    for (const [pair, decision] of Object.entries(decisions)) {
        if (!decision || !decision.decision) continue;

        const decisionCard = document.createElement('div');
        decisionCard.className = 'border rounded-lg p-4';

        let decisionClass = 'inline-flex items-center rounded-md px-3 py-1 text-sm font-semibold';
        if (decision.decision === 'BUY') {
            decisionClass += ' bg-success/10 text-success border border-success/20';
        } else if (decision.decision === 'SELL') {
            decisionClass += ' bg-destructive/10 text-destructive border border-destructive/20';
        } else {
            decisionClass += ' bg-amber-500/10 text-amber-700 border border-amber-500/20';
        }

        decisionCard.innerHTML = `
            <div class="flex items-center justify-between mb-3">
                <h3 class="font-semibold">${pair}</h3>
                <span class="${decisionClass}">${decision.decision}</span>
            </div>
            <div class="rounded-md bg-muted p-3 border-l-4 border-primary">
                <p class="text-sm leading-relaxed">${decision.reasoning || 'No reasoning provided'}</p>
            </div>
            ${decision.confidence ? `
                <div class="mt-2 text-xs text-muted-foreground">
                    Confidence: ${(decision.confidence * 100).toFixed(0)}% | Risk: ${decision.risk_level || 'N/A'}
                </div>
            ` : ''}
        `;

        container.appendChild(decisionCard);
    }
}

// Utility Functions
function formatNumber(num, decimals = 2) {
    if (num === null || num === undefined) return '-';
    return Number(num).toLocaleString('en-US', {
        minimumFractionDigits: decimals,
        maximumFractionDigits: decimals
    });
}

function formatTime(timestamp) {
    if (!timestamp) return '-';
    const date = new Date(timestamp);
    return date.toLocaleTimeString('en-US', {
        hour: '2-digit',
        minute: '2-digit',
        second: '2-digit'
    });
}

function truncate(str, maxLength) {
    if (!str) return '-';
    return str.length > maxLength ? str.substring(0, maxLength) + '...' : str;
}

function showNotification(message, type = 'info') {
    console.log(`[${type.toUpperCase()}] ${message}`);
    // You can implement a toast notification system here
}

function startAutoUpdate() {
    // Update every 5 seconds
    updateInterval = setInterval(updateDashboard, 5000);
}

function stopAutoUpdate() {
    if (updateInterval) {
        clearInterval(updateInterval);
        updateInterval = null;
    }
}

// Clean up on page unload
window.addEventListener('beforeunload', () => {
    stopAutoUpdate();
});

