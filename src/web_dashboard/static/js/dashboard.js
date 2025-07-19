// Dashboard JavaScript - All functionality moved from inline scripts

// Global variables
let currentTab = 'overview';
let socket = null;
let currentSearchResult = null;

// Initialize dashboard when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    console.log('Dashboard JavaScript loaded');
    initializeDashboard();
});

function initializeDashboard() {
    // Initialize socket connection
    initializeSocket();
    
    // Setup event listeners
    setupEventListeners();
    
    // Load initial data
    loadInitialData();
    
    // Initialize backtest date range
    initializeBacktestDates();
    
    // Initialize historical backtest
    initializeHistoricalBacktest();
}

function initializeSocket() {
    try {
        socket = io();
        
        socket.on('connect', function() {
            console.log('Connected to server');
        });
        
        socket.on('disconnect', function() {
            console.log('Disconnected from server');
        });
        
        socket.on('portfolio_update', function(data) {
            updatePortfolioDisplay(data);
        });
        
        socket.on('trade_update', function(data) {
            updateTradeHistory(data);
        });
        
    } catch (error) {
        console.error('Socket initialization failed:', error);
    }
}

function setupEventListeners() {
    // Tab switching
    const tabButtons = document.querySelectorAll('[data-tab]');
    tabButtons.forEach(button => {
        button.addEventListener('click', function() {
            const tabName = this.getAttribute('data-tab');
            showTab(tabName, this);
        });
    });
    
    // Backtest button
    const runBacktestBtn = document.getElementById('run-backtest-btn');
    if (runBacktestBtn) {
        runBacktestBtn.addEventListener('click', runBacktest);
    }
    
    // Strategy selection
    const strategySelect = document.getElementById('backtest-strategy');
    if (strategySelect) {
        strategySelect.addEventListener('change', updateStrategyDescription);
    }
    
    // Profile selection
    const profileSelect = document.getElementById('backtest-profile');
    if (profileSelect) {
        profileSelect.addEventListener('change', updateStrategyDescription);
    }
    
    // Trading controls
    const startTradingBtn = document.getElementById('start-trading-btn');
    const stopTradingBtn = document.getElementById('stop-trading-btn');
    
    if (startTradingBtn) {
        startTradingBtn.addEventListener('click', startTrading);
    }
    
    if (stopTradingBtn) {
        stopTradingBtn.addEventListener('click', stopTrading);
    }
    
    // Search functionality
    const searchBtn = document.getElementById('search-ticker-btn');
    const addBtn = document.getElementById('add-ticker-btn');
    const searchInput = document.getElementById('ticker-search');
    
    if (searchBtn) {
        searchBtn.addEventListener('click', searchTicker);
    }
    
    if (addBtn) {
        addBtn.addEventListener('click', addTickerToWatchlist);
    }
    
    if (searchInput) {
        searchInput.addEventListener('keypress', function(e) {
            if (e.key === 'Enter') {
                searchTicker();
            }
        });
    }
    
    // Symbol search functionality for backtesting
    const symbolSearchInput = document.getElementById('symbol-search');
    const symbolSearchBtn = document.getElementById('search-symbol-btn');
    const symbolSelect = document.getElementById('backtest-symbol');
    
    if (symbolSearchInput) {
        symbolSearchInput.addEventListener('input', debounce(searchSymbols, 300));
        symbolSearchInput.addEventListener('focus', function() {
            if (this.value.length > 0) {
                searchSymbols();
            }
        });
    }
    
    if (symbolSearchBtn) {
        symbolSearchBtn.addEventListener('click', searchSymbols);
    }
    
    // Close search results when clicking outside
    document.addEventListener('click', function(e) {
        const searchResults = document.getElementById('symbol-search-results');
        const searchInput = document.getElementById('symbol-search');
        if (searchResults && !searchInput.contains(e.target) && !searchResults.contains(e.target)) {
            searchResults.style.display = 'none';
        }
    });
    
    // Modal close button
    const closeModalBtn = document.getElementById('close-modal-btn');
    if (closeModalBtn) {
        closeModalBtn.addEventListener('click', closeTradeModal);
    }
    
    // Close modal when clicking outside
    window.addEventListener('click', function(event) {
        const modal = document.getElementById('tradeModal');
        if (event.target === modal) {
            modal.style.display = 'none';
        }
    });
    
    // Automation controls
    const startAutomationBtn = document.getElementById('start-automation-btn');
    const stopAutomationBtn = document.getElementById('stop-automation-btn');
    const runCycleBtn = document.getElementById('run-cycle-btn');
    const saveConfigBtn = document.getElementById('save-config-btn');
    const clearLogsBtn = document.getElementById('clear-logs-btn');
    const exportLogsBtn = document.getElementById('export-logs-btn');
    const addToWatchlistBtn = document.getElementById('add-to-watchlist-btn');
    
    if (startAutomationBtn) {
        startAutomationBtn.addEventListener('click', startAutomation);
    }
    
    if (stopAutomationBtn) {
        stopAutomationBtn.addEventListener('click', stopAutomation);
    }
    
    if (runCycleBtn) {
        runCycleBtn.addEventListener('click', runAutomationCycle);
    }
    
    if (saveConfigBtn) {
        saveConfigBtn.addEventListener('click', saveAutomationConfig);
    }
    
    if (clearLogsBtn) {
        clearLogsBtn.addEventListener('click', clearAutomationLogs);
    }
    
    if (exportLogsBtn) {
        exportLogsBtn.addEventListener('click', exportAutomationLogs);
    }
    
    if (addToWatchlistBtn) {
        addToWatchlistBtn.addEventListener('click', addToAutomationWatchlist);
    }
    
    // Historical backtest strategy and profile selection
    const historicalStrategySelect = document.getElementById('historical-backtest-strategy');
    const historicalProfileSelect = document.getElementById('historical-backtest-profile');
    if (historicalStrategySelect) {
        historicalStrategySelect.addEventListener('change', updateHistoricalStrategyDescription);
    }
    if (historicalProfileSelect) {
        historicalProfileSelect.addEventListener('change', updateHistoricalStrategyDescription);
    }
    
    // Historical backtest button
    const runHistoricalBacktestBtn = document.getElementById('run-historical-backtest-btn');
    if (runHistoricalBacktestBtn) {
        runHistoricalBacktestBtn.addEventListener('click', runHistoricalBacktest);
    }
    
    // Clear historical results button
    const clearHistoricalResultsBtn = document.getElementById('clear-historical-results-btn');
    if (clearHistoricalResultsBtn) {
        clearHistoricalResultsBtn.addEventListener('click', clearHistoricalResults);
    }
}

function loadInitialData() {
    // Load portfolio data
    fetch('/api/portfolio')
        .then(response => response.json())
        .then(data => {
            updatePortfolioDisplay(data);
        })
        .catch(error => {
            console.error('Error loading portfolio:', error);
        });
    
    // Load trading status
    fetch('/api/trading/status')
        .then(response => response.json())
        .then(data => {
            updateTradingStatus(data);
        })
        .catch(error => {
            console.error('Error loading trading status:', error);
        });
    
    // Load tickers data
    loadTickersData();
    
    // Load trades data
    loadTradesData();
    
    // Load market indexes
    loadMarketIndexes();
    
    // Set up periodic refresh for market indexes
    setInterval(loadMarketIndexes, 30000); // Refresh every 30 seconds
}

function loadTickersData() {
    console.log('loadTickersData called');
    const tbody = document.getElementById('tickers-tbody');
    if (!tbody) {
        console.error('tickers-tbody not found');
        return;
    }
    tbody.innerHTML = '<tr><td colspan="10" class="loading">Loading tickers...</td></tr>';

    // Simulate ticker data (in real implementation, this would come from API)
    const tickers = [
        { symbol: 'AAPL', price: 218.50, score: 85, macd: 'bullish', rsi: 65, ema: 'above', bb: 'upper', volume: 'high', signal: 'buy' },
        { symbol: 'MSFT', price: 415.20, score: 78, macd: 'neutral', rsi: 55, ema: 'above', bb: 'middle', volume: 'medium', signal: 'hold' },
        { symbol: 'GOOGL', price: 185.30, score: 92, macd: 'bullish', rsi: 70, ema: 'above', bb: 'upper', volume: 'high', signal: 'buy' },
        { symbol: 'TSLA', price: 245.80, score: 45, macd: 'bearish', rsi: 35, ema: 'below', bb: 'lower', volume: 'low', signal: 'sell' },
        { symbol: 'AMZN', price: 178.90, score: 67, macd: 'neutral', rsi: 50, ema: 'above', bb: 'middle', volume: 'medium', signal: 'hold' }
    ];

    updateTickersTable(tickers);
    console.log('Tickers data loaded successfully');
}

function loadTradesData() {
    const tbody = document.getElementById('trades-tbody');
    if (!tbody) return;
    
    tbody.innerHTML = '<tr><td colspan="8" class="loading">Loading trades...</td></tr>';

    // Fetch real trades from database
    fetch('/api/trades/stored?limit=50')
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                updateTradesTable(data.trades);
                loadTradeStatistics(); // Load statistics after trades
            } else {
                console.error('Error loading trades:', data.error);
                tbody.innerHTML = '<tr><td colspan="8" class="error">Error loading trades</td></tr>';
            }
        })
        .catch(error => {
            console.error('Error loading trades:', error);
            tbody.innerHTML = '<tr><td colspan="8" class="error">Error loading trades</td></tr>';
        });
}

function loadTradeStatistics() {
    fetch('/api/trades/statistics')
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                updateTradeStatistics(data.statistics);
            } else {
                console.error('Error loading trade statistics:', data.error);
            }
        })
        .catch(error => {
            console.error('Error loading trade statistics:', error);
        });
}

function updateTradeStatistics(stats) {
    const totalTrades = document.getElementById('total-trades');
    const winRate = document.getElementById('win-rate');
    const avgPnl = document.getElementById('avg-pnl');
    const totalPnl = document.getElementById('total-pnl');
    
    if (totalTrades) totalTrades.textContent = stats.total_trades || 0;
    if (winRate) winRate.textContent = `${(stats.win_rate || 0).toFixed(1)}%`;
    if (avgPnl) {
        avgPnl.textContent = `${(stats.avg_pnl_pct || 0).toFixed(2)}%`;
        avgPnl.className = `stat-value ${(stats.avg_pnl_pct || 0) >= 0 ? 'positive' : 'negative'}`;
    }
    if (totalPnl) {
        totalPnl.textContent = `$${(stats.total_pnl_dollars || 0).toFixed(2)}`;
        totalPnl.className = `stat-value ${(stats.total_pnl_dollars || 0) >= 0 ? 'positive' : 'negative'}`;
    }
}

function updateTickersTable(tickers) {
    const tbody = document.getElementById('tickers-tbody');
    if (!tbody) return;
    
    tbody.innerHTML = '';

    tickers.forEach(ticker => {
        const row = document.createElement('tr');
        row.innerHTML = `
            <td><strong>${ticker.symbol}</strong></td>
            <td>$${ticker.price.toFixed(2)}</td>
            <td><span class="score-badge ${getScoreClass(ticker.score)}">${ticker.score}</span></td>
            <td><span class="indicator-status ${getIndicatorClass(ticker.macd)}">${ticker.macd}</span></td>
            <td><span class="indicator-status ${getIndicatorClass(ticker.rsi)}">${ticker.rsi}</span></td>
            <td><span class="indicator-status ${getIndicatorClass(ticker.ema)}">${ticker.ema}</span></td>
            <td><span class="indicator-status ${getIndicatorClass(ticker.bb)}">${ticker.bb}</span></td>
            <td><span class="indicator-status ${getIndicatorClass(ticker.volume)}">${ticker.volume}</span></td>
            <td><span class="indicator-status ${getSignalClass(ticker.signal)}">${ticker.signal.toUpperCase()}</span></td>
            <td>
                <button class="btn btn-danger remove-ticker-btn" data-symbol="${ticker.symbol}" style="padding: 5px 10px; font-size: 12px;">Remove</button>
            </td>
        `;
        tbody.appendChild(row);
    });

    // Add event listeners to remove buttons
    const removeButtons = tbody.querySelectorAll('.remove-ticker-btn');
    removeButtons.forEach(button => {
        button.addEventListener('click', function() {
            const symbol = this.getAttribute('data-symbol');
            removeTicker(symbol);
        });
    });
}

function searchTicker() {
    const searchInput = document.getElementById('ticker-search');
    const symbol = searchInput.value.trim().toUpperCase();
    const searchResults = document.getElementById('search-results');
    const addTickerBtn = document.getElementById('add-ticker-btn');

    if (!symbol) {
        showMessage('Please enter a ticker symbol', 'error');
        return;
    }

    // Show loading state
    searchResults.innerHTML = '<div class="loading">Searching for ticker...</div>';
    searchResults.style.display = 'block';
    addTickerBtn.style.display = 'none';

    // Simulate API call to search for ticker
    setTimeout(() => {
        // Simulate finding ticker data
        const mockTickerData = {
            symbol: symbol,
            name: `${symbol} Company`,
            price: Math.random() * 500 + 50,
            change: (Math.random() - 0.5) * 10,
            volume: Math.floor(Math.random() * 1000000),
            marketCap: Math.floor(Math.random() * 1000000000)
        };

        currentSearchResult = mockTickerData;
        
        searchResults.innerHTML = `
            <div style="background: white; padding: 15px; border-radius: 8px; border: 1px solid #ddd;">
                <h4 style="margin-bottom: 10px; color: #2c3e50;">${mockTickerData.name} (${mockTickerData.symbol})</h4>
                <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr)); gap: 10px;">
                    <div>
                        <strong>Price:</strong> $${mockTickerData.price.toFixed(2)}
                    </div>
                    <div>
                        <strong>Change:</strong> 
                        <span class="${mockTickerData.change >= 0 ? 'positive' : 'negative'}">
                            ${mockTickerData.change >= 0 ? '+' : ''}$${mockTickerData.change.toFixed(2)}
                        </span>
                    </div>
                    <div>
                        <strong>Volume:</strong> ${mockTickerData.volume.toLocaleString()}
                    </div>
                    <div>
                        <strong>Market Cap:</strong> $${(mockTickerData.marketCap / 1000000).toFixed(1)}M
                    </div>
                </div>
            </div>
        `;
        
        addTickerBtn.style.display = 'inline-block';
    }, 1000);
}

function addTickerToWatchlist() {
    if (!currentSearchResult) {
        showMessage('No ticker selected', 'error');
        return;
    }

    console.log('Adding ticker to watchlist:', currentSearchResult.symbol);
    
    // Simulate adding to watchlist
    const newTicker = {
        symbol: currentSearchResult.symbol,
        price: currentSearchResult.price,
        score: Math.floor(Math.random() * 100),
        macd: ['bullish', 'bearish', 'neutral'][Math.floor(Math.random() * 3)],
        rsi: Math.floor(Math.random() * 100),
        ema: ['above', 'below', 'middle'][Math.floor(Math.random() * 3)],
        bb: ['upper', 'lower', 'middle'][Math.floor(Math.random() * 3)],
        volume: ['high', 'medium', 'low'][Math.floor(Math.random() * 3)],
        signal: ['buy', 'sell', 'hold'][Math.floor(Math.random() * 3)]
    };

    // Add to current tickers list
    const currentTickers = getCurrentTickers();
    currentTickers.push(newTicker);
    updateTickersTable(currentTickers);

    // Clear search
    document.getElementById('ticker-search').value = '';
    document.getElementById('search-results').style.display = 'none';
    document.getElementById('add-ticker-btn').style.display = 'none';
    currentSearchResult = null;

    showMessage(`Added ${newTicker.symbol} to watchlist`, 'success');
}

function searchSymbols() {
    const searchInput = document.getElementById('symbol-search');
    const searchResults = document.getElementById('symbol-search-results');
    const symbolSelect = document.getElementById('backtest-symbol');
    
    if (!searchInput || !searchResults) return;
    
    const query = searchInput.value.trim().toUpperCase();
    if (!query) {
        searchResults.style.display = 'none';
        return;
    }
    
    // Fetch symbols from API
    fetch(`/api/symbols/search?q=${encodeURIComponent(query)}`)
        .then(response => response.json())
        .then(data => {
            if (data.success && data.symbols.length > 0) {
                displaySymbolSearchResults(data.symbols);
            } else {
                searchResults.style.display = 'none';
            }
        })
        .catch(error => {
            console.error('Error searching symbols:', error);
            searchResults.style.display = 'none';
        });
}

function displaySymbolSearchResults(symbols) {
    const searchResults = document.getElementById('symbol-search-results');
    if (!searchResults) return;
    
    searchResults.innerHTML = '';
    
    symbols.forEach(symbol => {
        const div = document.createElement('div');
        div.className = 'search-result-item';
        div.style.cssText = 'padding: 8px 12px; cursor: pointer; border-bottom: 1px solid #eee; font-size: 14px;';
        div.textContent = symbol;
        
        div.addEventListener('click', function() {
            const symbolSelect = document.getElementById('backtest-symbol');
            const searchInput = document.getElementById('symbol-search');
            
            // Add to select if not already present
            let option = symbolSelect.querySelector(`option[value="${symbol}"]`);
            if (!option) {
                option = document.createElement('option');
                option.value = symbol;
                option.textContent = symbol;
                symbolSelect.appendChild(option);
            }
            
            symbolSelect.value = symbol;
            searchInput.value = symbol;
            searchResults.style.display = 'none';
            
            // Update benchmark to use selected symbol
            updateBenchmarkForSymbol(symbol);
        });
        
        div.addEventListener('mouseenter', function() {
            this.style.backgroundColor = '#f0f0f0';
        });
        
        div.addEventListener('mouseleave', function() {
            this.style.backgroundColor = '';
        });
        
        searchResults.appendChild(div);
    });
    
    searchResults.style.display = 'block';
}

function updateBenchmarkForSymbol(symbol) {
    // Update benchmark display to show that it will use the selected symbol
    const benchmarkReturn = document.getElementById('benchmark-return');
    if (benchmarkReturn) {
        benchmarkReturn.textContent = `${symbol} Benchmark`;
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

function removeTicker(symbol) {
    console.log('Removing ticker from watchlist:', symbol);
    
    const currentTickers = getCurrentTickers();
    const updatedTickers = currentTickers.filter(ticker => ticker.symbol !== symbol);
    updateTickersTable(updatedTickers);

    showMessage(`Removed ${symbol} from watchlist`, 'success');
}

function getCurrentTickers() {
    // In real implementation, this would come from your backend API
    return [
        { symbol: 'AAPL', price: 218.50, score: 85, macd: 'bullish', rsi: 65, ema: 'above', bb: 'upper', volume: 'high', signal: 'buy' },
        { symbol: 'MSFT', price: 415.20, score: 78, macd: 'neutral', rsi: 55, ema: 'above', bb: 'middle', volume: 'medium', signal: 'hold' },
        { symbol: 'GOOGL', price: 185.30, score: 92, macd: 'bullish', rsi: 70, ema: 'above', bb: 'upper', volume: 'high', signal: 'buy' },
        { symbol: 'TSLA', price: 245.80, score: 45, macd: 'bearish', rsi: 35, ema: 'below', bb: 'lower', volume: 'low', signal: 'sell' },
        { symbol: 'AMZN', price: 178.90, score: 67, macd: 'neutral', rsi: 50, ema: 'above', bb: 'middle', volume: 'medium', signal: 'hold' }
    ];
}

function updateTradesTable(trades) {
    const tbody = document.getElementById('trades-tbody');
    if (!tbody) return;
    
    tbody.innerHTML = '';

    if (trades.length === 0) {
        tbody.innerHTML = '<tr><td colspan="8" class="no-data">No trades found</td></tr>';
        return;
    }

    trades.forEach((trade, index) => {
        const row = document.createElement('tr');
        row.addEventListener('click', () => showTradeDetails(trade));
        row.style.cursor = 'pointer';
        
        // Format dates
        const entryDate = new Date(trade.entry_date).toLocaleDateString();
        const exitDate = trade.exit_date ? new Date(trade.exit_date).toLocaleDateString() : 'Open';
        
        // Calculate P&L
        const pnlPct = trade.pnl_pct || 0;
        const pnlDollars = trade.pnl_dollars || 0;
        
        row.innerHTML = `
            <td>${entryDate}</td>
            <td><strong>${trade.ticker}</strong></td>
            <td><span class="indicator-status ${pnlPct >= 0 ? 'indicator-bullish' : 'indicator-bearish'}">${pnlPct >= 0 ? 'WIN' : 'LOSS'}</span></td>
            <td>${trade.shares?.toFixed(2) || 'N/A'}</td>
            <td>$${trade.entry_price?.toFixed(2) || 'N/A'}</td>
            <td class="${pnlDollars >= 0 ? 'positive' : 'negative'}">$${pnlDollars?.toFixed(2) || 'N/A'}</td>
            <td>${trade.strategy}</td>
            <td><span class="indicator-status ${trade.status === 'closed' ? 'indicator-bullish' : 'indicator-neutral'}">${trade.status}</span></td>
        `;
        tbody.appendChild(row);
    });
}

function getScoreClass(score) {
    if (score >= 80) return 'score-high';
    if (score >= 60) return 'score-medium';
    return 'score-low';
}

function getIndicatorClass(indicator) {
    if (indicator === 'bullish' || indicator === 'above' || indicator === 'upper' || indicator === 'high') return 'indicator-bullish';
    if (indicator === 'bearish' || indicator === 'below' || indicator === 'lower' || indicator === 'low') return 'indicator-bearish';
    return 'indicator-neutral';
}

function getSignalClass(signal) {
    if (signal === 'buy') return 'indicator-bullish';
    if (signal === 'sell') return 'indicator-bearish';
    return 'indicator-neutral';
}

function showTradeDetails(trade) {
    const modal = document.getElementById('tradeModal');
    const title = document.getElementById('modal-title');
    const content = document.getElementById('modal-content');

    title.textContent = `Trade Details - ${trade.ticker}`;
    
    // Format dates
    const entryDate = new Date(trade.entry_date).toLocaleDateString();
    const exitDate = trade.exit_date ? new Date(trade.exit_date).toLocaleDateString() : 'Open';
    
    // Calculate P&L
    const pnlPct = trade.pnl_pct || 0;
    const pnlDollars = trade.pnl_dollars || 0;
    const totalValue = (trade.entry_price * trade.shares) || 0;
    
    content.innerHTML = `
        <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 20px;">
            <div>
                <h3>Trade Information</h3>
                <p><strong>Entry Date:</strong> ${entryDate}</p>
                <p><strong>Exit Date:</strong> ${exitDate}</p>
                <p><strong>Symbol:</strong> ${trade.ticker}</p>
                <p><strong>Strategy:</strong> ${trade.strategy}</p>
                <p><strong>Shares:</strong> ${trade.shares?.toFixed(2) || 'N/A'}</p>
                <p><strong>Entry Price:</strong> $${trade.entry_price?.toFixed(2) || 'N/A'}</p>
                <p><strong>Exit Price:</strong> $${trade.exit_price?.toFixed(2) || 'N/A'}</p>
                <p><strong>Status:</strong> ${trade.status}</p>
            </div>
            <div>
                <h3>Performance</h3>
                <p><strong>P&L:</strong> <span class="${pnlDollars >= 0 ? 'positive' : 'negative'}">$${pnlDollars?.toFixed(2) || 'N/A'}</span></p>
                <p><strong>P&L %:</strong> <span class="${pnlPct >= 0 ? 'positive' : 'negative'}">${pnlPct?.toFixed(2) || 'N/A'}%</span></p>
                <p><strong>Total Value:</strong> $${totalValue?.toFixed(2) || 'N/A'}</p>
            </div>
        </div>
        <div style="margin-top: 20px;">
            <h3>Trade Analysis</h3>
            <p><strong>Entry Reason:</strong> ${trade.entry_reason || 'N/A'}</p>
            <p><strong>Exit Reason:</strong> ${trade.exit_reason || 'N/A'}</p>
        </div>
        <div style="margin-top: 20px;">
            <h3>What I Learned</h3>
            <textarea id="what-learned-text" rows="4" style="width: 100%; padding: 10px; border: 1px solid #ddd; border-radius: 4px;">${trade.what_learned || ''}</textarea>
            <button onclick="saveTradeLearning(${trade.id})" style="margin-top: 10px; padding: 8px 16px; background: #3498db; color: white; border: none; border-radius: 4px; cursor: pointer;">Save Learning</button>
        </div>
    `;

    modal.style.display = 'block';
}

function saveTradeLearning(tradeId) {
    const whatLearned = document.getElementById('what-learned-text').value;
    
    fetch(`/api/trades/${tradeId}/learning`, {
        method: 'PUT',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            what_learned: whatLearned
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            alert('Learning saved successfully!');
        } else {
            alert('Error saving learning: ' + data.error);
        }
    })
    .catch(error => {
        console.error('Error saving learning:', error);
        alert('Error saving learning');
    });
}

function closeTradeModal() {
    document.getElementById('tradeModal').style.display = 'none';
}

function showTab(tabName, button) {
    console.log('Showing tab:', tabName);
    
    // Remove active class from all buttons
    document.querySelectorAll('[data-tab]').forEach(btn => {
        btn.classList.remove('active');
    });
    
    // Hide all tab content
    document.querySelectorAll('.tab-content').forEach(content => {
        content.style.display = 'none';
    });
    
    // Show selected tab content
    const tabContent = document.getElementById(tabName);
    if (tabContent) {
        tabContent.style.display = 'block';
        console.log('Showing tab content:', tabName);
    }
    
    // Add active class to clicked button
    if (button) {
        button.classList.add('active');
    }
    
    currentTab = tabName;
    
    // Load data based on tab
    switch(tabName) {
        case 'tickers':
            loadTickersData();
            break;
        case 'trades':
            loadTradesData();
            break;
        case 'automation':
            loadAutomationData();
            break;
    }
}

function runBacktest() {
    const symbol = document.getElementById('backtest-symbol').value;
    const strategy = document.getElementById('backtest-strategy').value;
    const profile = document.getElementById('backtest-profile').value;
    const startDate = document.getElementById('backtest-start-date').value;
    const endDate = document.getElementById('backtest-end-date').value;
    const resultsDiv = document.getElementById('backtest-results');
    const logContainer = document.getElementById('backtest-log-content');

    // Validate dates
    if (!startDate || !endDate) {
        showError('Please select both start and end dates');
        return;
    }
    
    if (startDate >= endDate) {
        showError('Start date must be before end date');
        return;
    }

    // Show results container and clear previous results
    resultsDiv.style.display = 'block';
    
    // Clear previous results by resetting individual elements
    const totalTradesElement = document.getElementById('total-trades');
    const totalReturnElement = document.getElementById('total-return');
    const finalValueElement = document.getElementById('final-value');
    const sharpeRatioElement = document.getElementById('sharpe-ratio');
    const tradeTbody = document.getElementById('trade-details-tbody');
    
    if (totalTradesElement) totalTradesElement.textContent = '0';
    if (totalReturnElement) totalReturnElement.textContent = '0%';
    if (finalValueElement) finalValueElement.textContent = '$0';
    if (sharpeRatioElement) sharpeRatioElement.textContent = '0.00';
    if (tradeTbody) tradeTbody.innerHTML = '<tr><td colspan="7" style="padding: 20px; text-align: center; color: #7f8c8d;">Running backtest...</td></tr>';
    
    // Clear and initialize log display
    if (logContainer) {
        logContainer.innerHTML = '<span style="color: #00ff00;">🚀 Starting backtest for ' + symbol + ' with ' + strategy + ' (' + profile + ') strategy...</span><br>';
        logContainer.innerHTML += '<span style="color: #00ff00;">📅 Period: ' + startDate + ' to ' + endDate + '</span><br>';
        logContainer.innerHTML += '<span style="color: #00ff00;">🏆 Benchmark: ' + symbol + '</span><br>';
    }

    fetch('/api/backtest', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            symbol: symbol,
            strategy: strategy,
            profile: profile,
            start_date: startDate,
            end_date: endDate,
            parameters: getCustomParameters(), // Pass custom parameters
            benchmark: symbol // Use selected symbol as benchmark
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.error) {
            showError('Backtest failed: ' + data.error);
            if (logContainer) {
                logContainer.innerHTML += '<span style="color: #ff0000;">❌ Backtest failed: ' + data.error + '</span><br>';
            }
            return;
        }
        
        displayBacktestResults(data);
        
        if (logContainer) {
            logContainer.innerHTML += '<span style="color: #00ff00;">✅ Backtest completed successfully!</span><br>';
            logContainer.innerHTML += '<span style="color: #00ff00;">📊 Total trades: ' + (data.trades ? data.trades.length : 0) + '</span><br>';
            if (data.performance) {
                logContainer.innerHTML += '<span style="color: #00ff00;">💰 Total return: ' + data.performance.total_return.toFixed(2) + '%</span><br>';
                logContainer.innerHTML += '<span style="color: #00ff00;">📈 Sharpe ratio: ' + data.performance.sharpe_ratio.toFixed(2) + '</span><br>';
            }
        }
    })
    .catch(error => {
        console.error('Error:', error);
        showError('Failed to run backtest: ' + error.message);
        if (logContainer) {
            logContainer.innerHTML += '<span style="color: #ff0000;">❌ Error: ' + error.message + '</span><br>';
        }
    });
}

function displayBacktestResults(results) {
    console.log('displayBacktestResults called with:', results);
    
    // Make backtest results visible
    const backtestResultsElement = document.getElementById('backtest-results');
    if (backtestResultsElement) {
        backtestResultsElement.style.display = 'block';
    }
    
    if (results.error) {
        showError(results.error);
        return;
    }
    
    // Extract data from results - handle both old and new structure
    const trades = results.trades || [];
    const performance = results.performance || {};
    const totalTrades = performance.total_trades || trades.length || 0;
    const finalValue = performance.final_value || 0;
    const totalReturn = performance.total_return || 0;
    const sharpeRatio = performance.sharpe_ratio || 0;
    
    console.log('Parsed data:', { totalTrades, finalValue, totalReturn, sharpeRatio, tradesCount: trades.length });
    
    // Update summary metrics
    const totalTradesElement = document.getElementById('total-trades');
    const totalReturnElement = document.getElementById('total-return');
    const finalValueElement = document.getElementById('final-value');
    const sharpeRatioElement = document.getElementById('sharpe-ratio');
    
    if (totalTradesElement) totalTradesElement.textContent = totalTrades;
    if (totalReturnElement) {
        totalReturnElement.textContent = `${totalReturn.toFixed(2)}%`;
        totalReturnElement.style.color = totalReturn >= 0 ? '#27ae60' : '#e74c3c';
    }
    if (finalValueElement) finalValueElement.textContent = formatCurrency(finalValue);
    if (sharpeRatioElement) sharpeRatioElement.textContent = sharpeRatio.toFixed(3);
    
    // Update CLI-like output with trade details
    const logContainer = document.getElementById('backtest-log-content');
    if (logContainer) {
        logContainer.innerHTML += '<span style="color: #ffff00;">📋 Processing ' + totalTrades + ' completed trades...</span><br>';
        
        if (trades.length === 0) {
            logContainer.innerHTML += '<span style="color: #ff0000;">❌ No trades executed</span><br>';
        } else {
            // Display each trade from the trades array
            trades.forEach((trade, index) => {
                const action = trade.action || 'BUY';
                const shares = trade.shares || 0;
                const price = trade.price || 0;
                const pnl = trade.pnl || 0;
                const pnlPct = trade.pnl_pct || 0;
                const date = trade.date || 'Unknown';
                const symbol = trade.symbol || 'Unknown';
                const reason = trade.reason || 'Signal';
                
                const logColor = pnl >= 0 ? '#00ff00' : '#ff0000';
                logContainer.innerHTML += `<span style="color: ${logColor};">💰 Trade ${index + 1}: ${action} ${shares.toFixed(2)} shares of ${symbol} at $${price.toFixed(2)} on ${date} (${pnlPct.toFixed(2)}%) - ${reason}</span><br>`;
            });
            
            logContainer.innerHTML += '<span style="color: #00ff00;">✅ All trades processed and displayed!</span><br>';
        }
    }
    
    // Update benchmark comparison
    const strategyReturnElement = document.getElementById('strategy-return');
    const benchmarkReturnElement = document.getElementById('benchmark-return');
    const alphaReturnElement = document.getElementById('alpha-return');
    const outperformanceElement = document.getElementById('outperformance');
    
    if (strategyReturnElement && benchmarkReturnElement && alphaReturnElement && outperformanceElement) {
        const strategyReturn = totalReturn;
        const benchmarkReturn = performance.benchmark_return || 0;
        const alpha = performance.alpha || (strategyReturn - benchmarkReturn);
        
        strategyReturnElement.textContent = strategyReturn.toFixed(2) + '%';
        strategyReturnElement.style.color = strategyReturn >= 0 ? '#27ae60' : '#e74c3c';
        
        benchmarkReturnElement.textContent = benchmarkReturn.toFixed(2) + '%';
        benchmarkReturnElement.style.color = benchmarkReturn >= 0 ? '#27ae60' : '#e74c3c';
        
        alphaReturnElement.textContent = alpha.toFixed(2) + '%';
        alphaReturnElement.style.color = alpha >= 0 ? '#27ae60' : '#e74c3c';
        
        if (alpha > 0) {
            outperformanceElement.textContent = '✅ Outperformed';
            outperformanceElement.style.color = '#27ae60';
        } else if (alpha < 0) {
            outperformanceElement.textContent = '❌ Underperformed';
            outperformanceElement.style.color = '#e74c3c';
        } else {
            outperformanceElement.textContent = '➖ Equal';
            outperformanceElement.style.color = '#7f8c8d';
        }
    }
    
    console.log('Backtest results display completed');
}

function formatCurrency(amount) {
    return new Intl.NumberFormat('en-US', {
        style: 'currency',
        currency: 'USD'
    }).format(amount);
}

function updatePortfolioDisplay(data) {
    if (data.error) {
        showError(data.error);
        return;
    }

    document.getElementById('total-value').textContent = formatCurrency(data.total_value || 0);
    document.getElementById('daily-pnl').textContent = formatCurrency(data.daily_pnl || 0);
    document.getElementById('total-pnl').textContent = formatCurrency(data.total_pnl || 0);
    document.getElementById('position-count').textContent = data.positions ? Object.keys(data.positions).length : 0;

    // Update P&L colors
    const dailyPnlElement = document.getElementById('daily-pnl');
    const totalPnlElement = document.getElementById('total-pnl');
    
    dailyPnlElement.className = 'value ' + (data.daily_pnl >= 0 ? 'positive' : 'negative');
    totalPnlElement.className = 'value ' + (data.total_pnl >= 0 ? 'positive' : 'negative');

    // Update positions table
    updatePositionsTable(data.positions || {});
}

function updateTradingStatus(data) {
    const statusIndicator = document.getElementById('status-indicator');
    const statusText = document.getElementById('status-text');
    const marketStatus = document.getElementById('market-status');
    const dailyTrades = document.getElementById('daily-trades');

    if (data.is_running) {
        statusIndicator.className = 'status-indicator status-online';
        statusText.textContent = 'Online';
    } else {
        statusIndicator.className = 'status-indicator status-offline';
        statusText.textContent = 'Offline';
    }

    marketStatus.textContent = data.market_open ? 'Open' : 'Closed';
    dailyTrades.textContent = data.daily_trades || 0;
}

function updatePositionsTable(positions) {
    const tbody = document.getElementById('positions-tbody');
    if (!tbody) return;
    
    tbody.innerHTML = '';

    if (Object.keys(positions).length === 0) {
        tbody.innerHTML = '<tr><td colspan="6" style="text-align: center; color: #7f8c8d;">No positions</td></tr>';
        return;
    }

    Object.entries(positions).forEach(([symbol, position]) => {
        const row = document.createElement('tr');
        const pnl = position.current_value - position.cost_basis;
        const pnlPercent = (pnl / position.cost_basis) * 100;

        row.innerHTML = `
            <td><strong>${symbol}</strong></td>
            <td>${position.shares}</td>
            <td>${formatCurrency(position.avg_price)}</td>
            <td>${formatCurrency(position.current_price)}</td>
            <td class="${pnl >= 0 ? 'positive' : 'negative'}">${formatCurrency(pnl)}</td>
            <td class="${pnl >= 0 ? 'positive' : 'negative'}">${pnlPercent.toFixed(2)}%</td>
        `;
        tbody.appendChild(row);
    });
}

function startTrading() {
    fetch('/api/trading/start', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.status === 'started') {
            showMessage('Trading started successfully', 'success');
        } else {
            showMessage(data.status, 'info');
        }
    })
    .catch(error => {
        console.error('Error starting trading:', error);
        showError('Failed to start trading');
    });
}

function stopTrading() {
    fetch('/api/trading/stop', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.status === 'stopped') {
            showMessage('Trading stopped successfully', 'success');
        } else {
            showMessage(data.status, 'info');
        }
    })
    .catch(error => {
        console.error('Error stopping trading:', error);
        showError('Failed to stop trading');
    });
}

function updateTradeHistory(data) {
    const tradeHistoryContainer = document.getElementById('trade-history');
    if (!tradeHistoryContainer) return;
    
    // Update trade history display
    // Implementation depends on your trade history structure
}

function showMessage(message, type) {
    // Simple message display - you could enhance this with a toast notification
    console.log(`${type.toUpperCase()}: ${message}`);
}

function showError(message) {
    console.error('ERROR:', message);
}

// Market Indexes Functions
function loadMarketIndexes() {
    console.log('Loading market indexes...');
    
    fetch('/api/market-indexes')
        .then(response => response.json())
        .then(data => {
            if (data.error) {
                console.error('Error loading market indexes:', data.error);
                return;
            }
            
            // Update each index display
            Object.keys(data).forEach(symbol => {
                updateMarketIndexDisplay(symbol, data[symbol]);
            });
            
            // Update last update timestamp
            const lastUpdateElement = document.getElementById('indexes-last-update');
            if (lastUpdateElement) {
                lastUpdateElement.textContent = new Date().toLocaleTimeString();
            }
        })
        .catch(error => {
            console.error('Error loading market indexes:', error);
        });
}

function updateMarketIndexDisplay(symbol, data) {
    const priceElement = document.getElementById(`${symbol.toLowerCase()}-price`);
    const changeElement = document.getElementById(`${symbol.toLowerCase()}-change`);
    
    if (priceElement && changeElement) {
        // Update price
        priceElement.textContent = `$${data.price.toFixed(2)}`;
        
        // Update change
        const changeText = `${data.change_pct >= 0 ? '+' : ''}${data.change_pct.toFixed(2)}%`;
        changeElement.textContent = changeText;
        
        // Update styling based on change
        changeElement.className = 'index-change';
        if (data.change_pct > 0) {
            changeElement.classList.add('positive');
        } else if (data.change_pct < 0) {
            changeElement.classList.add('negative');
        } else {
            changeElement.classList.add('neutral');
        }
    }
}

// Auto-refresh data every 30 seconds
setInterval(() => {
    if (currentTab === 'overview') {
        loadInitialData();
    }
}, 30000);

// Date period functions for backtesting
function setBacktestPeriod(period) {
    const startDateInput = document.getElementById('backtest-start-date');
    const endDateInput = document.getElementById('backtest-end-date');
    
    const today = new Date();
    let startDate = new Date();
    
    switch(period) {
        case '1M':
            startDate.setMonth(today.getMonth() - 1);
            break;
        case '3M':
            startDate.setMonth(today.getMonth() - 3);
            break;
        case '6M':
            startDate.setMonth(today.getMonth() - 6);
            break;
        case '1Y':
            startDate.setFullYear(today.getFullYear() - 1);
            break;
        case '2Y':
            startDate.setFullYear(today.getFullYear() - 2);
            break;
        case '5Y':
            startDate.setFullYear(today.getFullYear() - 5);
            break;
        default:
            return;
    }
    
    // Format dates as YYYY-MM-DD
    const formatDate = (date) => {
        const year = date.getFullYear();
        const month = String(date.getMonth() + 1).padStart(2, '0');
        const day = String(date.getDate()).padStart(2, '0');
        return `${year}-${month}-${day}`;
    };
    
    startDateInput.value = formatDate(startDate);
    endDateInput.value = formatDate(today);
    
    // Highlight the selected period button
    const buttons = document.querySelectorAll('[onclick^="setBacktestPeriod"]');
    buttons.forEach(btn => btn.classList.remove('active'));
    event.target.classList.add('active');
}

// Initialize default date range (1 year ago to today)
function initializeBacktestDates() {
    const startDateInput = document.getElementById('backtest-start-date');
    const endDateInput = document.getElementById('backtest-end-date');
    
    if (startDateInput && endDateInput) {
        const today = new Date();
        const oneYearAgo = new Date();
        oneYearAgo.setFullYear(today.getFullYear() - 1);
        
        const formatDate = (date) => {
            const year = date.getFullYear();
            const month = String(date.getMonth() + 1).padStart(2, '0');
            const day = String(date.getDate()).padStart(2, '0');
            return `${year}-${month}-${day}`;
        };
        
        startDateInput.value = formatDate(oneYearAgo);
        endDateInput.value = formatDate(today);
    }
}

function updateStrategyDescription() {
    const strategySelect = document.getElementById('backtest-strategy');
    const profileSelect = document.getElementById('backtest-profile');
    const descriptionDiv = document.getElementById('strategy-description');
    
    if (!strategySelect || !profileSelect || !descriptionDiv) return;
    
    const selectedStrategy = strategySelect.value;
    const selectedProfile = profileSelect.value;
    let description = '';
    
    if (selectedStrategy === 'MACD') {
        switch(selectedProfile) {
            case 'balanced':
                description = '<strong>MACD Balanced:</strong> Standard MACD Strategy with balanced parameters. Uses MACD crossover with RSI and EMA filters for moderate risk/reward.';
                break;
            case 'canonical':
                description = '<strong>MACD Canonical:</strong> Pure MACD crossover strategy without additional filters. Only uses MACD line crossing above/below signal line.';
                break;
            case 'aggressive':
                description = '<strong>MACD Aggressive:</strong> Looser filters with higher position sizing and more frequent trades. Higher risk for higher potential returns.';
                break;
            case 'conservative':
                description = '<strong>MACD Conservative:</strong> Strict filters with lower position sizing and fewer, higher-quality trades. Lower risk for steady returns.';
                break;
            default:
                description = 'Select a strategy and profile to see its description.';
        }
    } else {
        description = 'Select a strategy and profile to see its description.';
    }
    
    descriptionDiv.innerHTML = description;
}

// Strategy Parameters Functions
function toggleStrategyParameters() {
    const paramsSection = document.getElementById('strategy-parameters');
    const toggleSpan = document.getElementById('params-toggle');
    
    if (paramsSection.style.display === 'none') {
        paramsSection.style.display = 'block';
        toggleSpan.textContent = '▲';
    } else {
        paramsSection.style.display = 'none';
        toggleSpan.textContent = '▼';
    }
}

function loadStrategyParameters() {
    const strategySelect = document.getElementById('backtest-strategy');
    const selectedStrategy = strategySelect.value;
    
    if (!selectedStrategy) {
        showError('Please select a strategy first');
        return;
    }
    
    // Show loading state
    const paramsContent = document.getElementById('parameters-content');
    paramsContent.innerHTML = '<div style="text-align: center; color: #7f8c8d; padding: 20px;">Loading parameters...</div>';
    
    // Fetch strategy parameters from API
    fetch(`/api/strategy/${selectedStrategy}/parameters`)
        .then(response => response.json())
        .then(data => {
            if (data.error) {
                showError(data.error);
                return;
            }
            displayStrategyParameters(data);
        })
        .catch(error => {
            console.error('Error loading strategy parameters:', error);
            showError('Failed to load strategy parameters');
        });
}

function displayStrategyParameters(strategyData) {
    const paramsContent = document.getElementById('parameters-content');
    let html = '';
    
    html += `<div style="margin-bottom: 20px;">
        <h5 style="color: #2c3e50; margin-bottom: 10px;">${strategyData.name}</h5>
        <p style="color: #555; font-size: 0.9em; margin-bottom: 15px;">${strategyData.description}</p>
    </div>`;
    
    // Entry Conditions
    if (strategyData.entry_conditions) {
        html += createParameterSection('Entry Conditions', strategyData.entry_conditions);
    }
    
    // Exit Conditions
    if (strategyData.exit_conditions) {
        html += createParameterSection('Exit Conditions', strategyData.exit_conditions);
    }
    
    // Position Sizing
    if (strategyData.position_sizing) {
        html += createParameterSection('Position Sizing', strategyData.position_sizing);
    }
    
    paramsContent.innerHTML = html;
}

function createParameterSection(title, parameters) {
    let html = `<div style="margin-bottom: 20px; padding: 15px; background: white; border-radius: 8px; border: 1px solid #ddd;">
        <h6 style="color: #2c3e50; margin-bottom: 10px;">${title}</h6>`;
    
    for (const [key, value] of Object.entries(parameters)) {
        if (typeof value === 'object' && value !== null) {
            // Handle nested objects (like weights)
            html += `<div style="margin-bottom: 10px;">
                <label style="font-weight: bold; color: #2c3e50;">${key}:</label>
                <div style="margin-left: 15px;">`;
            
            for (const [subKey, subValue] of Object.entries(value)) {
                html += createParameterInput(`${key}_${subKey}`, subKey, subValue);
            }
            
            html += `</div></div>`;
        } else {
            html += createParameterInput(key, key, value);
        }
    }
    
    html += '</div>';
    return html;
}

function createParameterInput(id, label, value) {
    const inputType = typeof value === 'number' ? 'number' : 'text';
    const step = typeof value === 'number' && value % 1 !== 0 ? '0.01' : '1';
    
    return `<div style="margin-bottom: 8px;">
        <label style="display: block; margin-bottom: 3px; color: #555; font-size: 0.9em;">${label}:</label>
        <input type="${inputType}" id="param_${id}" value="${value}" step="${step}" 
               style="width: 100%; padding: 5px; border: 1px solid #ddd; border-radius: 4px; font-size: 0.9em;">
    </div>`;
}

function resetToDefaults() {
    loadStrategyParameters();
}

function getCustomParameters() {
    const customParams = {};
    const inputs = document.querySelectorAll('#strategy-parameters input[id^="param_"]');
    
    inputs.forEach(input => {
        const paramName = input.id.replace('param_', '');
        let value = input.value;
        
        // Convert to appropriate type
        if (input.type === 'number') {
            value = parseFloat(value);
            if (isNaN(value)) value = 0;
        } else if (value === 'true') {
            value = true;
        } else if (value === 'false') {
            value = false;
        }
        
        // Handle nested parameters (e.g., entry_conditions_weights_macd_crossover_up)
        const parts = paramName.split('_');
        if (parts.length > 2) {
            const mainKey = parts[0] + '_' + parts[1]; // entry_conditions
            const subKey = parts[2]; // weights
            const paramKey = parts.slice(3).join('_'); // macd_crossover_up
            
            if (!customParams[mainKey]) customParams[mainKey] = {};
            if (!customParams[mainKey][subKey]) customParams[mainKey][subKey] = {};
            customParams[mainKey][subKey][paramKey] = value;
        } else {
            customParams[paramName] = value;
        }
    });
    
    return customParams;
}

// Automation Functions
function startAutomation() {
    const modeSelect = document.getElementById('automation-mode-select');
    const mode = modeSelect ? modeSelect.value : 'paper_trading';
    
    fetch('/api/automation/start', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ mode: mode })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            showMessage('Automation started successfully', 'success');
            updateAutomationStatus();
        } else {
            showError('Failed to start automation: ' + data.error);
        }
    })
    .catch(error => {
        console.error('Error starting automation:', error);
        showError('Error starting automation');
    });
}

function stopAutomation() {
    fetch('/api/automation/stop', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            showMessage('Automation stopped successfully', 'success');
            updateAutomationStatus();
        } else {
            showError('Failed to stop automation: ' + data.error);
        }
    })
    .catch(error => {
        console.error('Error stopping automation:', error);
        showError('Error stopping automation');
    });
}

function runAutomationCycle() {
    fetch('/api/automation/cycle', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            showMessage('Automation cycle completed', 'success');
            updateAutomationStatus();
            loadAutomationPositions();
            loadAutomationPerformance();
        } else {
            showError('Failed to run automation cycle: ' + data.error);
        }
    })
    .catch(error => {
        console.error('Error running automation cycle:', error);
        showError('Error running automation cycle');
    });
}

function saveAutomationConfig() {
    const config = {
        mode: document.getElementById('automation-mode-select').value,
        max_positions: parseInt(document.getElementById('max-positions').value),
        position_size: parseInt(document.getElementById('position-size').value),
        stop_loss: parseInt(document.getElementById('stop-loss').value),
        take_profit: parseInt(document.getElementById('take-profit').value)
    };
    
    fetch('/api/automation/config', {
        method: 'PUT',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify(config)
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            showMessage('Configuration saved successfully', 'success');
        } else {
            showError('Failed to save configuration: ' + data.error);
        }
    })
    .catch(error => {
        console.error('Error saving configuration:', error);
        showError('Error saving configuration');
    });
}

function updateAutomationStatus() {
    fetch('/api/automation/status')
        .then(response => response.json())
        .then(data => {
            const statusIndicator = document.getElementById('automation-status-indicator');
            const statusText = document.getElementById('automation-status-text');
            const modeText = document.getElementById('automation-mode');
            const lastCycleTime = document.getElementById('last-cycle-time');
            const cyclesToday = document.getElementById('cycles-today');
            
            if (statusIndicator && statusText) {
                if (data.is_running) {
                    statusIndicator.className = 'status-indicator status-online';
                    statusText.textContent = 'Running';
                } else {
                    statusIndicator.className = 'status-indicator status-offline';
                    statusText.textContent = 'Stopped';
                }
            }
            
            if (modeText) {
                modeText.textContent = data.mode || 'Paper Trading';
            }
            
            if (lastCycleTime) {
                lastCycleTime.textContent = data.last_cycle_time || 'Never';
            }
            
            if (cyclesToday) {
                cyclesToday.textContent = data.cycles_today || '0';
            }
            
            // Display market hours information
            if (data.market_status) {
                const marketStatus = data.market_status;
                const statusContainer = document.getElementById('automation-status');
                
                // Create or update market status display
                let marketStatusElement = document.getElementById('market-status-display');
                if (!marketStatusElement) {
                    marketStatusElement = document.createElement('div');
                    marketStatusElement.id = 'market-status-display';
                    marketStatusElement.style.cssText = 'margin-top: 10px; padding: 10px; border-radius: 5px; font-size: 0.9em;';
                    statusContainer.appendChild(marketStatusElement);
                }
                
                const marketStatusClass = marketStatus.is_open ? 'status-online' : 'status-offline';
                const marketStatusText = marketStatus.is_open ? 'Market Open' : 'Market Closed';
                
                marketStatusElement.innerHTML = `
                    <div style="margin-bottom: 5px;">
                        <span class="status-indicator ${marketStatusClass}"></span>
                        <strong>${marketStatusText}</strong>
                    </div>
                    <div style="font-size: 0.8em; color: #666;">
                        <div>Current Time: ${marketStatus.current_time_et}</div>
                        <div>Market Hours: ${marketStatus.market_hours}</div>
                        <div>Next Open: ${marketStatus.next_open}</div>
                    </div>
                `;
            }
        })
        .catch(error => {
            console.error('Error updating automation status:', error);
        });
}

function loadAutomationPositions() {
    fetch('/api/automation/positions')
        .then(response => response.json())
        .then(data => {
            updateAutomationPositionsTable(data);
        })
        .catch(error => {
            console.error('Error loading automation positions:', error);
        });
}

function updateAutomationPositionsTable(positions) {
    const tbody = document.getElementById('automation-positions-tbody');
    if (!tbody) return;
    
    if (!positions || positions.length === 0) {
        tbody.innerHTML = '<tr><td colspan="8" class="loading">No active positions</td></tr>';
        return;
    }
    
    tbody.innerHTML = '';
    positions.forEach(position => {
        const row = document.createElement('tr');
        const pnlClass = position.pnl >= 0 ? 'positive' : 'negative';
        const duration = position.duration || 'N/A';
        
        row.innerHTML = `
            <td>${position.symbol}</td>
            <td>${position.shares}</td>
            <td>$${position.entry_price}</td>
            <td>$${position.current_price}</td>
            <td class="${pnlClass}">$${position.pnl}</td>
            <td class="${pnlClass}">${position.pnl_percent}%</td>
            <td>${duration}</td>
            <td>
                <button class="btn btn-danger btn-sm" onclick="closePosition('${position.symbol}')">Close</button>
            </td>
        `;
        tbody.appendChild(row);
    });
}

function loadAutomationPerformance() {
    fetch('/api/automation/performance')
        .then(response => response.json())
        .then(data => {
            updateAutomationPerformanceDisplay(data);
        })
        .catch(error => {
            console.error('Error loading automation performance:', error);
        });
}

function updateAutomationPerformanceDisplay(performance) {
    const totalPnl = document.getElementById('automation-total-pnl');
    const winRate = document.getElementById('automation-win-rate');
    const avgReturn = document.getElementById('automation-avg-return');
    const sharpe = document.getElementById('automation-sharpe');
    
    if (totalPnl) {
        totalPnl.textContent = formatCurrency(performance.total_pnl || 0);
        totalPnl.className = `value ${performance.total_pnl >= 0 ? 'positive' : 'negative'}`;
    }
    
    if (winRate) {
        winRate.textContent = `${performance.win_rate || 0}%`;
    }
    
    if (avgReturn) {
        avgReturn.textContent = `${performance.avg_return || 0}%`;
        avgReturn.className = `value ${performance.avg_return >= 0 ? 'positive' : 'negative'}`;
    }
    
    if (sharpe) {
        sharpe.textContent = (performance.sharpe_ratio || 0).toFixed(2);
    }
}

function clearAutomationLogs() {
    const logContent = document.getElementById('automation-log-content');
    if (logContent) {
        logContent.innerHTML = '<span style="color: #888;">Logs cleared...</span>';
    }
}

function exportAutomationLogs() {
    const logContent = document.getElementById('automation-log-content');
    if (logContent) {
        const text = logContent.innerText;
        const blob = new Blob([text], { type: 'text/plain' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = 'automation-logs.txt';
        a.click();
        URL.revokeObjectURL(url);
    }
}

function addToAutomationWatchlist() {
    const input = document.getElementById('watchlist-add');
    const symbol = input.value.trim().toUpperCase();
    
    if (!symbol) {
        showError('Please enter a symbol');
        return;
    }
    
    // Add to watchlist display
    const watchlistContainer = document.getElementById('watchlist-symbols');
    if (watchlistContainer) {
        const symbolElement = document.createElement('span');
        symbolElement.className = 'watchlist-symbol';
        symbolElement.innerHTML = `
            ${symbol}
            <button onclick="removeFromWatchlist('${symbol}')" style="margin-left: 5px; background: #e74c3c; color: white; border: none; border-radius: 50%; width: 20px; height: 20px; cursor: pointer;">×</button>
        `;
        watchlistContainer.appendChild(symbolElement);
    }
    
    input.value = '';
    showMessage(`Added ${symbol} to watchlist`, 'success');
}

function removeFromWatchlist(symbol) {
    const watchlistContainer = document.getElementById('watchlist-symbols');
    if (watchlistContainer) {
        const symbolElements = watchlistContainer.querySelectorAll('.watchlist-symbol');
        symbolElements.forEach(element => {
            if (element.textContent.includes(symbol)) {
                element.remove();
            }
        });
    }
    showMessage(`Removed ${symbol} from watchlist`, 'success');
}

function closePosition(symbol) {
    // This would typically call an API to close the position
    showMessage(`Closing position for ${symbol}...`, 'info');
    // In a real implementation, you would call an API endpoint to close the position
}

// Load automation data when automation tab is shown
function loadAutomationData() {
    updateAutomationStatus();
    loadAutomationPositions();
    loadAutomationPerformance();
}

// Historical Backtest Functions
function initializeHistoricalBacktest() {
    // Set default dates
    const endDate = new Date();
    const startDate = new Date();
    startDate.setFullYear(startDate.getFullYear() - 1); // Default to 1 year ago
    
    document.getElementById('backtest-end-date').value = endDate.toISOString().split('T')[0];
    document.getElementById('backtest-start-date').value = startDate.toISOString().split('T')[0];
    
    // Add event listeners
    document.getElementById('run-historical-backtest-btn').addEventListener('click', runHistoricalBacktest);
    document.getElementById('clear-historical-results-btn').addEventListener('click', clearHistoricalResults);
    document.getElementById('clear-historical-logs-btn').addEventListener('click', clearHistoricalLogs);
    document.getElementById('export-historical-logs-btn').addEventListener('click', exportHistoricalLogs);
    
    // Add period change listener
    document.getElementById('backtest-period').addEventListener('change', updateHistoricalDates);
}

function updateHistoricalDates() {
    const period = document.getElementById('backtest-period').value;
    const endDate = new Date();
    let startDate = new Date();
    
    switch (period) {
        case '1m':
            startDate.setMonth(startDate.getMonth() - 1);
            break;
        case '6m':
            startDate.setMonth(startDate.getMonth() - 6);
            break;
        case '1y':
            startDate.setFullYear(startDate.getFullYear() - 1);
            break;
        case '2y':
            startDate.setFullYear(startDate.getFullYear() - 2);
            break;
        case '3y':
            startDate.setFullYear(startDate.getFullYear() - 3);
            break;
        case '5y':
            startDate.setFullYear(startDate.getFullYear() - 5);
            break;
    }
    
    document.getElementById('backtest-start-date').value = startDate.toISOString().split('T')[0];
    document.getElementById('backtest-end-date').value = endDate.toISOString().split('T')[0];
}

function runHistoricalBacktest() {
    const period = document.getElementById('backtest-period').value;
    const benchmark = document.getElementById('backtest-benchmark').value;
    const startDate = document.getElementById('backtest-start-date').value;
    const endDate = document.getElementById('backtest-end-date').value;
    const strategy = document.getElementById('historical-backtest-strategy').value;
    const profile = document.getElementById('historical-backtest-profile').value;
    
    if (!startDate || !endDate) {
        showError('Please select start and end dates');
        return;
    }
    
    if (new Date(startDate) >= new Date(endDate)) {
        showError('Start date must be before end date');
        return;
    }
    
    // Show loading state
    const button = document.getElementById('run-historical-backtest-btn');
    const originalText = button.textContent;
    button.textContent = 'Running...';
    button.disabled = true;
    
    // Clear previous results
    clearHistoricalResults();
    
    // Add log entry
    addHistoricalLog(`Starting historical backtest for period: ${period}, benchmark: ${benchmark}`);
    addHistoricalLog(`Strategy: ${strategy} (${profile})`);
    addHistoricalLog(`Date range: ${startDate} to ${endDate}`);
    
    const requestData = {
        period: period,
        benchmark: benchmark,
        start_date: startDate,
        end_date: endDate,
        strategy: strategy,
        profile: profile
    };
    
    fetch('/api/automation/historical-backtest', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(requestData)
    })
    .then(response => response.json())
    .then(data => {
        // Reset button
        button.textContent = originalText;
        button.disabled = false;
        
        if (data.error) {
            showError('Historical backtest failed: ' + data.error);
            addHistoricalLog(`❌ Error: ${data.error}`);
            return;
        }
        
        // Display results
        displayHistoricalResults(data);
        
        // Add completion log
        addHistoricalLog('✅ Historical backtest completed successfully!');
        if (data.trades) {
            addHistoricalLog(`📊 Total trades: ${data.trades.length}`);
        }
        if (data.performance) {
            addHistoricalLog(`💰 Total return: ${data.performance.total_return.toFixed(2)}%`);
            addHistoricalLog(`📈 Sharpe ratio: ${data.performance.sharpe_ratio.toFixed(2)}`);
        }
    })
    .catch(error => {
        console.error('Error:', error);
        button.textContent = originalText;
        button.disabled = false;
        showError('Failed to run historical backtest: ' + error.message);
        addHistoricalLog(`❌ Error: ${error.message}`);
    });
}

function displayHistoricalResults(results) {
    if (!results) return;
    
    // Update metrics
    document.getElementById('historical-strategy-return').textContent = `${results.total_return?.toFixed(2) || 0}%`;
    document.getElementById('historical-benchmark-return').textContent = `${results.benchmark_return?.toFixed(2) || 0}%`;
    document.getElementById('historical-alpha-return').textContent = `${results.excess_return?.toFixed(2) || 0}%`;
    document.getElementById('historical-sharpe-ratio').textContent = (results.sharpe_ratio || 0).toFixed(2);
    document.getElementById('historical-max-drawdown').textContent = `${results.max_drawdown?.toFixed(2) || 0}%`;
    document.getElementById('historical-total-trades').textContent = results.total_trades || 0;
    
    // Calculate win rate
    const winRate = results.total_trades > 0 ? (results.winning_trades / results.total_trades * 100) : 0;
    document.getElementById('historical-win-rate').textContent = `${winRate.toFixed(1)}%`;
    
    // Calculate average trade return
    let avgTradeReturn = 0;
    if (results.trades && results.trades.length > 0) {
        const sellTrades = results.trades.filter(t => t.action === 'SELL' && t.pnl_pct !== undefined);
        if (sellTrades.length > 0) {
            avgTradeReturn = sellTrades.reduce((sum, trade) => sum + trade.pnl_pct, 0) / sellTrades.length;
        }
    }
    document.getElementById('historical-avg-trade-return').textContent = `${avgTradeReturn.toFixed(2)}%`;
    
    // Update trades table
    updateHistoricalTradesTable(results.trades || []);
    
    // Create performance chart
    createHistoricalPerformanceChart(results);
    
    // Add summary to logs
    addHistoricalLog(`Strategy Return: ${results.total_return?.toFixed(2) || 0}%`);
    addHistoricalLog(`Benchmark Return: ${results.benchmark_return?.toFixed(2) || 0}%`);
    addHistoricalLog(`Alpha: ${results.excess_return?.toFixed(2) || 0}%`);
    addHistoricalLog(`Sharpe Ratio: ${(results.sharpe_ratio || 0).toFixed(2)}`);
    addHistoricalLog(`Max Drawdown: ${results.max_drawdown?.toFixed(2) || 0}%`);
    addHistoricalLog(`Total Trades: ${results.total_trades || 0}`);
    addHistoricalLog(`Win Rate: ${winRate.toFixed(1)}%`);
}

function updateHistoricalTradesTable(trades) {
    const tbody = document.getElementById('historical-trades-tbody');
    if (!tbody) return;
    
    if (!trades || trades.length === 0) {
        tbody.innerHTML = '<tr><td colspan="9" class="loading">No trades found</td></tr>';
        return;
    }
    
    tbody.innerHTML = '';
    trades.forEach(trade => {
        const row = document.createElement('tr');
        const pnlClass = trade.pnl >= 0 ? 'positive' : 'negative';
        const pnlPercent = trade.pnl_pct || 0;
        
        row.innerHTML = `
            <td>${trade.date}</td>
            <td>${trade.symbol}</td>
            <td>${trade.action}</td>
            <td>${trade.shares?.toFixed(2) || 0}</td>
            <td>$${trade.price?.toFixed(2) || 0}</td>
            <td>$${trade.value?.toFixed(2) || 0}</td>
            <td class="${pnlClass}">${trade.pnl ? `$${trade.pnl.toFixed(2)}` : '-'}</td>
            <td class="${pnlClass}">${trade.action === 'SELL' ? `${pnlPercent.toFixed(2)}%` : '-'}</td>
            <td>${trade.strategy || 'N/A'}</td>
        `;
        tbody.appendChild(row);
    });
}

function createHistoricalPerformanceChart(results) {
    const chartContainer = document.getElementById('historical-backtest-chart');
    if (!chartContainer || !results.portfolio_values || !results.benchmark_values) {
        return;
    }
    
    // Clear container
    chartContainer.innerHTML = '';
    
    // Create chart using Plotly
    if (typeof Plotly !== 'undefined') {
        const portfolioDates = results.portfolio_values.map(pv => pv.date);
        const portfolioValues = results.portfolio_values.map(pv => pv.value);
        const benchmarkDates = results.benchmark_values.map(bv => bv.date);
        const benchmarkValues = results.benchmark_values.map(bv => bv.value);
        
        // Normalize benchmark values to start at the same value as portfolio
        const initialPortfolioValue = portfolioValues[0];
        const initialBenchmarkValue = benchmarkValues[0];
        const normalizedBenchmarkValues = benchmarkValues.map(value => 
            (value / initialBenchmarkValue) * initialPortfolioValue
        );
        
        const trace1 = {
            x: portfolioDates,
            y: portfolioValues,
            type: 'scatter',
            mode: 'lines',
            name: 'Strategy',
            line: { color: '#3498db', width: 2 }
        };
        
        const trace2 = {
            x: benchmarkDates,
            y: normalizedBenchmarkValues,
            type: 'scatter',
            mode: 'lines',
            name: 'Benchmark',
            line: { color: '#e74c3c', width: 2 }
        };
        
        const layout = {
            title: 'Strategy vs Benchmark Performance',
            xaxis: { title: 'Date' },
            yaxis: { title: 'Portfolio Value ($)' },
            hovermode: 'x unified',
            legend: { x: 0, y: 1 }
        };
        
        Plotly.newPlot(chartContainer, [trace1, trace2], layout);
    } else {
        chartContainer.innerHTML = '<div style="text-align: center; color: #7f8c8d; padding-top: 180px;">Chart library not available</div>';
    }
}

function clearHistoricalResults() {
    // Clear metrics
    document.getElementById('historical-strategy-return').textContent = '0%';
    document.getElementById('historical-benchmark-return').textContent = '0%';
    document.getElementById('historical-alpha-return').textContent = '0%';
    document.getElementById('historical-sharpe-ratio').textContent = '0.00';
    document.getElementById('historical-max-drawdown').textContent = '0%';
    document.getElementById('historical-total-trades').textContent = '0';
    document.getElementById('historical-win-rate').textContent = '0%';
    document.getElementById('historical-avg-trade-return').textContent = '0%';
    
    // Clear trades table
    const tbody = document.getElementById('historical-trades-tbody');
    if (tbody) {
        tbody.innerHTML = '<tr><td colspan="9" class="loading">No trades yet. Run a backtest to see results.</td></tr>';
    }
    
    // Clear chart
    const chartContainer = document.getElementById('historical-backtest-chart');
    if (chartContainer) {
        chartContainer.innerHTML = '<div style="text-align: center; color: #7f8c8d; padding-top: 180px;">Chart will appear here after running backtest</div>';
    }
}

function addHistoricalLog(message) {
    const logContent = document.getElementById('historical-log-content');
    if (logContent) {
        const timestamp = new Date().toLocaleTimeString();
        const logEntry = document.createElement('div');
        logEntry.innerHTML = `<span style="color: #888;">[${timestamp}]</span> ${message}`;
        logContent.appendChild(logEntry);
        logContent.scrollTop = logContent.scrollHeight;
    }
}

function clearHistoricalLogs() {
    const logContent = document.getElementById('historical-log-content');
    if (logContent) {
        logContent.innerHTML = '<span style="color: #888;">Historical backtest logs cleared...</span>';
    }
}

function exportHistoricalLogs() {
    const logContent = document.getElementById('historical-log-content');
    if (logContent) {
        const text = logContent.innerText;
        const blob = new Blob([text], { type: 'text/plain' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = 'historical-backtest-logs.txt';
        a.click();
        URL.revokeObjectURL(url);
    }
}

// Historical backtest strategy and profile selection
function updateHistoricalStrategyDescription() {
    const strategySelect = document.getElementById('historical-backtest-strategy');
    const profileSelect = document.getElementById('historical-backtest-profile');
    const descriptionDiv = document.getElementById('historical-strategy-description');
    
    if (!strategySelect || !profileSelect || !descriptionDiv) return;
    
    const selectedStrategy = strategySelect.value;
    const selectedProfile = profileSelect.value;
    let description = '';
    
    if (selectedStrategy === 'MACD') {
        switch(selectedProfile) {
            case 'balanced':
                description = '<strong>MACD Balanced:</strong> Standard MACD Strategy with balanced parameters. Uses MACD crossover with RSI and EMA filters for moderate risk/reward.';
                break;
            case 'canonical':
                description = '<strong>MACD Canonical:</strong> Pure MACD crossover strategy without additional filters. Only uses MACD line crossing above/below signal line.';
                break;
            case 'aggressive':
                description = '<strong>MACD Aggressive:</strong> Looser filters with higher position sizing and more frequent trades. Higher risk for higher potential returns.';
                break;
            case 'conservative':
                description = '<strong>MACD Conservative:</strong> Strict filters with lower position sizing and fewer, higher-quality trades. Lower risk for steady returns.';
                break;
            default:
                description = 'Select a strategy and profile to see its description.';
        }
    } else {
        description = 'Select a strategy and profile to see its description.';
    }
    
    descriptionDiv.innerHTML = description;
} 