// ========================================
// COMPLETELY REBUILT TRADE HISTORY SYSTEM
// ========================================

// IMMEDIATE TEST - Check if JavaScript is loading
console.log('🚀 JavaScript file loaded successfully!');
console.log('📄 Document ready state:', document.readyState);

// Test DOM access immediately
setTimeout(() => {
    console.log('⏰ Immediate DOM check:');
    console.log('  - trades-tbody exists:', !!document.getElementById('trades-tbody'));
    console.log('  - trade-history-section exists:', !!document.querySelector('.trade-history-section'));
    
    if (document.getElementById('trades-tbody')) {
        console.log('  - trades-tbody innerHTML:', document.getElementById('trades-tbody').innerHTML.substring(0, 100));
    }
}, 100);

// Global variables for trade history
let tradeHistoryData = [];
let tradeHistoryLoaded = false;

// ========================================
// CORE TRADE HISTORY FUNCTIONS
// ========================================

/**
 * Load trade history data from the API
 */
function loadTradeHistory() {
    console.log('🔍 DEBUG: Loading trade history...');
    
    // First try to get backtest results
    fetch('/api/trades/backtest-results')
        .then(response => response.json())
        .then(data => {
            console.log('🔍 DEBUG: Backtest results response:', data);
            if (data.success && data.trades && data.trades.length > 0) {
                console.log('✅ Using backtest results:', data.trades.length, 'trades');
                updateTradesTable(data.trades);
                return;
            }
            
            // Fallback to stored trades
            console.log('🔄 No backtest results, falling back to stored trades...');
            return fetch('/api/trades/stored?limit=100');
        })
        .then(response => {
            if (response) {
                return response.json();
            }
        })
        .then(data => {
            if (data && data.success && data.trades) {
                console.log('✅ Using stored trades:', data.trades.length, 'trades');
                updateTradesTable(data.trades);
            } else {
                console.log('⚠️ No trades found');
                updateTradesTable([]);
            }
        })
        .catch(error => {
            console.error('❌ Error loading trade history:', error);
            updateTradesTable([]);
        });
}

/**
 * Display trade history in the table
 */
function displayTradeHistory() {
    console.log('📊 Displaying trade history...');
    
    const tbody = document.getElementById('trades-tbody');
    if (!tbody) {
        console.error('❌ Trade history table body not found');
        return;
    }
    
    // Clear existing content
    tbody.innerHTML = '';
    
    if (tradeHistoryData.length === 0) {
        tbody.innerHTML = `
            <tr>
                <td colspan="9" class="no-data">
                    <div style="text-align: center; padding: 20px; color: #666;">
                        <div style="font-size: 24px; margin-bottom: 10px;">📊</div>
                        <div style="font-size: 16px; font-weight: bold; margin-bottom: 5px;">No trades yet</div>
                        <div style="font-size: 14px;">Run a backtest to see results</div>
                    </div>
                </td>
            </tr>
        `;
        return;
    }
    
    // Sort trades by entry date (newest first)
    const sortedTrades = [...tradeHistoryData].sort((a, b) => 
        new Date(b.entry_date) - new Date(a.entry_date)
    );
    
    // Display each trade
    sortedTrades.forEach(trade => {
        const row = createTradeRow(trade);
        tbody.appendChild(row);
    });
    
    console.log(`✅ Displayed ${sortedTrades.length} trades`);
    updateTradeStatistics();
}

/**
 * Create a table row for a trade
 */
function createTradeRow(trade) {
    const row = document.createElement('tr');
    row.className = 'trade-row';
    row.setAttribute('data-trade-id', trade.id);
    
    // Format dates
    const entryDate = formatDate(trade.entry_date);
    const exitDate = trade.exit_date ? formatDate(trade.exit_date) : 'Open';
    
    // Calculate P&L
    const pnlDollars = trade.pnl_dollars || 0;
    const pnlPercent = trade.pnl_pct || 0;
    
    // Determine status and styling
    const isClosed = trade.status === 'closed';
    const isProfitable = pnlDollars >= 0;
    
    row.innerHTML = `
        <td>${entryDate}</td>
        <td><strong>${trade.ticker}</strong></td>
        <td>
            <span class="status-badge ${isClosed ? 'closed' : 'open'}">
                ${isClosed ? 'CLOSED' : 'OPEN'}
            </span>
        </td>
        <td>${trade.shares?.toFixed(2) || 'N/A'}</td>
        <td>$${trade.entry_price?.toFixed(2) || 'N/A'}</td>
        <td class="${isProfitable ? 'positive' : 'negative'}">
            $${pnlDollars?.toFixed(2) || 'N/A'}
        </td>
        <td class="${isProfitable ? 'positive' : 'negative'}">
            ${pnlPercent?.toFixed(2) || 'N/A'}%
        </td>
        <td>${trade.strategy || 'N/A'}</td>
        <td>
            <span class="result-badge ${isProfitable ? 'win' : 'loss'}">
                ${isProfitable ? 'WIN' : 'LOSS'}
            </span>
        </td>
    `;
    
    // Add click handler for trade details
    row.addEventListener('click', () => showTradeDetails(trade));
    row.style.cursor = 'pointer';
    
    return row;
}

/**
 * Show error message in trade history
 */
function showTradeHistoryError(message) {
    const tbody = document.getElementById('trades-tbody');
    if (tbody) {
        tbody.innerHTML = `
            <tr>
                <td colspan="9" class="error">
                    <div style="text-align: center; padding: 20px; color: #d32f2f;">
                        <div style="font-size: 24px; margin-bottom: 10px;">⚠️</div>
                        <div style="font-size: 16px; font-weight: bold; margin-bottom: 5px;">Error</div>
                        <div style="font-size: 14px;">${message}</div>
                    </div>
                </td>
            </tr>
        `;
    }
}

/**
 * Update trade statistics
 */
function updateTradeStatistics() {
    if (!tradeHistoryData.length) return;
    
    const closedTrades = tradeHistoryData.filter(t => t.status === 'closed');
    const totalTrades = closedTrades.length;
    const winningTrades = closedTrades.filter(t => (t.pnl_dollars || 0) >= 0).length;
    const totalPnL = closedTrades.reduce((sum, t) => sum + (t.pnl_dollars || 0), 0);
    const winRate = totalTrades > 0 ? (winningTrades / totalTrades * 100).toFixed(1) : 0;
    
    console.log(`📈 Trade Statistics: ${totalTrades} trades, ${winRate}% win rate, $${totalPnL.toFixed(2)} total P&L`);
}

/**
 * Format date for display
 */
function formatDate(dateString) {
    if (!dateString) return 'N/A';
    try {
        return new Date(dateString).toLocaleDateString();
    } catch (error) {
        return dateString;
    }
}

/**
 * Show trade details modal
 */
function showTradeDetails(trade) {
    console.log('📋 Showing trade details:', trade);
    
    const modal = document.createElement('div');
    modal.className = 'trade-details-modal';
    modal.innerHTML = `
        <div class="modal-content">
            <div class="modal-header">
                <h3>Trade Details - ${trade.ticker}</h3>
                <button class="close-btn" onclick="this.parentElement.parentElement.parentElement.remove()">&times;</button>
            </div>
            <div class="modal-body">
                <div class="trade-info">
                    <div class="info-row">
                        <span class="label">Entry Date:</span>
                        <span class="value">${formatDate(trade.entry_date)}</span>
                    </div>
                    <div class="info-row">
                        <span class="label">Exit Date:</span>
                        <span class="value">${trade.exit_date ? formatDate(trade.exit_date) : 'Open'}</span>
                    </div>
                    <div class="info-row">
                        <span class="label">Shares:</span>
                        <span class="value">${trade.shares?.toFixed(2) || 'N/A'}</span>
                    </div>
                    <div class="info-row">
                        <span class="label">Entry Price:</span>
                        <span class="value">$${trade.entry_price?.toFixed(2) || 'N/A'}</span>
                    </div>
                    <div class="info-row">
                        <span class="label">Exit Price:</span>
                        <span class="value">$${trade.exit_price?.toFixed(2) || 'N/A'}</span>
                    </div>
                    <div class="info-row">
                        <span class="label">P&L:</span>
                        <span class="value ${(trade.pnl_dollars || 0) >= 0 ? 'positive' : 'negative'}">
                            $${(trade.pnl_dollars || 0).toFixed(2)} (${(trade.pnl_pct || 0).toFixed(2)}%)
                        </span>
                    </div>
                    <div class="info-row">
                        <span class="label">Strategy:</span>
                        <span class="value">${trade.strategy || 'N/A'}</span>
                    </div>
                    <div class="info-row">
                        <span class="label">Entry Reason:</span>
                        <span class="value">${trade.entry_reason || 'N/A'}</span>
                    </div>
                    <div class="info-row">
                        <span class="label">Exit Reason:</span>
                        <span class="value">${trade.exit_reason || 'N/A'}</span>
                    </div>
                </div>
            </div>
        </div>
    `;
    
    document.body.appendChild(modal);
    
    // Close modal when clicking outside
    modal.addEventListener('click', (e) => {
        if (e.target === modal) {
            modal.remove();
        }
    });
}

// ========================================
// AUTO-REFRESH SYSTEM
// ========================================

let refreshInterval = null;

/**
 * Start automatic refresh of trade history
 */
// DISABLED: Auto-refresh to prevent trade history from vanishing
function startAutoRefresh() {
    // Auto-refresh disabled to prevent trade history from vanishing
    console.log('ℹ️ Auto-refresh disabled - trade history will persist');
    return;
    
    // Original code commented out:
    /*
    if (refreshInterval) {
        clearInterval(refreshInterval);
    }
    
    // Refresh every 30 seconds
    refreshInterval = setInterval(() => {
        console.log('🔄 Auto-refreshing trade history...');
        loadTradeHistory();
    }, 30000);
    
    console.log('✅ Auto-refresh started (30s interval)');
    */
}

/**
 * Stop automatic refresh
 */
function stopAutoRefresh() {
    if (refreshInterval) {
        clearInterval(refreshInterval);
        refreshInterval = null;
        console.log('⏹️ Auto-refresh stopped');
    }
}

// ========================================
// MANUAL REFRESH BUTTONS
// ========================================

/**
 * Add refresh button to the page
 */
function addRefreshButton() {
    const tradeHistorySection = document.querySelector('.trade-history-section');
    if (!tradeHistorySection) return;
    
    // Check if button already exists
    if (document.getElementById('refresh-trades-btn')) return;
    
    const button = document.createElement('button');
    button.id = 'refresh-trades-btn';
    button.className = 'refresh-btn';
    button.innerHTML = '🔄 Refresh Trades';
    button.onclick = () => {
        console.log('🔄 Manual refresh triggered');
        loadTradeHistory();
    };
    
    // Insert button at the top of the trade history section
    const header = tradeHistorySection.querySelector('h2');
    if (header) {
        header.parentNode.insertBefore(button, header.nextSibling);
    }
}

// ========================================
// INITIALIZATION
// ========================================

/**
 * Initialize the trade history system
 */
function initializeTradeHistory() {
    console.log('🚀 Initializing trade history system...');
    console.log('🔍 DOM check - trades-tbody exists:', !!document.getElementById('trades-tbody'));
    console.log('🔍 DOM check - trade-history-section exists:', !!document.querySelector('.trade-history-section'));
    
    // Add refresh button
    addRefreshButton();
    
    // Load initial data
    loadTradeHistory();
    
    // Start auto-refresh
    startAutoRefresh();
    
    console.log('✅ Trade history system initialized');
}

// ========================================
// EVENT LISTENERS
// ========================================

// REMOVED: Duplicate DOMContentLoaded listener - consolidated below

// Initialize when window loads (backup)
window.addEventListener('load', function() {
    console.log('🌐 Window loaded, ensuring trade history is initialized...');
    if (!tradeHistoryLoaded) {
        initializeTradeHistory();
    }
});

// ========================================
// WEBSOCKET INTEGRATION (for real-time updates)
// ========================================

// Initialize WebSocket connection
let socket = null;

function initializeWebSocket() {
    try {
        socket = io();
        
        socket.on('connect', function() {
            console.log('🔌 WebSocket connected');
        });
        
        socket.on('new_trade', function(data) {
            console.log('📈 New trade received:', data);
            loadTradeHistory(); // Refresh to show new trade
        });
        
        socket.on('trade_closed', function(data) {
            console.log('📉 Trade closed received:', data);
            loadTradeHistory(); // Refresh to show updated trade
        });
        
        socket.on('backtest_complete', function(data) {
            console.log('✅ Backtest complete received:', data);
            loadTradeHistory(); // Refresh to show all new trades
        });
        
        socket.on('disconnect', function() {
            console.log('🔌 WebSocket disconnected');
        });
        
    } catch (error) {
        console.warn('⚠️ WebSocket not available:', error);
    }
}

// Initialize WebSocket when page loads
if (typeof io !== 'undefined') {
    initializeWebSocket();
}

// ========================================
// LEGACY COMPATIBILITY (keeping old function names)
// ========================================

// Keep old function names for compatibility
function loadTradesData() {
    loadTradeHistory();
}

// REMOVED: Duplicate updateTradesTable function - using the one at line 770

// ========================================
// DEBUG FUNCTIONS
// ========================================

/**
 * Debug function to test the system
 */
function debugTradeHistory() {
    console.log('🔍 Debugging trade history system...');
    console.log('- Trade history data:', tradeHistoryData);
    console.log('- Trade history loaded:', tradeHistoryLoaded);
    console.log('- Auto-refresh interval:', refreshInterval);
    console.log('- WebSocket connected:', socket?.connected);
    
    // Test API call
    fetch('/api/trades/stored?limit=3')
        .then(response => response.json())
        .then(data => {
            console.log('- API test result:', data);
        })
        .catch(error => {
            console.error('- API test error:', error);
        });
}

/**
 * Simple test function to force load trades
 */
function testLoadTrades() {
    console.log('🧪 Testing trade loading...');
    
    fetch('/api/trades/stored?limit=5')
        .then(response => response.json())
        .then(data => {
            console.log('🧪 API Response:', data);
            
            if (data.success && data.trades.length > 0) {
                console.log('🧪 Found trades, updating display...');
                tradeHistoryData = data.trades;
                displayTradeHistory();
            } else {
                console.log('🧪 No trades found in API response');
            }
        })
        .catch(error => {
            console.error('🧪 API Error:', error);
        });
}

// Make debug function available globally
window.debugTradeHistory = debugTradeHistory;
window.testLoadTrades = testLoadTrades;

// DISABLED: Immediate test to prevent interference
// setTimeout(() => {
//     console.log('🧪 Running immediate trade test...');
//     testLoadTrades();
// }, 500);

// ========================================
// ESSENTIAL DASHBOARD FUNCTIONS
// ========================================

// REMOVED: Duplicate DOMContentLoaded listener - consolidated below

// ========================================
// NEW TRADE HISTORY FUNCTIONS
// ========================================

function exportTradeHistoryToCSV() {
    if (!window.currentHistoricalTradesData || window.currentHistoricalTradesData.length === 0) {
        alert('No historical trade data to export. Run a backtest first.');
        return;
    }
    
    // Create CSV content
    const headers = ['Date', 'Symbol', 'Action', 'Shares', 'Price', 'Value', 'P&L', 'P&L %', 'Strategy'];
    const csvContent = [
        headers.join(','),
        ...window.currentHistoricalTradesData.map(trade => [
            trade.date,
            trade.symbol,
            trade.action,
            trade.shares?.toFixed(2) || '',
            trade.price?.toFixed(2) || '',
            trade.value?.toFixed(2) || '',
            trade.pnl?.toFixed(2) || '',
            trade.pnl_pct?.toFixed(2) || '',
            trade.strategy || ''
        ].join(','))
    ].join('\n');
    
    // Create and download file
    const blob = new Blob([csvContent], { type: 'text/csv' });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `trade_history_${new Date().toISOString().split('T')[0]}.csv`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    window.URL.revokeObjectURL(url);
}

function toggleRealData() {
    const btn = document.getElementById('toggle-real-data-btn');
    const isRealData = btn.textContent.includes('Real Data');
    
    if (isRealData) {
        // Switch to cached data
        btn.textContent = '🔄 Show Cached Data';
        btn.style.background = '#e74c3c';
        loadTradeHistory(); // Load cached data
    } else {
        // Switch to real data (from historical backtest)
        btn.textContent = '🔄 Show Real Data';
        btn.style.background = '#9b59b6';
        if (window.currentHistoricalTradesData && window.currentHistoricalTradesData.length > 0) {
            updateTradesTable(window.currentHistoricalTradesData);
        } else {
            alert('No real data available. Run a historical backtest first.');
        }
    }
}

function clearTradeHistory() {
    // Clear the trades table
    const tbody = document.getElementById('trades-tbody');
    if (tbody) {
        tbody.innerHTML = `
            <tr>
                <td colspan="9" style="text-align: center; color: #666; padding: 20px;">
                    No trades yet. Run a backtest to see results.
                </td>
            </tr>
        `;
    }
    
    // Clear stored data
    window.currentHistoricalTradesData = [];
    
    // Clear historical results
    const historicalResultsSection = document.getElementById('historical-results');
    if (historicalResultsSection) {
        historicalResultsSection.style.display = 'none';
    }
    
    // Reset KPIs
    const strategyReturn = document.getElementById('historical-strategy-return');
    const benchmarkReturn = document.getElementById('historical-benchmark-return');
    const alphaReturn = document.getElementById('historical-alpha-return');
    const winRateElement = document.getElementById('historical-win-rate');
    const avgTradeReturnElement = document.getElementById('historical-avg-trade-return');
    
    if (strategyReturn) strategyReturn.textContent = '0.00%';
    if (benchmarkReturn) benchmarkReturn.textContent = '0.00%';
    if (alphaReturn) alphaReturn.textContent = '0.00%';
    if (winRateElement) winRateElement.textContent = '0.0%';
    if (avgTradeReturnElement) avgTradeReturnElement.textContent = '0.00%';
    
    // Call API to clear server-side data with force=true
    fetch('/api/trades/clear', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ force: true })
    })
    .then(response => response.json())
    .then(result => {
        console.log('🗑️ Trade history cleared:', result);
    })
    .catch(error => {
        console.error('❌ Error clearing trade history:', error);
    });
}

// ========================================
// ENHANCED BACKTEST LOGS
// ========================================

function runHistoricalBacktest(data) {
    const btn = document.getElementById('run-backtest-btn');
    const logs = document.getElementById('backtest-logs');
    
    // Update UI
    btn.disabled = true;
    btn.textContent = '🔄 Running...';
    
    // Clear previous logs and show header
    logs.innerHTML = `
        <div style="font-family: 'Courier New', monospace; background: #1e1e1e; color: #00ff00; padding: 15px; border-radius: 5px; margin-bottom: 10px;">
            <div style="color: #ffff00;">[${new Date().toLocaleTimeString()}] 🚀 Starting Historical Backtest</div>
            <div style="color: #00ffff;">[${new Date().toLocaleTimeString()}] 📊 Period: ${data.period}</div>
            <div style="color: #00ffff;">[${new Date().toLocaleTimeString()}] 🎯 Strategy: ${data.strategy} (${data.profile})</div>
            <div style="color: #00ffff;">[${new Date().toLocaleTimeString()}] 📈 Benchmark: ${data.benchmark}</div>
            <div style="color: #ffff00;">[${new Date().toLocaleTimeString()}] ⏳ Calculating date range...</div>
        </div>
    `;
    
    // Calculate date range
    let endDate = new Date();
    let startDate = new Date();
    
    if (data.period === 'custom') {
        // Use custom date range
        const startDateInput = document.getElementById('start-date');
        const endDateInput = document.getElementById('end-date');
        
        if (startDateInput.value && endDateInput.value) {
            startDate = new Date(startDateInput.value);
            endDate = new Date(endDateInput.value);
        } else {
            logs.innerHTML += `
                <div style="font-family: 'Courier New', monospace; background: #1e1e1e; color: #ff0000; padding: 15px; border-radius: 5px; margin-bottom: 10px;">
                    <div style="color: #ff0000;">[${new Date().toLocaleTimeString()}] ❌ Error: Please select both start and end dates for custom range</div>
                </div>
            `;
            btn.disabled = false;
            btn.textContent = '🚀 Run Historical Backtest';
            return;
        }
    } else {
        // Use predefined periods
        switch(data.period) {
            case '1m':
                startDate.setMonth(endDate.getMonth() - 1);
                break;
            case '6m':
                startDate.setMonth(endDate.getMonth() - 6);
                break;
            case '1y':
                startDate.setFullYear(endDate.getFullYear() - 1);
                break;
            case '2y':
                startDate.setFullYear(endDate.getFullYear() - 2);
                break;
            case '3y':
                startDate.setFullYear(endDate.getFullYear() - 3);
                break;
            case '5y':
                startDate.setFullYear(endDate.getFullYear() - 5);
                break;
        }
    }
    
    logs.innerHTML += `
        <div style="font-family: 'Courier New', monospace; background: #1e1e1e; color: #00ff00; padding: 15px; border-radius: 5px; margin-bottom: 10px;">
            <div style="color: #00ffff;">[${new Date().toLocaleTimeString()}] 📅 Date Range: ${startDate.toISOString().split('T')[0]} to ${endDate.toISOString().split('T')[0]}</div>
            <div style="color: #ffff00;">[${new Date().toLocaleTimeString()}] 🔄 Making API call...</div>
        </div>
    `;
    
    // Make API call
    fetch('/api/automation/historical-backtest', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            period: data.period,
            strategy: data.strategy,
            profile: data.profile,
            benchmark: data.benchmark
        })
    })
    .then(response => response.json())
    .then(result => {
        if (result.error) {
            logs.innerHTML += `
                <div style="font-family: 'Courier New', monospace; background: #1e1e1e; color: #ff0000; padding: 15px; border-radius: 5px; margin-bottom: 10px;">
                    <div style="color: #ff0000;">[${new Date().toLocaleTimeString()}] ❌ Error: ${result.error}</div>
                </div>
            `;
            updateTradesTable([]);
        } else {
            logs.innerHTML += `
                <div style="font-family: 'Courier New', monospace; background: #1e1e1e; color: #00ff00; padding: 15px; border-radius: 5px; margin-bottom: 10px;">
                    <div style="color: #00ff00;">[${new Date().toLocaleTimeString()}] ✅ Backtest completed successfully!</div>
            `;
            
            // Display terminal output if available
            if (result.terminal_output) {
                logs.innerHTML += `
                    <div style="font-family: 'Courier New', monospace; background: #1e1e1e; color: #00ff00; padding: 15px; border-radius: 5px; margin-bottom: 10px; max-height: 400px; overflow-y: auto;">
                        <div style="color: #ffff00;">[${new Date().toLocaleTimeString()}] 📋 Terminal Output:</div>
                        <pre style="color: #00ff00; margin: 10px 0; white-space: pre-wrap;">${result.terminal_output}</pre>
                    </div>
                `;
            }
            
            // Handle the new API response format
            if (result.summary) {
                logs.innerHTML += `
                    <div style="color: #00ffff;">[${new Date().toLocaleTimeString()}] 📊 Total trades: ${result.summary.total_trades || 'undefined'}</div>
                    <div style="color: #00ffff;">[${new Date().toLocaleTimeString()}] 💰 Final portfolio value: $${(result.summary.final_portfolio_value || 0).toLocaleString()}</div>
                    <div style="color: #00ffff;">[${new Date().toLocaleTimeString()}] 📈 Total return: ${(result.summary.total_return || 0).toFixed(2)}%</div>
                `;
                
                displayHistoricalResults(result);
            } else {
                // Fallback for old format
                logs.innerHTML += `
                    <div style="color: #00ffff;">[${new Date().toLocaleTimeString()}] 📊 Total trades: ${result.total_trades || 'undefined'}</div>
                    <div style="color: #00ffff;">[${new Date().toLocaleTimeString()}] 💰 Final value: $${(result.final_value || 0).toLocaleString()}</div>
                    <div style="color: #00ffff;">[${new Date().toLocaleTimeString()}] 📈 Total return: ${(result.total_return || 0).toFixed(2)}%</div>
                `;
                
                displayHistoricalResults(result);
            }
            
            logs.innerHTML += `</div>`;
        }
    })
    .catch(error => {
        logs.innerHTML += `
            <div style="font-family: 'Courier New', monospace; background: #1e1e1e; color: #ff0000; padding: 15px; border-radius: 5px; margin-bottom: 10px;">
                <div style="color: #ff0000;">[${new Date().toLocaleTimeString()}] ❌ Error: ${error.message}</div>
            </div>
        `;
        updateTradesTable([]);
    })
    .finally(() => {
        btn.disabled = false;
        btn.textContent = '🚀 Run Historical Backtest';
    });
}

function updateTradesTable(trades) {
    console.log('🔍 DEBUG: updateTradesTable called with', trades.length, 'trades');
    const tbody = document.getElementById('trades-tbody');
    
    if (!tbody) {
        console.error('❌ Trade history table body not found!');
        return;
    }
    
    if (!trades || trades.length === 0) {
        console.log('⚠️ No trades to display');
        tbody.innerHTML = '<tr><td colspan="9" class="loading">No trades found.</td></tr>';
        const exportBtn = document.getElementById('export-csv-btn');
        if (exportBtn) exportBtn.style.display = 'none';
        return;
    }
    
    tbody.innerHTML = trades.map((trade, index) => {
        // Map backend field names to frontend expected names
        const symbol = trade.symbol || trade.ticker || 'N/A';
        const date = trade.date || trade.entry_date || 'N/A';
        const action = trade.action || (trade.status === 'open' ? 'BUY' : 'SELL');
        const shares = trade.shares || 0;
        const price = trade.price || trade.entry_price || 0;
        const value = trade.value || (shares * price);
        const pnl = trade.pnl || trade.pnl_dollars || 0;
        const pnlPercent = trade.pnl_pct || 0;
        const strategy = trade.strategy || 'N/A';
        
        // Determine P&L classes
        const pnlClass = pnl > 0 ? 'positive' : pnl < 0 ? 'negative' : '';
        const pnlPercentClass = pnlPercent > 0 ? 'positive' : pnlPercent < 0 ? 'negative' : '';
        
        return `
            <tr>
                <td style="font-weight: bold; color: #495057;">${index + 1}</td>
                <td>${date}</td>
                <td>${symbol}</td>
                <td>${action}</td>
                <td>${shares.toFixed(2)}</td>
                <td>$${price.toFixed(2)}</td>
                <td>$${value.toFixed(2)}</td>
                <td class="${pnlClass}">${pnl ? `$${pnl.toFixed(2)}` : '-'}</td>
                <td class="${pnlPercentClass}">${pnlPercent ? `${pnlPercent.toFixed(2)}%` : '-'}</td>
                <td>${strategy}</td>
            </tr>
        `;
    }).join('');
    
    // Update the trade count
    const tradeCountElement = document.getElementById('trade-count');
    if (tradeCountElement) {
        tradeCountElement.textContent = trades.length;
        console.log('🔍 DEBUG: Updated trade count to', trades.length);
    }
    
    // Show export button and store trades data
    const exportBtn = document.getElementById('export-csv-btn');
    if (exportBtn) exportBtn.style.display = 'inline-block';
    window.currentTradesData = trades;
}

function displayHistoricalResults(results) {
    console.log('🔍 DEBUG: displayHistoricalResults called with:', results);
    
    if (!results) return;
    
    // Show the historical results section
    const historicalResultsSection = document.getElementById('historical-results');
    if (historicalResultsSection) {
        historicalResultsSection.style.display = 'block';
        console.log('🔍 DEBUG: Showing historical results section');
    }
    
    // Handle different response formats
    let trades = [];
    let summary = {};
    
    if (results.summary && results.trades) {
        // New format with summary and trades
        trades = results.trades;
        summary = results.summary;
        console.log('🔍 DEBUG: Using new format with summary and trades');
    } else if (results.trades) {
        // Just trades array
        trades = results.trades;
        summary = results;
        console.log('🔍 DEBUG: Using trades array format');
    } else {
        console.error('❌ No trades found in results');
        return;
    }
    
    // Store the trades for later use
    window.currentHistoricalTradesData = trades;
    console.log('💾 Stored', trades.length, 'trades in window.currentHistoricalTradesData');
    
    // Update the trade history table with the new data
    updateTradesTable(trades);
    
    // Calculate basic KPIs
    const kpis = calculateBasicKPIs(trades, summary);
    
    console.log('📈 Basic KPI Calculations:', kpis);
    
    // Update KPI displays
    const startingBalanceElement = document.getElementById('starting-balance');
    const endingBalanceElement = document.getElementById('ending-balance');
    const openPositionsBalanceElement = document.getElementById('open-positions-balance');
    const totalTradesElement = document.getElementById('total-trades');
    const closedTradesPnlElement = document.getElementById('closed-trades-pnl');
    const totalPnlElement = document.getElementById('total-pnl');
    
    if (startingBalanceElement) startingBalanceElement.textContent = `$${kpis.startingBalance.toLocaleString()}`;
    if (endingBalanceElement) endingBalanceElement.textContent = `$${kpis.endingBalance.toLocaleString()}`;
    if (openPositionsBalanceElement) openPositionsBalanceElement.textContent = `$${kpis.openPositionsBalance.toLocaleString()}`;
    if (totalTradesElement) totalTradesElement.textContent = kpis.totalTrades;
    if (closedTradesPnlElement) {
        closedTradesPnlElement.textContent = `$${kpis.closedTradesPnl.toLocaleString()}`;
        closedTradesPnlElement.className = `metric-value ${kpis.closedTradesPnl >= 0 ? 'positive' : 'negative'}`;
    }
    if (totalPnlElement) {
        totalPnlElement.textContent = `$${kpis.totalPnl.toLocaleString()}`;
        totalPnlElement.className = `metric-value ${kpis.totalPnl >= 0 ? 'positive' : 'negative'}`;
    }
    
    // Display terminal output if available
    if (results.terminal_output) {
        const logs = document.getElementById('backtest-logs');
        if (logs) {
            logs.innerHTML += `
                <div style="font-family: 'Courier New', monospace; background: #1e1e1e; color: #00ff00; padding: 15px; border-radius: 5px; margin-bottom: 10px; max-height: 400px; overflow-y: auto;">
                    <div style="color: #ffff00;">[${new Date().toLocaleTimeString()}] 📋 Terminal Output:</div>
                    <pre style="color: #00ff00; margin: 10px 0; white-space: pre-wrap;">${results.terminal_output}</pre>
                </div>
            `;
        }
    }
    
    console.log('✅ Historical results displayed successfully');
}

function updateHistoricalTradesTable(trades) {
    console.log('🔍 DEBUG: updateHistoricalTradesTable called with trades length:', trades.length);
    console.log('🔍 DEBUG: First 3 trades for table:', trades.slice(0, 3));
    
    const tbody = document.getElementById('historical-trades-tbody');
    if (!tbody) return;
    
    if (!trades || trades.length === 0) {
        tbody.innerHTML = '<tr><td colspan="9" class="loading">No trades found</td></tr>';
        return;
    }
    
    tbody.innerHTML = '';
    trades.forEach((trade, index) => {
        if (index < 5) { // Only log first 5 trades to avoid spam
            console.log(`🔍 DEBUG: Processing trade ${index + 1}:`, trade);
        }
        
        const row = document.createElement('tr');
        row.innerHTML = `
            <td>${trade.date || 'N/A'}</td>
            <td>${trade.symbol || 'N/A'}</td>
            <td class="${trade.action === 'BUY' ? 'buy' : 'sell'}">${trade.action || 'N/A'}</td>
            <td>${(trade.shares || 0).toFixed(2)}</td>
            <td>$${(trade.price || 0).toFixed(2)}</td>
            <td>$${(trade.value || 0).toFixed(2)}</td>
            <td class="${(trade.pnl || 0) >= 0 ? 'positive' : 'negative'}">$${(trade.pnl || 0).toFixed(2)}</td>
            <td class="${(trade.pnl_pct || 0) >= 0 ? 'positive' : 'negative'}">${(trade.pnl_pct || 0).toFixed(2)}%</td>
            <td>${trade.strategy || 'N/A'}</td>
        `;
        tbody.appendChild(row);
    });
    
    console.log('🔍 DEBUG: Historical trades table updated with', trades.length, 'trades');
}

function clearHistoricalResults() {
    // Hide the historical results section
    const historicalResultsSection = document.getElementById('historical-results');
    if (historicalResultsSection) {
        historicalResultsSection.style.display = 'none';
        console.log('🔍 DEBUG: Hiding historical results section');
    }
    
    // Clear metrics
    const strategyReturn = document.getElementById('historical-strategy-return');
    const benchmarkReturn = document.getElementById('historical-benchmark-return');
    const alphaReturn = document.getElementById('historical-alpha-return');
    const winRateElement = document.getElementById('historical-win-rate');
    const avgTradeReturnElement = document.getElementById('historical-avg-trade-return');
    
    if (strategyReturn) strategyReturn.textContent = '0%';
    if (benchmarkReturn) benchmarkReturn.textContent = '0%';
    if (alphaReturn) alphaReturn.textContent = '0%';
    if (winRateElement) winRateElement.textContent = '0%';
    if (avgTradeReturnElement) avgTradeReturnElement.textContent = '0%';
    
    // Clear trades table
    const tbody = document.getElementById('historical-trades-tbody');
    if (tbody) {
        tbody.innerHTML = '<tr><td colspan="9" class="loading">No trades yet. Run a backtest to see results.</td></tr>';
    }
    
    console.log('🔍 DEBUG: Historical results cleared');
}

function exportToCSV() {
    if (!window.currentHistoricalTradesData || window.currentHistoricalTradesData.length === 0) {
        alert('No trade data to export');
        return;
    }
    
    // Create CSV content
    const headers = ['Date', 'Symbol', 'Action', 'Shares', 'Price', 'Value', 'P&L', 'P&L %', 'Strategy'];
    const csvContent = [
        headers.join(','),
        ...window.currentHistoricalTradesData.map(trade => [
            trade.date,
            trade.symbol,
            trade.action,
            trade.shares?.toFixed(2) || '',
            trade.price?.toFixed(2) || '',
            trade.value?.toFixed(2) || '',
            trade.pnl?.toFixed(2) || '',
            trade.pnl_pct?.toFixed(2) || '',
            trade.strategy || ''
        ].join(','))
    ].join('\n');
    
    // Create and download file
    const blob = new Blob([csvContent], { type: 'text/csv' });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `historical_backtest_${new Date().toISOString().split('T')[0]}.csv`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    window.URL.revokeObjectURL(url);
} 

// DISABLED: Auto-refresh functionality to prevent trade history from vanishing
function checkBacktestStatus() {
    // Auto-refresh disabled to prevent trade history from vanishing
    console.log('ℹ️ Auto-refresh disabled - trade history will persist');
    return;
    
    // Original code commented out:
    /*
    fetch('/api/trades/backtest-status')
        .then(response => response.json())
        .then(data => {
            if (data.success && data.has_results) {
                console.log('✅ Backtest results available:', data.trade_count, 'trades');
                // Reload the trade history with the available data
                loadTradeHistory();
            } else {
                console.log('ℹ️ No backtest results available');
            }
        })
        .catch(error => {
            console.error('❌ Error checking backtest status:', error);
        });
    */
} 

// Initialize dashboard when page loads
document.addEventListener('DOMContentLoaded', function() {
    console.log('🚀 Dashboard initializing...');
    
    // Initialize trade history
    console.log('📄 Initializing trade history...');
    initializeTradeHistory();
    
    // Set up tab switching
    console.log('🔧 Setting up tab switching...');
    document.querySelectorAll('.tab-button').forEach(button => {
        button.addEventListener('click', () => {
            // Remove active class from all buttons and content
            document.querySelectorAll('.tab-button').forEach(btn => btn.classList.remove('active'));
            document.querySelectorAll('.tab-content').forEach(content => content.classList.remove('active'));
            
            // Add active class to clicked button and corresponding content
            button.classList.add('active');
            const tabId = button.getAttribute('data-tab');
            document.getElementById(tabId).classList.add('active');
        });
    });

    // Historical Backtest Form
    const backtestForm = document.getElementById('backtest-form');
    if (backtestForm) {
        backtestForm.addEventListener('submit', function(e) {
            e.preventDefault();
            
            const formData = new FormData(this);
            const data = {
                period: formData.get('period'),
                strategy: formData.get('strategy'),
                profile: formData.get('profile'),
                benchmark: formData.get('benchmark')
            };
            
            runHistoricalBacktest(data);
        });
    }
    
    // Export CSV button
    const exportBtn = document.getElementById('export-csv-btn');
    if (exportBtn) {
        exportBtn.addEventListener('click', exportToCSV);
    }
    
    // Clear Historical Results Button
    const clearHistoricalResultsBtn = document.getElementById('clear-historical-results-btn');
    if (clearHistoricalResultsBtn) {
        clearHistoricalResultsBtn.addEventListener('click', clearHistoricalResults);
    }
    
    // Add event listener for custom date range
    const periodSelect = document.getElementById('period');
    const customDateRange = document.getElementById('custom-date-range');
    const customDateRangeEnd = document.getElementById('custom-date-range-end');
    
    if (periodSelect) {
        periodSelect.addEventListener('change', function() {
            if (this.value === 'custom') {
                customDateRange.style.display = 'block';
                customDateRangeEnd.style.display = 'block';
            } else {
                customDateRange.style.display = 'none';
                customDateRangeEnd.style.display = 'none';
            }
        });
    }
    
    // DISABLED: Initial load timeout to prevent interference
    // setTimeout(() => {
    //     console.log('🔄 Loading trade history...');
    //     loadTradeHistory();
    // }, 1000);
    
    console.log('✅ Dashboard initialized');
}); 

function calculateBasicKPIs(trades, summary = {}) {
    console.log('🔍 DEBUG: Calculating basic KPIs from', trades.length, 'trades');
    
    // Initialize values
    const startingBalance = 100000; // Default starting balance
    let endingBalance = startingBalance;
    let openPositionsBalance = 0;
    let closedTradesPnl = 0;
    let totalPnl = 0;
    
    // Group trades by symbol to calculate positions
    const positions = {};
    const closedTrades = [];
    
    // Process all trades
    trades.forEach(trade => {
        // Handle different trade formats (backtest vs database)
        const symbol = trade.symbol || trade.ticker;
        const action = trade.action || (trade.exit_date ? 'SELL' : 'BUY');
        const shares = trade.shares || 0;
        const price = trade.price || trade.entry_price || trade.exit_price || 0;
        const value = trade.value || (shares * price);
        
        if (!positions[symbol]) {
            positions[symbol] = {
                shares: 0,
                avgPrice: 0,
                totalCost: 0
            };
        }
        
        if (action === 'BUY' || !trade.exit_date) {
            // Add to position
            const newShares = positions[symbol].shares + shares;
            const newTotalCost = positions[symbol].totalCost + value;
            positions[symbol].shares = newShares;
            positions[symbol].totalCost = newTotalCost;
            positions[symbol].avgPrice = newTotalCost / newShares;
            
            // Update ending balance (cash spent)
            endingBalance -= value;
        } else if (action === 'SELL' && trade.exit_date) {
            // Close position
            const sharesSold = shares;
            const avgPrice = positions[symbol].avgPrice;
            const costBasis = sharesSold * avgPrice;
            const proceeds = value;
            const pnl = proceeds - costBasis;
            
            // Update position
            positions[symbol].shares -= sharesSold;
            positions[symbol].totalCost -= costBasis;
            
            if (positions[symbol].shares === 0) {
                positions[symbol].avgPrice = 0;
            } else {
                positions[symbol].avgPrice = positions[symbol].totalCost / positions[symbol].shares;
            }
            
            // Add to closed trades P&L
            closedTradesPnl += pnl;
            
            // Update ending balance (cash received)
            endingBalance += proceeds;
            
            // Record closed trade
            closedTrades.push({
                ...trade,
                pnl: pnl,
                costBasis: costBasis
            });
        }
    });
    
    // Calculate open positions balance and unrealized P&L
    let unrealizedPnl = 0;
    Object.keys(positions).forEach(symbol => {
        const position = positions[symbol];
        if (position.shares > 0) {
            // Use the last trade price as current price
            const lastTrade = trades.filter(t => (t.symbol || t.ticker) === symbol).pop();
            if (lastTrade) {
                const currentPrice = lastTrade.price || lastTrade.entry_price || lastTrade.exit_price || 0;
                const positionValue = position.shares * currentPrice;
                openPositionsBalance += positionValue;
                unrealizedPnl += positionValue - position.totalCost;
            }
        }
    });
    
    // Calculate total P&L (realized + unrealized)
    totalPnl = closedTradesPnl + unrealizedPnl;
    
    // Update ending balance to include open positions
    endingBalance += openPositionsBalance;
    
    console.log('📊 Basic KPI Calculations:', {
        startingBalance,
        endingBalance,
        openPositionsBalance,
        totalTrades: trades.length,
        closedTradesPnl,
        totalPnl,
        positions: Object.keys(positions).length
    });
    
    return {
        startingBalance,
        endingBalance,
        openPositionsBalance,
        totalTrades: trades.length,
        closedTradesPnl,
        totalPnl
    };
} 