/**
 * AI Backtesting Modal JavaScript
 * Handles all frontend functionality for the AI strategy backtesting modal.
 * Completely separate from existing portfolio functionality.
 */

class AIBacktestingModal {
    constructor() {
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
        // Parameter input changes
        document.getElementById('availableCash').addEventListener('input', (e) => {
            this.updateTransactionLimitDisplay();
        });
        
        document.getElementById('transactionLimit').addEventListener('input', (e) => {
            this.updateTransactionLimitDisplay();
        });
        
        // Save parameters button
        document.getElementById('saveParametersBtn').addEventListener('click', () => {
            this.saveParameters();
        });
        
        // Run backtesting button
        document.getElementById('runBacktestBtn').addEventListener('click', () => {
            this.runBacktesting();
        });
        
        // Reset results button
        document.getElementById('resetResultsBtn').addEventListener('click', () => {
            this.resetResults();
        });
        
        // Export results button
        document.getElementById('exportResultsBtn').addEventListener('click', () => {
            this.exportResults();
        });
        
        // Data collection change
        document.getElementById('dataCollection').addEventListener('change', (e) => {
            this.validateDataCollection();
        });
    }
    
    /**
     * Load initial data when modal opens
     */
    async loadInitialData() {
        try {
            await Promise.all([
                this.loadStatus(),
                this.loadParameters(),
                this.loadStrategies(),
                this.loadStrategyCombinations(),
                this.loadDataCollections()
            ]);
        } catch (error) {
            console.error('Error loading initial data:', error);
            this.showError('Failed to load initial data. Please try again.');
        }
    }
    
    /**
     * Load backtesting engine status
     */
    async loadStatus() {
        try {
            const response = await fetch(`${this.baseUrl}/status`);
            const data = await response.json();
            
            if (data.success) {
                this.updateStatusDisplay(data);
            } else {
                throw new Error(data.error || 'Failed to load status');
            }
        } catch (error) {
            console.error('Error loading status:', error);
            this.updateStatusDisplay({ error: error.message });
        }
    }
    
    /**
     * Load current parameters
     */
    async loadParameters() {
        try {
            const response = await fetch(`${this.baseUrl}/parameters`);
            const data = await response.json();
            
            if (data.success) {
                this.currentParameters = data.parameters;
                this.populateParameterFields(data.parameters);
            } else {
                throw new Error(data.error || 'Failed to load parameters');
            }
        } catch (error) {
            console.error('Error loading parameters:', error);
            this.showError('Failed to load parameters. Using default values.');
        }
    }
    
    /**
     * Load available strategies
     */
    async loadStrategies() {
        try {
            const response = await fetch(`${this.baseUrl}/strategies`);
            const data = await response.json();
            
            if (data.success) {
                this.populateStrategiesDisplay(data.strategies);
            } else {
                throw new Error(data.error || 'Failed to load strategies');
            }
        } catch (error) {
            console.error('Error loading strategies:', error);
            this.showError('Failed to load strategies.');
        }
    }
    
    /**
     * Load strategy combinations
     */
    async loadStrategyCombinations() {
        try {
            const response = await fetch(`${this.baseUrl}/combinations?max_combinations=3`);
            const data = await response.json();
            
            if (data.success) {
                this.populateCombinationsDisplay(data.combinations);
            } else {
                throw new Error(data.error || 'Failed to load strategy combinations');
            }
        } catch (error) {
            console.error('Error loading strategy combinations:', error);
            this.showError('Failed to load strategy combinations.');
        }
    }
    
    /**
     * Load available data collections
     */
    async loadDataCollections() {
        try {
            const response = await fetch('/api/data-collection/collections');
            const data = await response.json();
            
            if (data.success) {
                this.populateDataCollectionsSelect(data.collections);
            } else {
                throw new Error(data.error || 'Failed to load data collections');
            }
        } catch (error) {
            console.error('Error loading data collections:', error);
            this.showError('Failed to load data collections.');
        }
    }
    
    /**
     * Update status display
     */
    updateStatusDisplay(status) {
        const statusElement = document.getElementById('backtestingStatus');
        
        if (status.error) {
            statusElement.innerHTML = `
                <div class="text-danger">
                    <i class="fas fa-exclamation-triangle fa-2x mb-2"></i>
                    <p class="mb-0">Error: ${status.error}</p>
                </div>
            `;
            return;
        }
        
        const hasResults = status.has_results;
        const totalStrategies = status.total_strategies_tested;
        const lastExecution = status.last_execution ? new Date(status.last_execution).toLocaleString() : 'Never';
        
        statusElement.innerHTML = `
            <div class="row">
                <div class="col-md-4">
                    <div class="text-center">
                        <i class="fas fa-robot fa-2x text-primary mb-2"></i>
                        <h6>Engine Status</h6>
                        <span class="badge bg-success">${status.engine_status}</span>
                    </div>
                </div>
                <div class="col-md-4">
                    <div class="text-center">
                        <i class="fas fa-chart-line fa-2x text-info mb-2"></i>
                        <h6>Strategies Tested</h6>
                        <span class="badge bg-info">${totalStrategies}</span>
                    </div>
                </div>
                <div class="col-md-4">
                    <div class="text-center">
                        <i class="fas fa-clock fa-2x text-warning mb-2"></i>
                        <h6>Last Execution</h6>
                        <small class="text-muted">${lastExecution}</small>
                    </div>
                </div>
            </div>
        `;
    }
    
    /**
     * Populate parameter fields with current values
     */
    populateParameterFields(parameters) {
        document.getElementById('availableCash').value = parameters.available_cash;
        document.getElementById('transactionLimit').value = parameters.transaction_limit_pct * 100;
        document.getElementById('stopLoss').value = parameters.stop_loss_pct * 100;
        document.getElementById('stopGain').value = parameters.stop_gain_pct * 100;
        document.getElementById('safeNet').value = parameters.safe_net;
        document.getElementById('riskTolerance').value = parameters.risk_tolerance;
        document.getElementById('recommendationThreshold').value = parameters.recommendation_threshold * 100;
        
        this.updateTransactionLimitDisplay();
    }
    
    /**
     * Populate strategies display
     */
    populateStrategiesDisplay(strategies) {
        const container = document.getElementById('availableStrategies');
        
        if (!strategies || strategies.length === 0) {
            container.innerHTML = '<p class="text-muted text-center">No strategies available</p>';
            return;
        }
        
        const strategiesHtml = strategies.map(strategy => 
            `<span class="badge bg-primary me-2 mb-2">${strategy.label}</span>`
        ).join('');
        
        container.innerHTML = strategiesHtml;
    }
    
    /**
     * Populate strategy combinations display
     */
    populateCombinationsDisplay(combinations) {
        const container = document.getElementById('strategyCombinations');
        
        if (!combinations || combinations.length === 0) {
            container.innerHTML = '<p class="text-muted text-center">No combinations available</p>';
            return;
        }
        
        const combinationsHtml = combinations.map(combo => 
            `<div class="mb-2">
                <span class="badge bg-secondary me-1">${combo.count}</span>
                <small class="text-muted">${combo.name}</small>
            </div>`
        ).join('');
        
        container.innerHTML = combinationsHtml;
    }
    
    /**
     * Populate data collections select
     */
    populateDataCollectionsSelect(collections) {
        const select = document.getElementById('dataCollection');
        
        // Clear existing options
        select.innerHTML = '<option value="">Select a data collection...</option>';
        
        if (!collections || collections.length === 0) {
            select.innerHTML = '<option value="">No data collections available</option>';
            return;
        }
        
        // Add collection options
        collections.forEach(collection => {
            const option = document.createElement('option');
            option.value = collection.id;
            option.textContent = `${collection.name} (${collection.symbols_count} symbols)`;
            select.appendChild(option);
        });
    }
    
    /**
     * Update transaction limit display
     */
    updateTransactionLimitDisplay() {
        const availableCash = parseFloat(document.getElementById('availableCash').value) || 0;
        const transactionLimit = parseFloat(document.getElementById('transactionLimit').value) || 0;
        const currentLimit = (availableCash * transactionLimit / 100);
        
        document.getElementById('currentLimit').textContent = `$${currentLimit.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
    }
    
    /**
     * Save parameters to backend
     */
    async saveParameters() {
        try {
            const parameters = {
                available_cash: parseFloat(document.getElementById('availableCash').value),
                transaction_limit_pct: parseFloat(document.getElementById('transactionLimit').value) / 100,
                stop_loss_pct: parseFloat(document.getElementById('stopLoss').value) / 100,
                stop_gain_pct: parseFloat(document.getElementById('stopGain').value) / 100,
                safe_net: parseFloat(document.getElementById('safeNet').value),
                risk_tolerance: document.getElementById('riskTolerance').value,
                recommendation_threshold: parseFloat(document.getElementById('recommendationThreshold').value) / 100
            };
            
            const response = await fetch(`${this.baseUrl}/parameters`, {
                method: 'PUT',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(parameters)
            });
            
            const data = await response.json();
            
            if (data.success) {
                this.currentParameters = data.parameters;
                this.showSuccess('Parameters saved successfully!');
            } else {
                throw new Error(data.error || 'Failed to save parameters');
            }
        } catch (error) {
            console.error('Error saving parameters:', error);
            this.showError('Failed to save parameters: ' + error.message);
        }
    }
    
    /**
     * Run AI backtesting
     */
    async runBacktesting() {
        const collectionId = document.getElementById('dataCollection').value;
        
        if (!collectionId) {
            this.showError('Please select a data collection first.');
            return;
        }
        
        try {
            this.showLoading(true);
            
            const response = await fetch(`${this.baseUrl}/run`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    collection_id: collectionId
                })
            });
            
            const data = await response.json();
            
            if (data.success) {
                this.showSuccess(data.message);
                await this.loadResults();
                await this.loadSummary();
                this.showResults();
            } else {
                throw new Error(data.error || 'Failed to run backtesting');
            }
        } catch (error) {
            console.error('Error running backtesting:', error);
            this.showError('Failed to run backtesting: ' + error.message);
        } finally {
            this.showLoading(false);
        }
    }
    
    /**
     * Load backtesting results
     */
    async loadResults() {
        try {
            const response = await fetch(`${this.baseUrl}/results`);
            const data = await response.json();
            
            if (data.success) {
                this.currentResults = data.results;
                this.populateResultsTable(data.results);
            } else {
                throw new Error(data.error || 'Failed to load results');
            }
        } catch (error) {
            console.error('Error loading results:', error);
            this.showError('Failed to load results.');
        }
    }
    
    /**
     * Load backtesting summary
     */
    async loadSummary() {
        try {
            const response = await fetch(`${this.baseUrl}/summary`);
            const data = await response.json();
            
            if (data.success && data.summary) {
                this.currentSummary = data.summary;
                this.populateSummaryDisplay(data.summary);
            }
        } catch (error) {
            console.error('Error loading summary:', error);
            this.showError('Failed to load summary.');
        }
    }
    
    /**
     * Populate results table
     */
    populateResultsTable(results) {
        const tbody = document.getElementById('resultsTableBody');
        
        if (!results || results.length === 0) {
            tbody.innerHTML = '<tr><td colspan="8" class="text-center text-muted">No results available</td></tr>';
            return;
        }
        
        const rowsHtml = results.map(result => `
            <tr>
                <td><strong>${result.strategy_name}</strong></td>
                <td class="${result.total_return_pct >= 0 ? 'text-success' : 'text-danger'}">
                    ${result.total_return_pct.toFixed(2)}%
                </td>
                <td>${result.sharpe_ratio.toFixed(2)}</td>
                <td class="${result.risk_score < 50 ? 'text-success' : result.risk_score < 70 ? 'text-warning' : 'text-danger'}">
                    ${result.risk_score.toFixed(1)}
                </td>
                <td class="text-danger">${result.max_drawdown_pct.toFixed(2)}%</td>
                <td class="${result.win_rate >= 0.6 ? 'text-success' : result.win_rate >= 0.4 ? 'text-warning' : 'text-danger'}">
                    ${(result.win_rate * 100).toFixed(1)}%
                </td>
                <td>${result.total_trades}</td>
                <td>${result.execution_time.toFixed(2)}</td>
            </tr>
        `).join('');
        
        tbody.innerHTML = rowsHtml;
    }
    
    /**
     * Populate summary display
     */
    populateSummaryDisplay(summary) {
        // Best strategy
        document.getElementById('bestStrategyName').textContent = summary.best_strategy.name;
        document.getElementById('bestStrategyReturn').textContent = `${summary.best_strategy.total_return_pct.toFixed(2)}%`;
        
        // Total return
        document.getElementById('totalReturn').textContent = `$${summary.best_strategy.total_return_pct.toFixed(2)}%`;
        document.getElementById('totalReturnPct').textContent = `Best Strategy`;
        
        // Sharpe ratio
        document.getElementById('sharpeRatio').textContent = summary.best_strategy.sharpe_ratio.toFixed(2);
        document.getElementById('riskScore').textContent = `Risk: ${summary.best_strategy.risk_score.toFixed(1)}`;
        
        // Strategies tested
        document.getElementById('strategiesTested').textContent = summary.total_strategies_tested;
        document.getElementById('executionTime').textContent = `${summary.total_execution_time.toFixed(1)}s`;
        
        // Recommendations
        this.populateRecommendations(summary.recommendations);
    }
    
    /**
     * Populate recommendations
     */
    populateRecommendations(recommendations) {
        const container = document.getElementById('recommendationsList');
        
        if (!recommendations || recommendations.length === 0) {
            container.innerHTML = '<p class="text-muted">No recommendations available.</p>';
            return;
        }
        
        const recommendationsHtml = recommendations.map(rec => 
            `<div class="alert alert-info mb-2">
                <i class="fas fa-lightbulb me-2"></i>${rec}
            </div>`
        ).join('');
        
        container.innerHTML = recommendationsHtml;
    }
    
    /**
     * Reset backtesting results
     */
    async resetResults() {
        if (!confirm('Are you sure you want to reset all backtesting results? This action cannot be undone.')) {
            return;
        }
        
        try {
            const response = await fetch(`${this.baseUrl}/reset`, {
                method: 'POST'
            });
            
            const data = await response.json();
            
            if (data.success) {
                this.showSuccess('Results reset successfully!');
                this.currentResults = [];
                this.currentSummary = null;
                this.hideResults();
                await this.loadStatus();
            } else {
                throw new Error(data.error || 'Failed to reset results');
            }
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
            const response = await fetch(`${this.baseUrl}/export`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    filename: `ai_backtest_results_${new Date().toISOString().slice(0, 19).replace(/:/g, '-')}.csv`
                })
            });
            
            const data = await response.json();
            
            if (data.success) {
                this.showSuccess('Results exported successfully!');
            } else {
                throw new Error(data.error || 'Failed to export results');
            }
        } catch (error) {
            console.error('Error exporting results:', error);
            this.showError('Failed to export results: ' + error.message);
        }
    }
    
    /**
     * Validate data collection selection
     */
    validateDataCollection() {
        const collectionId = document.getElementById('dataCollection').value;
        const runButton = document.getElementById('runBacktestBtn');
        
        if (collectionId) {
            runButton.disabled = false;
            runButton.classList.remove('btn-secondary');
            runButton.classList.add('btn-success');
        } else {
            runButton.disabled = true;
            runButton.classList.remove('btn-success');
            runButton.classList.add('btn-secondary');
        }
    }
    
    /**
     * Show loading overlay
     */
    showLoading(show) {
        const overlay = document.getElementById('loadingOverlay');
        if (show) {
            overlay.classList.remove('d-none');
        } else {
            overlay.classList.add('d-none');
        }
    }
    
    /**
     * Show results section
     */
    showResults() {
        document.getElementById('resultsSection').classList.remove('d-none');
    }
    
    /**
     * Hide results section
     */
    hideResults() {
        document.getElementById('resultsSection').classList.add('d-none');
    }
    
    /**
     * Show success message
     */
    showSuccess(message) {
        // You can implement a toast notification system here
        console.log('Success:', message);
        alert('Success: ' + message);
    }
    
    /**
     * Show error message
     */
    showError(message) {
        // You can implement a toast notification system here
        console.error('Error:', message);
        alert('Error: ' + message);
    }
}

// Initialize the modal when the page loads
document.addEventListener('DOMContentLoaded', () => {
    // Only initialize if the modal exists
    if (document.getElementById('aiBacktestingModal')) {
        window.aiBacktestingModal = new AIBacktestingModal();
    }
});

// Export for use in other scripts
if (typeof module !== 'undefined' && module.exports) {
    module.exports = AIBacktestingModal;
}
