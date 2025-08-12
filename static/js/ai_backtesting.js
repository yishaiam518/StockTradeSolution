/**
 * AI Backtesting Modal JavaScript
 * Handles all frontend functionality for the AI strategy backtesting modal.
 * Completely separate from existing portfolio functionality.
 */

class AIBacktestingModal {
    constructor() {
        console.log('AIBacktestingModal constructor called');
        this.baseUrl = '/api/ai-backtesting';
        this.currentParameters = {};
        this.currentResults = [];
        this.currentSummary = null;
        
        this.initializeEventListeners();
        this.loadInitialData();
    }
    
    /**
     * Initialize all event listeners
     */
    initializeEventListeners() {
        // Run backtesting button
        const runBacktestBtn = document.getElementById('runBacktestBtn');
        if (runBacktestBtn) {
            runBacktestBtn.addEventListener('click', () => {
                console.log('Run Backtesting button clicked!');
                this.runBacktesting();
            });
        }
        
        // Reset results button
        const resetResultsBtn = document.getElementById('resetResultsBtn');
        if (resetResultsBtn) {
            resetResultsBtn.addEventListener('click', () => {
                console.log('Reset Results button clicked!');
                this.resetResults();
            });
        }
        
        // Export results button
        const exportResultsBtn = document.getElementById('exportResultsBtn');
        if (exportResultsBtn) {
            exportResultsBtn.addEventListener('click', () => {
                console.log('Export Results button clicked!');
                this.exportResults();
            });
        }
        
        console.log('Event listeners initialized for AI Backtesting Modal');
    }
    
    /**
     * Load initial data when modal opens
     */
    async loadInitialData() {
        try {
            // Populate strategy performance table
            this.populateStrategyPerformanceTable();
            
            console.log('AI Backtesting Modal initialized successfully');
        } catch (error) {
            console.error('Error loading initial data:', error);
            this.showError('Failed to load initial data. Please try again.');
        }
    }
    
    /**
     * Populate strategy performance table with sample data
     */
    populateStrategyPerformanceTable() {
        const tbody = document.getElementById('strategyPerformanceTableBody');
        if (!tbody) return;
        
            // Sample strategies for demonstration (showing expected 5-year trade counts)
            const sampleStrategies = [
                {
                    name: 'MACD Aggressive',
                    pnl: 0,
                    trades: 0,
                    winRate: 0,
                    availableCash: 1000000,
                    stopLossCount: 0,
                    stopGainCount: 0
                },
                {
                    name: 'MACD Conservative',
                    pnl: 0,
                    trades: 0,
                    winRate: 0,
                    availableCash: 1000000,
                    stopLossCount: 0,
                    stopGainCount: 0
                },
                {
                    name: 'Bollinger Bands',
                    pnl: 0,
                    trades: 0,
                    winRate: 0,
                    availableCash: 1000000,
                    stopLossCount: 0,
                    stopGainCount: 0
                },
                {
                    name: 'RSI Strategy',
                    pnl: 0,
                    trades: 0,
                    winRate: 0,
                    availableCash: 1000000,
                    stopLossCount: 0,
                    stopGainCount: 0
                }
            ];
        
        tbody.innerHTML = '';
        sampleStrategies.forEach(strategy => {
            const row = document.createElement('tr');
            row.innerHTML = `
                <td><strong>${strategy.name}</strong></td>
                <td class="text-success">$${strategy.pnl.toLocaleString()}</td>
                <td>${strategy.trades}</td>
                <td>${strategy.winRate}%</td>
                <td>$${strategy.availableCash.toLocaleString()}</td>
                <td>${strategy.stopLossCount}</td>
                <td>${strategy.stopGainCount}</td>
                <td>
                    <button class="btn btn-sm btn-outline-primary" onclick="window.aiBacktestingModal.viewStrategyTransactions('${strategy.name}')">
                        <i class="fas fa-eye me-1"></i>View Trades
                    </button>
                </td>
            `;
            tbody.appendChild(row);
        });
    }
    
    /**
     * View strategy transactions (opens Syncfusion table like portfolio)
     */
    async viewStrategyTransactions(strategyName) {
        try {
            // Check if we have transaction data for this strategy
            const transactions = this.strategyTransactions && this.strategyTransactions[strategyName];
            
            // Create a modal to show transactions
            const modalHtml = `
                <div class="modal fade" id="strategyTransactionsModal" tabindex="-1">
                    <div class="modal-dialog modal-xl modal-dialog-scrollable">
                        <div class="modal-content">
                            <div class="modal-header">
                                <h5 class="modal-title">${strategyName} - Transaction History</h5>
                                <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                            </div>
                            <div class="modal-body">
                                <div class="table-responsive">
                                    <table class="table table-striped table-hover">
                                        <thead class="table-dark">
                                            <tr>
                                                <th>Symbol</th>
                                                <th>Action</th>
                                                <th>Qty</th>
                                                <th>Price</th>
                                                <th>Total</th>
                                                <th>P&L</th>
                                                <th>P&L %</th>
                                                <th>Timestamp</th>
                                            </tr>
                                        </thead>
                                        <tbody id="strategyTransactionsTableBody">
                                            ${transactions ? this.generateTransactionRows(transactions) : `
                                                <tr>
                                                    <td colspan="8" class="text-center text-muted">
                                                        <i class="fas fa-info-circle me-2"></i>
                                                        No transactions available yet. Run backtesting to generate data.
                                                    </td>
                                                </tr>
                                            `}
                                        </tbody>
                                    </table>
                                </div>
                            </div>
                            <div class="modal-footer">
                                <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Close</button>
                            </div>
                        </div>
                    </div>
                </div>
            `;
            
            // Remove existing modal if any
            const existingModal = document.getElementById('strategyTransactionsModal');
            if (existingModal) {
                existingModal.remove();
            }
            
            // Add new modal to body
            document.body.insertAdjacentHTML('beforeend', modalHtml);
            
            // Show the modal
            const modal = new bootstrap.Modal(document.getElementById('strategyTransactionsModal'));
            modal.show();
            
        } catch (error) {
            console.error('Error opening strategy transactions modal:', error);
            this.showError('Failed to open strategy transactions.');
        }
    }
    
    /**
     * Run AI backtesting simulation
     */
    async runBacktesting() {
        try {
            this.showLoading(true);
            
            // Simulate AI backtesting process
            await new Promise(resolve => setTimeout(resolve, 2000));
            
            // Generate sample results for 5-year period (more realistic trade counts)
            const sampleResults = [
                {
                    name: 'MACD Aggressive',
                    pnl: 125000,
                    trades: 1247, // ~250 trades per year for aggressive strategy
                    winRate: 68,
                    availableCash: 875000,
                    stopLossCount: 187, // 15% of trades hit stop loss
                    stopGainCount: 249  // 20% of trades hit stop gain
                },
                {
                    name: 'MACD Conservative',
                    pnl: 89000,
                    trades: 892, // ~180 trades per year for conservative strategy
                    winRate: 72,
                    availableCash: 911000,
                    stopLossCount: 134, // 15% of trades hit stop loss
                    stopGainCount: 178  // 20% of trades hit stop gain
                },
                {
                    name: 'Bollinger Bands',
                    pnl: 156000,
                    trades: 1563, // ~310 trades per year for mean reversion strategy
                    winRate: 65,
                    availableCash: 844000,
                    stopLossCount: 234, // 15% of trades hit stop loss
                    stopGainCount: 312  // 20% of trades hit stop gain
                },
                {
                    name: 'RSI Strategy',
                    pnl: 67000,
                    trades: 745, // ~150 trades per year for RSI strategy
                    winRate: 75,
                    availableCash: 933000,
                    stopLossCount: 112, // 15% of trades hit stop loss
                    stopGainCount: 149  // 20% of trades hit stop gain
                }
            ];
            
            // Store sample transaction data for each strategy
            this.strategyTransactions = {
                'MACD Aggressive': this.generateSampleTransactions('MACD Aggressive', 1247),
                'MACD Conservative': this.generateSampleTransactions('MACD Conservative', 892),
                'Bollinger Bands': this.generateSampleTransactions('Bollinger Bands', 1563),
                'RSI Strategy': this.generateSampleTransactions('RSI Strategy', 745)
            };
            
            // Update the strategy performance table
            this.updateStrategyPerformanceTable(sampleResults);
            
            this.showSuccess('AI Backtesting completed successfully! Results updated.');
            
        } catch (error) {
            console.error('Error running backtesting:', error);
            this.showError('Failed to run backtesting: ' + error.message);
        } finally {
            this.showLoading(false);
        }
    }
    
    /**
     * Generate sample transaction data for a strategy
     */
    generateSampleTransactions(strategyName, tradeCount) {
        const symbols = ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'TSLA', 'NVDA', 'META', 'NFLX', 'AMD', 'INTC'];
        const transactions = [];
        
        for (let i = 0; i < tradeCount; i++) {
            const symbol = symbols[Math.floor(Math.random() * symbols.length)];
            const action = Math.random() > 0.5 ? 'BUY' : 'SELL';
            const qty = Math.floor(Math.random() * 100) + 1;
            const price = Math.random() * 500 + 50;
            const total = qty * price;
            
            // Generate realistic P&L based on action and strategy
            let pnl = 0;
            let pnlPct = 0;
            
            if (action === 'SELL') {
                // For sell orders, generate some profit/loss
                pnl = (Math.random() - 0.4) * 1000; // -400 to +600
                pnlPct = (pnl / total) * 100;
            }
            
            const timestamp = new Date(Date.now() - Math.random() * 30 * 24 * 60 * 60 * 1000); // Random date within last 30 days
            
            transactions.push({
                symbol: symbol,
                action: action,
                qty: qty,
                price: price.toFixed(2),
                total: total.toFixed(2),
                pnl: pnl.toFixed(2),
                pnlPct: pnlPct.toFixed(2),
                timestamp: timestamp.toLocaleString()
            });
        }
        
        return transactions;
    }
    
    /**
     * Generate HTML rows for transaction table
     */
    generateTransactionRows(transactions) {
        return transactions.map(tx => {
            const actionClass = tx.action === 'BUY' ? 'badge bg-success' : 'badge bg-danger';
            const pnlClass = parseFloat(tx.pnl) >= 0 ? 'text-success' : 'text-danger';
            const pnlSign = parseFloat(tx.pnl) >= 0 ? '+' : '';
            
            return `
                <tr>
                    <td><strong>${tx.symbol}</strong></td>
                    <td><span class="${actionClass}">${tx.action}</span></td>
                    <td>${tx.qty}</td>
                    <td>$${tx.price}</td>
                    <td>$${tx.total}</td>
                    <td class="${pnlClass}">${pnlSign}$${tx.pnl}</td>
                    <td class="${pnlClass}">${pnlSign}${tx.pnlPct}%</td>
                    <td>${tx.timestamp}</td>
                </tr>
            `;
        }).join('');
    }
    
    /**
     * Update strategy performance table with results
     */
    updateStrategyPerformanceTable(results) {
        const tbody = document.getElementById('strategyPerformanceTableBody');
        if (!tbody) return;
        
        tbody.innerHTML = '';
        results.forEach(strategy => {
            const row = document.createElement('tr');
            const pnlClass = strategy.pnl >= 0 ? 'text-success' : 'text-danger';
            const pnlSign = strategy.pnl >= 0 ? '+' : '';
            
            row.innerHTML = `
                <td><strong>${strategy.name}</strong></td>
                <td class="${pnlClass}">${pnlSign}$${strategy.pnl.toLocaleString()}</td>
                <td>${strategy.trades}</td>
                <td>${strategy.winRate}%</td>
                <td>$${strategy.availableCash.toLocaleString()}</td>
                <td>${strategy.stopLossCount}</td>
                <td>${strategy.stopGainCount}</td>
                <td>
                    <button class="btn btn-sm btn-outline-primary" onclick="window.aiBacktestingModal.viewStrategyTransactions('${strategy.name}')">
                        <i class="fas fa-eye me-1"></i>View Trades
                    </button>
                </td>
            `;
            tbody.appendChild(row);
        });
    }
    
    /**
     * Reset backtesting results
     */
    async resetResults() {
        if (!confirm('Are you sure you want to reset all backtesting results? This action cannot be undone.')) {
            return;
        }
        
        try {
            this.showSuccess('Results reset successfully!');
            this.currentResults = [];
            this.currentSummary = null;
            this.strategyTransactions = null;
            
            // Reset the strategy performance table to initial state
            this.populateStrategyPerformanceTable();
            
        } catch (error) {
            console.error('Error resetting results:', error);
            this.showError('Failed to reset results: ' + error.message);
        }
    }
    
    /**
     * Export results to CSV
     */
    async exportResults() {
        if (!this.currentResults || this.currentResults.length === 0) {
            this.showError('No results to export. Please run backtesting first.');
            return;
        }
        
        try {
            this.showSuccess('Export functionality coming soon!');
        } catch (error) {
            console.error('Error exporting results:', error);
            this.showError('Failed to export results: ' + error.message);
        }
    }
    
    /**
     * Show/hide loading state
     */
    showLoading(show) {
        if (show) {
            console.log('Showing loading state...');
            // You can add a loading spinner here if needed
        } else {
            console.log('Hiding loading state...');
            // You can hide the loading spinner here if needed
        }
    }
    
    /**
     * Show success message
     */
    showSuccess(message) {
        console.log('SUCCESS:', message);
        // You can add a toast notification here if needed
        alert('Success: ' + message);
    }
    
    /**
     * Show error message
     */
    showError(message) {
        console.error('ERROR:', message);
        // You can add a toast notification here if needed
        alert('Error: ' + message);
    }
}
