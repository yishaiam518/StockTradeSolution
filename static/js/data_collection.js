// Data Collection JavaScript
// Global function wrappers for inline onclick handlers
function updateCollection(collectionId) {
    console.log('Global updateCollection called with:', collectionId);
    console.log('window.dataCollectionManager exists:', !!window.dataCollectionManager);
    if (window.dataCollectionManager) {
        window.dataCollectionManager.updateCollection(collectionId);
    } else {
        console.error('dataCollectionManager not found!');
    }
}

function refreshAIRanking(collectionId) {
    if (window.dataCollectionManager) {
        window.dataCollectionManager.refreshAIRankingData(collectionId);
    }
}

async function exportAIRankingReport(collectionId) {
    try {
        const response = await fetch(`/api/ai-ranking/collection/${collectionId}/export?format=json`);
        const data = await response.json();
        
        if (data.success) {
            // Create and download file
            const blob = new Blob([JSON.stringify(data.data, null, 2)], { type: 'application/json' });
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `ai-ranking-${collectionId}-${new Date().toISOString().split('T')[0]}.json`;
            document.body.appendChild(a);
            a.click();
            window.URL.revokeObjectURL(url);
            document.body.removeChild(a);
        } else {
            alert('Error exporting report');
        }
    } catch (error) {
        console.error('Error exporting report:', error);
        alert('Error exporting report');
    }
}

function toggleAutoUpdate(collectionId, enable) {
    if (window.dataCollectionManager) {
        window.dataCollectionManager.toggleAutoUpdate(collectionId, enable);
    }
}

function viewCollection(collectionId) {
    if (window.dataCollectionManager) {
        window.dataCollectionManager.viewCollection(collectionId);
    }
}

function deleteCollection(collectionId) {
    if (window.dataCollectionManager) {
        window.dataCollectionManager.deleteCollection(collectionId);
    }
}

function setCollectionInterval(collectionId, interval) {
    if (window.dataCollectionManager) {
        window.dataCollectionManager.setCollectionInterval(collectionId, interval);
    }
}

function startCollectionScheduler(collectionId) {
    if (window.dataCollectionManager) {
        window.dataCollectionManager.startCollectionScheduler(collectionId);
    }
}

function stopCollectionScheduler(collectionId) {
    if (window.dataCollectionManager) {
        window.dataCollectionManager.stopCollectionScheduler(collectionId);
    }
}

function calculateCollectionIndicators(collectionId) {
    if (window.dataCollectionManager) {
        window.dataCollectionManager.calculateCollectionIndicators(collectionId);
    }
}

function openPerformanceAnalytics(collectionId) {
    if (window.dataCollectionManager) {
        window.dataCollectionManager.openPerformanceAnalytics(collectionId);
    }
}

function openAIRanking(collectionId) {
    if (window.dataCollectionManager) {
        window.dataCollectionManager.openAIRanking(collectionId);
    }
}

class DataCollectionManager {
    constructor() {
        this.initializeEventListeners();
        this.loadExchanges();
        this.loadCollections();
    }

    initializeEventListeners() {
        // Form submission
        const collectionForm = document.getElementById('collectionForm');
        if (collectionForm) {
            collectionForm.addEventListener('submit', (e) => {
                e.preventDefault();
                this.startDataCollection();
            });
        }

        // Time period change
        const timePeriod = document.getElementById('timePeriod');
        if (timePeriod) {
            timePeriod.addEventListener('change', (e) => {
                const customRange = document.getElementById('customDateRange');
                if (customRange) {
                    if (e.target.value === 'custom') {
                        customRange.style.display = 'block';
                    } else {
                        customRange.style.display = 'none';
                    }
                }
            });
        }

        // Delete confirmation
        const confirmDelete = document.getElementById('confirmDelete');
        if (confirmDelete) {
            confirmDelete.addEventListener('click', () => {
                this.deleteConfirmedCollection();
            });
        }

        // Auto-refresh collections every 30 seconds
        setInterval(() => {
            this.loadCollections();
        }, 30000);
    }

    async loadExchanges() {
        try {
            const response = await fetch('/api/data-collection/exchanges');
            const data = await response.json();
            
            if (data.success) {
                const exchangeSelect = document.getElementById('exchange');
                data.exchanges.forEach(exchange => {
                    const option = document.createElement('option');
                    option.value = exchange;
                    option.textContent = exchange;
                    exchangeSelect.appendChild(option);
                });
            }
        } catch (error) {
            console.error('Error loading exchanges:', error);
            this.showAlert('Error loading exchanges', 'danger');
        }
    }

    async loadCollections() {
        try {
            console.log('Loading collections...');
            const response = await fetch('/api/data-collection/collections');
            const data = await response.json();
            console.log('Collections loaded:', data);
            
            // Handle the API response structure
            const collections = data.success ? data.collections : data;
            console.log('Collections to display:', collections);
            console.log('Container element:', document.getElementById('collectionsContainer'));
            
            this.displayCollections(collections);
            
            // Load scheduler status for each collection
            for (const collection of collections) {
                if (collection.auto_update) {
                    this.loadCollectionSchedulerStatus(collection.collection_id);
                }
            }
        } catch (error) {
            console.error('Error loading collections:', error);
            this.showAlert('Error loading collections', 'danger');
        }
    }

    displayCollections(collections) {
        console.log('displayCollections called with:', collections);
        const container = document.getElementById('collectionsContainer');
        console.log('Container found:', container);
        if (!container) {
            console.error('Container not found');
            return;
        }
        
        // Clear existing content
        container.innerHTML = '';
        
        if (!collections || collections.length === 0) {
            container.innerHTML = `
                <div class="col-12">
                    <div class="alert alert-info text-center">
                        <i class="fas fa-info-circle"></i> No data collections found. Start by creating a new collection.
                    </div>
                </div>
            `;
            return;
        }
        
        // Create a row container for proper grid layout
        const row = document.createElement('div');
        row.className = 'row';
        container.appendChild(row);
        
        collections.forEach(collection => {
            const card = document.createElement('div');
            card.className = 'col-md-6 col-lg-4 mb-4';
            card.setAttribute('data-collection-id', collection.collection_id);
            
            const schedulerDisplay = collection.auto_update ? 'block' : 'none';
            const intervalButtons = ['1min', '5min', '10min', '30min', '1h', '24h'].map(interval => 
                `<button type="button" class="btn ${collection.update_interval === interval ? 'btn-primary' : 'btn-outline-primary'} btn-sm" onclick="setCollectionInterval('${collection.collection_id}', '${interval}')">${interval === '1min' ? '1 min' : interval === '1h' ? '1 hour' : interval === '24h' ? '24 hours' : interval}</button>`
            ).join('');

            // Default to not running (show Start button, hide Stop button)
            const isRunning = collection.auto_update === true;
            const startButtonDisplay = isRunning ? 'none' : 'inline-block';
            const stopButtonDisplay = isRunning ? 'inline-block' : 'none';

            card.innerHTML = `
                <div class="card h-100">
                    <div class="card-body">
                        <div class="d-flex justify-content-between align-items-start mb-2">
                            <h6 class="card-title mb-0">${collection.exchange}</h6>
                            <span class="badge ${collection.failed_count > 0 ? 'bg-danger' : 'bg-success'}">${collection.failed_count} failed</span>
                        </div>
                        <p class="card-text small text-muted mb-2">
                            ${collection.start_date} to ${collection.end_date}<br>
                            ${collection.successful_symbols} symbols collected
                        </p>
                        <p class="card-text small text-muted mb-3">
                            Last update: ${collection.last_updated || 'Never'}
                        </p>
                        
                        <!-- Action Buttons -->
                        <div class="action-buttons mt-3 mb-3">
                            <div class="btn-group w-100" role="group">
                                <button type="button" class="btn btn-primary btn-sm" onclick="viewCollection('${collection.collection_id}')">
                                    <i class="fas fa-chart-line"></i> View Data
                                </button>
                                <button type="button" class="btn btn-success btn-sm" onclick="openPerformanceAnalytics('${collection.collection_id}')">
                                    <i class="fas fa-chart-bar"></i> Analytics
                                </button>
                                <button type="button" class="btn btn-warning btn-sm" onclick="openAIRanking('${collection.collection_id}')">
                                    <i class="fas fa-robot"></i> AI Ranking
                                </button>
                                <button type="button" class="btn btn-info btn-sm" onclick="updateCollection('${collection.collection_id}')">
                                    <i class="fas fa-sync"></i> Update
                                </button>
                                <button type="button" class="btn btn-danger btn-sm" onclick="deleteCollection('${collection.collection_id}')">
                                    <i class="fas fa-trash"></i> Delete
                                </button>
                            </div>
                        </div>

                        <!-- Scheduler Controls -->
                        <div class="scheduler-controls mt-3">
                            <!-- Row 1: Time Interval Selection (Full Width) -->
                            <div class="col-12 mb-3">
                                <div class="d-flex flex-column">
                                    <label class="form-label small text-muted mb-2">Update Interval:</label>
                                    <div class="d-flex flex-wrap gap-1">
                                        ${intervalButtons}
                                    </div>
                                    <small class="text-muted mt-1">Current: ${collection.update_interval || '24h'}</small>
                                </div>
                            </div>
                            
                            <!-- Row 2: Start/Stop Controls and Status -->
                            <div class="row">
                                <div class="col-md-6">
                                    <div class="btn-group w-100" role="group">
                                        <button type="button" class="btn btn-success btn-sm scheduler-btn" id="start-${collection.collection_id}" onclick="startScheduler('${collection.collection_id}')" style="display: ${collection.auto_update ? 'none' : 'inline-block'};">
                                            <i class="fas fa-play"></i> Start
                                        </button>
                                        <button type="button" class="btn btn-danger btn-sm scheduler-btn" id="stop-${collection.collection_id}" onclick="stopScheduler('${collection.collection_id}')" style="display: ${collection.auto_update ? 'inline-block' : 'none'};">
                                            <i class="fas fa-stop"></i> Stop
                                        </button>
                                    </div>
                                </div>
                                <div class="col-md-6">
                                    <div class="d-flex flex-column">
                                        <div class="small text-muted">
                                            <span id="last-run-${collection.collection_id}">Data: ${collection.last_run ? new Date(collection.last_run).toLocaleString() : 'Never'}</span> | 
                                            <span id="next-run-${collection.collection_id}">Next: ${collection.next_run ? new Date(collection.next_run).toLocaleString() : 'Not scheduled'}</span>
                                        </div>
                                        <div class="small text-info">
                                            <span id="ai-ranking-last-update-${collection.collection_id}">
                                                <i class="fas fa-robot"></i> AI Ranking: ${collection.ai_ranking_last_update ? new Date(collection.ai_ranking_last_update).toLocaleString() : 'Never'}
                                            </span>
                                        </div>
                                    </div>
                                </div>
                            </div>
                        </div>
                        
                        <!-- Technical Indicators Section -->
                        <div class="technical-indicators mt-3">
                            <div class="d-flex justify-content-between align-items-center mb-2">
                                <label class="form-label small text-muted mb-0">Technical Indicators:</label>
                                <button type="button" class="btn btn-outline-primary btn-sm" onclick="window.dataCollectionManager.calculateCollectionIndicators('${collection.collection_id}')">
                                    <i class="fas fa-calculator"></i> Calculate
                                </button>
                            </div>
                            <div id="indicators-status-${collection.collection_id}" class="indicators-status">
                                <div class="indicators-info">
                                    <span class="badge bg-secondary">Loading...</span>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            `;
            
            row.appendChild(card);
            
            // Load indicators status for this collection
            this.loadCollectionIndicatorsStatus(collection.collection_id);
        });
    }

    handleTimePeriodChange(period) {
        const customDateRange = document.getElementById('customDateRange');
        
        if (period === 'custom') {
            customDateRange.style.display = 'block';
        } else {
            customDateRange.style.display = 'none';
            this.setDefaultDates(period);
        }
    }

    setDefaultDates(period) {
        const endDate = new Date();
        let startDate = new Date();
        
        switch (period) {
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
        
        document.getElementById('startDate').value = startDate.toISOString().split('T')[0];
        document.getElementById('endDate').value = endDate.toISOString().split('T')[0];
    }

    async startDataCollection() {
        const form = document.getElementById('collectionForm');
        const formData = new FormData(form);
        
        // Validate form
        if (!this.validateForm(formData)) {
            return;
        }

        // Prepare data
        const data = {
            exchange: formData.get('exchange'),
            start_date: formData.get('startDate'),
            end_date: formData.get('endDate'),
            symbols: formData.get('symbols') ? formData.get('symbols').split(',').map(s => s.trim()) : null,
            sectors: formData.get('sectors') ? formData.get('sectors').split(',').map(s => s.trim()) : null,
            market_cap_min: formData.get('marketCapMin') ? parseFloat(formData.get('marketCapMin')) : null,
            market_cap_max: formData.get('marketCapMax') ? parseFloat(formData.get('marketCapMax')) : null,
            include_etfs: formData.get('includeEtfs') === 'on',
            include_penny_stocks: formData.get('includePennyStocks') === 'on'
        };

        // Show loading state
        const submitBtn = form.querySelector('button[type="submit"]');
        const originalText = submitBtn.innerHTML;
        submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Collecting...';
        submitBtn.disabled = true;

        try {
            const response = await fetch('/api/data-collection/start', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(data)
            });

            const result = await response.json();

            if (result.success) {
                this.showAlert(`Data collection started successfully! Collected ${result.successful_symbols} symbols.`, 'success');
                form.reset();
                this.loadCollections(); // Refresh the list
            } else {
                this.showAlert(`Error: ${result.error}`, 'danger');
            }
        } catch (error) {
            console.error('Error starting data collection:', error);
            this.showAlert('Error starting data collection', 'danger');
        } finally {
            // Restore button state
            submitBtn.innerHTML = originalText;
            submitBtn.disabled = false;
        }
    }

    validateForm(formData) {
        if (!formData.get('exchange')) {
            this.showAlert('Please select an exchange', 'warning');
            return false;
        }

        const timePeriod = document.getElementById('timePeriod').value;
        if (timePeriod === 'custom') {
            if (!formData.get('startDate') || !formData.get('endDate')) {
                this.showAlert('Please select start and end dates', 'warning');
                return false;
            }
        }

        return true;
    }

    async viewCollection(collectionId) {
        try {
            const response = await fetch(`/api/data-collection/collections/${collectionId}`);
            const data = await response.json();
            
            if (data.success) {
                // Open stock viewer directly instead of showing modal
                this.openStockViewer(data.collection);
            } else {
                this.showAlert(`Error loading collection: ${data.error}`, 'danger');
            }
        } catch (error) {
            console.error('Error viewing collection:', error);
            this.showAlert('Error loading collection details', 'danger');
        }
    }

    openStockViewer(collection) {
        // Create URL for stock viewer with collection parameters
        const url = `/stock-viewer?collection_id=${collection.collection_id}&exchange=${collection.exchange}&start_date=${collection.start_date}&end_date=${collection.end_date}`;
        
        // Open in new window/tab
        window.open(url, '_blank', 'width=1400,height=900,scrollbars=yes,resizable=yes,menubar=no,toolbar=no,location=no,status=no');
    }

    showCollectionDetails(collection) {
                    // Create modal content with stock viewer
                    const modalContent = `
                        <div class="modal-header">
                            <h5 class="modal-title">
                                <i class="fas fa-database"></i> Collection Details - ${collection.exchange}
                            </h5>
                            <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                        </div>
                        <div class="modal-body">
                            <!-- Collection Info -->
                            <div class="row mb-4">
                                <div class="col-md-6">
                                    <h6><i class="fas fa-building"></i> Exchange</h6>
                                    <p class="text-muted">${collection.exchange}</p>
                                    
                                    <h6><i class="fas fa-calendar"></i> Date Range</h6>
                                    <p class="text-muted">${collection.start_date} to ${collection.end_date}</p>
                                    
                                    <h6><i class="fas fa-clock"></i> Collection Date</h6>
                                    <p class="text-muted">${new Date(collection.collection_date).toLocaleString()}</p>
                                </div>
                                <div class="col-md-6">
                                    <h6><i class="fas fa-chart-bar"></i> Statistics</h6>
                                    <div class="row">
                                        <div class="col-6">
                                            <p class="text-muted mb-1">Total Symbols</p>
                                            <h5 class="text-primary">${collection.total_symbols}</h5>
                                        </div>
                                        <div class="col-6">
                                            <p class="text-muted mb-1">Successful</p>
                                            <h5 class="text-success">${collection.successful_symbols}</h5>
                                        </div>
                                    </div>
                                    <div class="row mt-2">
                                        <div class="col-6">
                                            <p class="text-muted mb-1">Failed</p>
                                            <h5 class="text-danger">${collection.failed_count}</h5>
                                        </div>
                                        <div class="col-6">
                                            <p class="text-muted mb-1">Success Rate</p>
                                            <h5 class="text-info">${Math.round((collection.successful_symbols / collection.total_symbols) * 100)}%</h5>
                                        </div>
                                    </div>
                                </div>
                            </div>
                            
                            <div class="mt-3 mb-4">
                                <h6><i class="fas fa-info-circle"></i> Status</h6>
                                <span class="badge bg-success">${collection.status}</span>
                            </div>

                            <!-- Stock Viewer Section -->
                            <div class="stock-viewer-section">
                                <h6><i class="fas fa-chart-line"></i> Professional Stock Analysis</h6>
                                <div class="row mb-3">
                                    <div class="col-md-4">
                                        <label for="stockSelector" class="form-label">Select Stock</label>
                                        <div class="input-group">
                                            <input type="text" class="form-control" id="stockSearch" placeholder="Search stocks..." onkeyup="dataCollectionManager.filterStocks()">
                                            <select class="form-select" id="stockSelector" onchange="dataCollectionManager.loadStockData('${collection.collection_id}')">
                                                <option value="">Choose a stock...</option>
                                            </select>
                                        </div>
                                    </div>
                                    <div class="col-md-8">
                                        <div id="stockInfo" style="display: none;">
                                            <div class="card">
                                                <div class="card-body">
                                                    <div class="row">
                                                        <div class="col-md-6">
                                                            <h4 id="stockSymbol" class="card-title text-primary"></h4>
                                                            <div id="stockPrice"></div>
                                                        </div>
                                                        <div class="col-md-6">
                                                            <div class="text-end">
                                                                <small class="text-muted">Data from ${collection.start_date} to ${collection.end_date}</small>
                                                            </div>
                                                        </div>
                                                    </div>
                                                </div>
                                            </div>
                                        </div>
                                    </div>
                                </div>
                                <div id="stockChart" style="display: none;">
                                    <!-- Chart will be rendered here -->
                                </div>
                            </div>
                        </div>
                        <div class="modal-footer">
                            <button type="button" class="btn btn-primary" onclick="dataCollectionManager.openFullScreenViewer('${collection.collection_id}', '${collection.exchange}', '${collection.start_date}', '${collection.end_date}')">
                                <i class="fas fa-expand"></i> Full Screen Viewer
                            </button>
                            <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Close</button>
                            <button type="button" class="btn btn-danger" onclick="dataCollectionManager.confirmDelete('${collection.collection_id}')">
                                <i class="fas fa-trash"></i> Delete Collection
                            </button>
                        </div>
                    `;
                    
                    // Create or update modal
                    let modal = document.getElementById('collectionDetailsModal');
                    if (!modal) {
                        modal = document.createElement('div');
                        modal.className = 'modal fade';
                        modal.id = 'collectionDetailsModal';
                        modal.innerHTML = `
                            <div class="modal-dialog modal-xl">
                                <div class="modal-content">
                                    ${modalContent}
                                </div>
                            </div>
                        `;
                        document.body.appendChild(modal);
                    } else {
                        modal.querySelector('.modal-content').innerHTML = modalContent;
                    }
                    
                    // Show modal and load stock list
                    const bootstrapModal = new bootstrap.Modal(modal);
                    bootstrapModal.show();
                    
                    // Load available stocks for this collection
                    this.loadStockList(collection.collection_id);
                }

                async loadStockList(collectionId) {
                    try {
                        const response = await fetch(`/api/data-collection/collections/${collectionId}`);
                        const data = await response.json();
                        
                        if (data.success && data.collection.symbols_count > 0) {
                            // Get the stock symbols from the collection
                            const stockResponse = await fetch(`/api/data-collection/collections/${collectionId}/symbols`);
                            const stockData = await stockResponse.json();
                            
                            if (stockData.success) {
                                const stockSelector = document.getElementById('stockSelector');
                                stockSelector.innerHTML = '<option value="">Choose a stock...</option>';
                                
                                stockData.symbols.forEach(symbol => {
                                    const option = document.createElement('option');
                                    option.value = symbol;
                                    option.textContent = symbol;
                                    stockSelector.appendChild(option);
                                });
                            }
                        }
                    } catch (error) {
                        console.error('Error loading stock list:', error);
                    }
                }

                async loadStockData(collectionId) {
                    const stockSelector = document.getElementById('stockSelector');
                    const selectedSymbol = stockSelector.value;
                    
                    if (!selectedSymbol) {
                        document.getElementById('stockInfo').style.display = 'none';
                        return;
                    }
                    
                    try {
                        const response = await fetch(`/api/data-collection/collections/${collectionId}/symbols/${selectedSymbol}`);
                        const data = await response.json();
                        
                        if (data.success) {
                            this.displayStockInfo(selectedSymbol, data.stock_data);
                        }
                    } catch (error) {
                        console.error('Error loading stock data:', error);
                    }
                }

                displayStockInfo(symbol, stockData) {
                    const stockInfo = document.getElementById('stockInfo');
                    const stockSymbol = document.getElementById('stockSymbol');
                    const stockPrice = document.getElementById('stockPrice');
                    const stockChange = document.getElementById('stockChange');
                    
                    // Update stock info
                    stockSymbol.textContent = symbol;
                    
                    if (stockData && stockData.length > 0) {
                        const latest = stockData[stockData.length - 1];
                        const previous = stockData[stockData.length - 2];
                        
                        const currentPrice = latest.Close;
                        const previousPrice = previous ? previous.Close : currentPrice;
                        const change = currentPrice - previousPrice;
                        const changePercent = (change / previousPrice) * 100;
                        
                        // Calculate additional metrics
                        const high = Math.max(...stockData.map(d => d.High));
                        const low = Math.min(...stockData.map(d => d.Low));
                        const avgVolume = stockData.reduce((sum, d) => sum + d.Volume, 0) / stockData.length;
                        
                        stockPrice.innerHTML = `
                            <div class="row">
                                <div class="col-md-6">
                                    <h3 class="text-primary mb-1">$${currentPrice.toFixed(2)}</h3>
                                    <p class="mb-0 ${change >= 0 ? 'text-success' : 'text-danger'}">
                                        ${change >= 0 ? '+' : ''}${change.toFixed(2)} (${changePercent.toFixed(2)}%)
                                    </p>
                                </div>
                                <div class="col-md-6">
                                    <small class="text-muted">
                                        <div>High: $${high.toFixed(2)}</div>
                                        <div>Low: $${low.toFixed(2)}</div>
                                        <div>Avg Volume: ${Math.round(avgVolume).toLocaleString()}</div>
                                    </small>
                                </div>
                            </div>
                        `;
                        
                        // Show the stock info
                        stockInfo.style.display = 'block';
                        
                        // Initialize Syncfusion license
                        ej.base.setLicenseKey('Ngo9BigBOggjHTQxAR8/V1JEaF5cXmRCf1FpRmJGdld5fUVHYVZUTXxaS00DNHVRdkdmWXdec3VTRWZfU0BxWENWYE0=');
                        
                        // Create chart
                        this.createStockChart(stockData);
                    }
                }

                createStockChart(stockData) {
                    const chartContainer = document.getElementById('stockChart');
                    chartContainer.style.display = 'block';
                    chartContainer.innerHTML = `
                        <div class="card">
                            <div class="card-header">
                                <div class="d-flex justify-content-between align-items-center">
                                    <h6 class="mb-0">Price Chart</h6>
                                    <div class="btn-group" role="group">
                                        <button type="button" class="btn btn-outline-primary btn-sm" onclick="dataCollectionManager.changeChartType('line')">Line</button>
                                        <button type="button" class="btn btn-outline-primary btn-sm" onclick="dataCollectionManager.changeChartType('candlestick')">Candlestick</button>
                                        <button type="button" class="btn btn-outline-primary btn-sm" onclick="dataCollectionManager.changeChartType('ohlc')">OHLC</button>
                                    </div>
                                    <div class="btn-group" role="group">
                                        <button type="button" class="btn btn-outline-secondary btn-sm" onclick="dataCollectionManager.changeTimeframe('1M')">1M</button>
                                        <button type="button" class="btn btn-outline-secondary btn-sm" onclick="dataCollectionManager.changeTimeframe('3M')">3M</button>
                                        <button type="button" class="btn btn-outline-secondary btn-sm" onclick="dataCollectionManager.changeTimeframe('6M')">6M</button>
                                        <button type="button" class="btn btn-outline-secondary btn-sm" onclick="dataCollectionManager.changeTimeframe('1Y')">1Y</button>
                                        <button type="button" class="btn btn-outline-secondary btn-sm" onclick="dataCollectionManager.changeTimeframe('ALL')">ALL</button>
                                    </div>
                                </div>
                            </div>
                            <div class="card-body">
                                <div id="stockChartCanvas" style="height: 400px; width: 100%;"></div>
                            </div>
                        </div>
                    `;
                    
                    // Store data for chart type switching
                    this.currentChartData = stockData;
                    this.currentChartType = 'line';
                    this.currentTimeframe = 'ALL';
                    
                    this.renderChart();
                }

                renderChart() {
                    if (!this.currentChartData) return;
                    
                    // Filter data based on timeframe
                    const filteredData = this.filterDataByTimeframe(this.currentChartData, this.currentTimeframe);
                    
                    // Transform data for Syncfusion
                    const chartData = filteredData.map(d => ({
                        date: new Date(d.Date),
                        close: d.Close,
                        high: d.High,
                        low: d.Low,
                        open: d.Open,
                        volume: d.Volume
                    }));
                    
                    // Clear previous chart
                    const chartContainer = document.getElementById('stockChartCanvas');
                    chartContainer.innerHTML = '';
                    
                    if (this.currentChartType === 'candlestick') {
                        this.createCandlestickChart(chartData);
                    } else if (this.currentChartType === 'ohlc') {
                        this.createOHLCChart(chartData);
                    } else {
                        this.createLineChart(chartData);
                    }
                }

                createLineChart(chartData) {
                    const chart = new ej.charts.Chart({
                        primaryXAxis: {
                            valueType: 'DateTime',
                            majorGridLines: { width: 0 },
                            crosshairTooltip: { enable: true }
                        },
                        primaryYAxis: {
                            labelFormat: '${value}',
                            majorTickLines: { width: 0 },
                            lineStyle: { width: 0 }
                        },
                        chartArea: {
                            border: { width: 0 }
                        },
                        tooltip: {
                            enable: true,
                            shared: true,
                            format: '${point.x} : $${point.y}'
                        },
                        crosshair: {
                            enable: true,
                            lineType: 'Vertical'
                        },
                        series: [
                            {
                                dataSource: chartData,
                                xName: 'date',
                                yName: 'close',
                                type: 'Line',
                                width: 2,
                                fill: '#3C78D8',
                                border: { color: '#3C78D8', width: 2 }
                            }
                        ],
                        width: '100%',
                        height: '400px'
                    });
                    
                    chart.appendTo('#stockChartCanvas');
                }

                createCandlestickChart(chartData) {
                    const chart = new ej.charts.Chart({
                        primaryXAxis: {
                            valueType: 'DateTime',
                            majorGridLines: { width: 0 },
                            crosshairTooltip: { enable: true }
                        },
                        primaryYAxis: {
                            labelFormat: '${value}',
                            majorTickLines: { width: 0 },
                            lineStyle: { width: 0 }
                        },
                        chartArea: {
                            border: { width: 0 }
                        },
                        tooltip: {
                            enable: true,
                            shared: true,
                            format: 'Open: ${open}<br/>High: ${high}<br/>Low: ${low}<br/>Close: ${close}'
                        },
                        crosshair: {
                            enable: true,
                            lineType: 'Vertical'
                        },
                        series: [
                            {
                                dataSource: chartData,
                                xName: 'date',
                                low: 'low',
                                high: 'high',
                                open: 'open',
                                close: 'close',
                                type: 'Candle',
                                bearFillColor: '#F44336',
                                bullFillColor: '#4CAF50',
                                border: { color: '#000000' }
                            }
                        ],
                        width: '100%',
                        height: '400px'
                    });
                    
                    chart.appendTo('#stockChartCanvas');
                }

                createOHLCChart(chartData) {
                    const chart = new ej.charts.Chart({
                        primaryXAxis: {
                            valueType: 'DateTime',
                            majorGridLines: { width: 0 },
                            crosshairTooltip: { enable: true }
                        },
                        primaryYAxis: {
                            labelFormat: '${value}',
                            majorTickLines: { width: 0 },
                            lineStyle: { width: 0 }
                        },
                        chartArea: {
                            border: { width: 0 }
                        },
                        tooltip: {
                            enable: true,
                            shared: true,
                            format: 'Open: ${open}<br/>High: ${high}<br/>Low: ${low}<br/>Close: ${close}'
                        },
                        crosshair: {
                            enable: true,
                            lineType: 'Vertical'
                        },
                        series: [
                            {
                                dataSource: chartData,
                                xName: 'date',
                                low: 'low',
                                high: 'high',
                                open: 'open',
                                close: 'close',
                                type: 'HiloOpenClose',
                                bearFillColor: '#F44336',
                                bullFillColor: '#4CAF50',
                                border: { color: '#000000' }
                            }
                        ],
                        width: '100%',
                        height: '400px'
                    });
                    
                    chart.appendTo('#stockChartCanvas');
                }

                changeChartType(type) {
                    this.currentChartType = type;
                    this.renderChart();
                }

                changeTimeframe(timeframe) {
                    this.currentTimeframe = timeframe;
                    this.renderChart();
                }

                filterDataByTimeframe(data, timeframe) {
                    if (timeframe === 'ALL') return data;
                    
                    const now = new Date();
                    let startDate = new Date();
                    
                    switch (timeframe) {
                        case '1M':
                            startDate.setMonth(now.getMonth() - 1);
                            break;
                        case '3M':
                            startDate.setMonth(now.getMonth() - 3);
                            break;
                        case '6M':
                            startDate.setMonth(now.getMonth() - 6);
                            break;
                        case '1Y':
                            startDate.setFullYear(now.getFullYear() - 1);
                            break;
                        default:
                            return data;
                    }
                    
                    return data.filter(d => new Date(d.Date) >= startDate);
                }

                filterStocks() {
                    const searchTerm = document.getElementById('stockSearch').value.toLowerCase();
                    const stockSelector = document.getElementById('stockSelector');
                    const options = stockSelector.options;
                    
                    for (let i = 0; i < options.length; i++) {
                        const option = options[i];
                        const text = option.textContent.toLowerCase();
                        
                        if (text.includes(searchTerm)) {
                            option.style.display = '';
                        } else {
                            option.style.display = 'none';
                        }
                    }
                }

                openFullScreenViewer(collectionId, exchange, startDate, endDate) {
                    // Create a new window with the stock viewer
                    const url = `/stock-viewer?collection_id=${collectionId}&exchange=${exchange}&start_date=${startDate}&end_date=${endDate}`;
                    const features = 'width=1400,height=900,scrollbars=yes,resizable=yes,menubar=no,toolbar=no,location=no,status=no';
                    window.open(url, '_blank', features);
                }

    confirmDelete(collectionId) {
        this.collectionToDelete = collectionId;
        const modal = new bootstrap.Modal(document.getElementById('deleteModal'));
        modal.show();
    }

    async deleteCollection() {
        if (!this.collectionToDelete) return;

        try {
            const response = await fetch(`/api/data-collection/collections/${this.collectionToDelete}`, {
                method: 'DELETE'
            });

            const result = await response.json();

            if (result.success) {
                this.showAlert('Collection deleted successfully', 'success');
                this.loadCollections(); // Refresh the list
            } else {
                this.showAlert('Error deleting collection: ' + result.error, 'danger');
            }
        } catch (error) {
            console.error('Error deleting collection:', error);
            this.showAlert('Error deleting collection', 'danger');
        }

        // Close modal
        const modal = bootstrap.Modal.getInstance(document.getElementById('deleteModal'));
        if (modal) {
            modal.hide();
        }
        
        this.collectionToDelete = null;
    }

    async updateCollection(collectionId) {
        try {
            console.log('Starting update for collection:', collectionId);
            this.showAlert('Updating collection...', 'info');
            
            const response = await fetch(`/api/data-collection/collections/${collectionId}/update`, {
                method: 'POST'
            });
            
            console.log('Update response status:', response.status);
            const data = await response.json();
            console.log('Update response data:', data);
            
            if (data.success) {
                this.showAlert(`Collection updated successfully! ${data.updated_symbols} symbols updated, ${data.failed_symbols} failed`, 'success');
                // Force reload collections to show updated data
                console.log('Scheduling collection reload in 1 second...');
                setTimeout(() => {
                    console.log('Reloading collections after update...');
                    this.loadCollections();
                }, 1000);
            } else {
                this.showAlert('Error updating collection: ' + data.error, 'danger');
            }
        } catch (error) {
            console.error('Error updating collection:', error);
            this.showAlert('Error updating collection', 'danger');
        }
    }

    async setCollectionInterval(collectionId, interval) {
        try {
            const response = await fetch(`/api/data-collection/collections/${collectionId}/auto-update`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    enable: true,
                    interval: interval
                })
            });
            
            const data = await response.json();
            
            if (data.success) {
                this.showAlert(`Collection interval updated to ${interval}`, 'success');
                // Refresh the collections display to show the updated interval selection
                this.loadCollections();
            } else {
                this.showAlert('Error updating collection interval: ' + data.error, 'danger');
            }
        } catch (error) {
            console.error('Error setting collection interval:', error);
            this.showAlert('Error updating collection interval', 'danger');
        }
    }

    async toggleAutoUpdate(collectionId, enable) {
        try {
            // First get current details to see if auto-update is enabled
            const detailsResponse = await fetch(`/api/data-collection/collections/${collectionId}`);
            const detailsData = await detailsResponse.json();
            
            if (!detailsData.success) {
                this.showAlert('Error getting collection details: ' + detailsData.error, 'danger');
                return;
            }
            
            const currentAutoUpdate = detailsData.collection.auto_update || false;
            const newAutoUpdate = !currentAutoUpdate; // Simply toggle the current state
            
            // If enabling, use the current interval or default to 24h
            const interval = detailsData.collection.update_interval || '24h';
            
            const response = await fetch(`/api/data-collection/collections/${collectionId}/auto-update`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    enable: newAutoUpdate,
                    interval: interval
                })
            });
            
            const data = await response.json();
            
            if (data.success) {
                const status = newAutoUpdate ? 'enabled' : 'disabled';
                this.showAlert(`Auto-update ${status} for collection`, 'success');
                this.loadCollections();
            } else {
                this.showAlert('Error toggling auto-update: ' + data.error, 'danger');
            }
        } catch (error) {
            console.error('Error toggling auto-update:', error);
            this.showAlert('Error toggling auto-update', 'danger');
        }
    }

    async startCollectionScheduler(collectionId) {
        try {
            const response = await fetch(`/api/data-collection/collections/${collectionId}/scheduler/start`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                }
            });
            
            const data = await response.json();
            
            if (data.success) {
                this.showAlert(`Scheduler started for collection ${collectionId}`, 'success');
                document.getElementById(`start-${collectionId}`).style.display = 'none';
                document.getElementById(`stop-scheduler-${collectionId}`).style.display = 'inline-block';
                document.getElementById(`status-${collectionId}`).textContent = 'Running';
            } else {
                this.showAlert('Error starting scheduler: ' + data.error, 'danger');
            }
        } catch (error) {
            console.error('Error starting collection scheduler:', error);
            this.showAlert('Error starting collection scheduler', 'danger');
        }
    }

    async stopCollectionScheduler(collectionId) {
        try {
            const response = await fetch(`/api/data-collection/collections/${collectionId}/scheduler/stop`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                }
            });
            
            const result = await response.json();
            if (result.success) {
                this.updateSchedulerStatus(collectionId, false);
                this.showAlert('Scheduler stopped successfully', 'success');
            } else {
                this.showAlert(`Error stopping scheduler: ${result.error}`, 'danger');
            }
        } catch (error) {
            console.error('Error stopping scheduler:', error);
            this.showAlert('Error stopping scheduler', 'danger');
        }
    }
    
    // Technical Indicators Methods
    async calculateCollectionIndicators(collectionId) {
        try {
            this.showAlert('Calculating technical indicators...', 'info');
            
            const response = await fetch(`/api/data-collection/collections/${collectionId}/indicators/calculate`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                }
            });
            
            const result = await response.json();
            if (result.success) {
                this.showAlert(`Technical indicators calculated successfully! ${result.calculated_count}/${result.total_symbols} symbols processed (${result.coverage} coverage)`, 'success');
                // Refresh the collections display to show updated indicator status
                this.loadCollections();
            } else {
                this.showAlert(`Error calculating indicators: ${result.error}`, 'danger');
            }
        } catch (error) {
            console.error('Error calculating indicators:', error);
            this.showAlert('Error calculating technical indicators', 'danger');
        }
    }
    
    async getCollectionIndicatorsStatus(collectionId) {
        try {
            const response = await fetch(`/api/data-collection/collections/${collectionId}/indicators/status`);
            const result = await response.json();
            
            if (result.success) {
                return result.status;
            } else {
                console.error('Error getting indicators status:', result.error);
                return null;
            }
        } catch (error) {
            console.error('Error getting indicators status:', error);
            return null;
        }
    }
    
    async loadCollectionIndicatorsStatus(collectionId) {
        const status = await this.getCollectionIndicatorsStatus(collectionId);
        if (status) {
            this.updateIndicatorsStatus(collectionId, status);
        }
    }
    
    updateIndicatorsStatus(collectionId, status) {
        const statusElement = document.getElementById(`indicators-status-${collectionId}`);
        if (statusElement) {
            if (status.indicators_available) {
                statusElement.innerHTML = `
                    <div class="indicators-info">
                        <span class="badge bg-success">✓ Indicators Available</span>
                        <small class="text-muted">${status.symbols_with_indicators}/${status.total_symbols} symbols (${status.indicators_coverage})</small>
                        <br><small class="text-muted">Last calculated: ${new Date(status.latest_calculation).toLocaleString()}</small>
                    </div>
                `;
            } else {
                statusElement.innerHTML = `
                    <div class="indicators-info">
                        <span class="badge bg-warning">⚠ No Indicators</span>
                        <small class="text-muted">Technical indicators not calculated yet</small>
                    </div>
                `;
            }
        }
    }

    async loadCollectionSchedulerStatus(collectionId) {
        try {
            const response = await fetch(`/api/data-collection/collections/${collectionId}/scheduler/status`);
            const data = await response.json();
            
            if (data.success) {
                const startBtn = document.getElementById(`start-${collectionId}`);
                const stopBtn = document.getElementById(`stop-${collectionId}`);
                const lastRunElement = document.getElementById(`last-run-${collectionId}`);
                const nextRunElement = document.getElementById(`next-run-${collectionId}`);
                const aiRankingElement = document.getElementById(`ai-ranking-last-update-${collectionId}`);
                
                // Update button visibility based on auto_update status
                if (startBtn && stopBtn) {
                    if (data.auto_update) {
                        startBtn.style.display = 'none';
                        stopBtn.style.display = 'inline-block';
                    } else {
                        startBtn.style.display = 'inline-block';
                        stopBtn.style.display = 'none';
                    }
                }

                // Update last run and next run times
                if (lastRunElement) {
                    lastRunElement.textContent = `Last: ${data.last_run ? new Date(data.last_run).toLocaleString() : 'Never'}`;
                }

                if (nextRunElement) {
                    nextRunElement.textContent = `Next: ${data.auto_update ? (data.next_run ? new Date(data.next_run).toLocaleString() : 'Calculating...') : 'Not scheduled'}`;
                }

                // Update AI ranking last update time
                if (aiRankingElement) {
                    const aiUpdateTime = data.ai_ranking_last_update_formatted || data.ai_ranking_last_update;
                    aiRankingElement.innerHTML = `<i class="fas fa-robot"></i> AI Ranking: ${aiUpdateTime ? new Date(aiUpdateTime).toLocaleString() : 'Never'}`;
                }
            }
        } catch (error) {
            console.error('Error loading collection scheduler status:', error);
        }
    }

    showAlert(message, type) {
        // Create alert element
        const alertDiv = document.createElement('div');
        alertDiv.className = `alert alert-${type} alert-dismissible fade show`;
        alertDiv.innerHTML = `
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        `;

        // Insert at the top of the main content
        const main = document.querySelector('main');
        main.insertBefore(alertDiv, main.firstChild);

        // Auto-dismiss after 5 seconds
        setTimeout(() => {
            if (alertDiv.parentNode) {
                alertDiv.remove();
            }
        }, 5000);
    }

    // Scheduler Functions
    async startScheduler(collectionId) {
        try {
            const response = await fetch(`/api/data-collection/collections/${collectionId}/scheduler/start`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                }
            });
            
            const data = await response.json();
            
            if (data.success) {
                this.showAlert(`Scheduler started for collection ${collectionId}`, 'success');
                // Update the UI to show running status
                this.updateSchedulerStatus(collectionId, true);
                // Refresh collections to get updated status
                await this.loadCollections();
            } else {
                this.showAlert(`Error starting scheduler: ${data.message}`, 'error');
            }
        } catch (error) {
            console.error('Error starting scheduler:', error);
            this.showAlert('Error starting scheduler', 'error');
        }
    }

    async stopScheduler(collectionId) {
        try {
            const response = await fetch(`/api/data-collection/collections/${collectionId}/scheduler/stop`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                }
            });
            
            const data = await response.json();
            
            if (data.success) {
                this.showAlert(`Scheduler stopped for collection ${collectionId}`, 'success');
                // Update the UI to show stopped status
                this.updateSchedulerStatus(collectionId, false);
                // Refresh collections to get updated status
                await this.loadCollections();
            } else {
                this.showAlert(`Error stopping scheduler: ${data.message}`, 'error');
            }
        } catch (error) {
            console.error('Error stopping scheduler:', error);
            this.showAlert('Error stopping scheduler', 'error');
        }
    }

    updateSchedulerStatus(collectionId, isRunning) {
        const startBtn = document.getElementById(`start-${collectionId}`);
        const stopBtn = document.getElementById(`stop-${collectionId}`);
        
        if (startBtn && stopBtn) {
            if (isRunning) {
                startBtn.style.display = 'none';
                stopBtn.style.display = 'inline-block';
            } else {
                startBtn.style.display = 'inline-block';
                stopBtn.style.display = 'none';
            }
        }
    }

    updateSchedulerStatusText(collectionId, isRunning) {
        const statusContainer = document.querySelector(`[data-collection-id="${collectionId}"] .scheduler-status`);
        if (statusContainer) {
            const now = new Date();
            const nextRun = isRunning ? new Date(now.getTime() + 60000).toLocaleTimeString() : 'Not scheduled';
            const lastRun = isRunning ? now.toLocaleTimeString() : 'Never';
            
            statusContainer.innerHTML = `
                <small class="text-muted">
                    <i class="fas fa-clock"></i> ${isRunning ? 'Running' : 'Stopped'}
                </small>
                <br>
                <small class="text-muted">
                    <i class="fas fa-sync"></i> Data: ${lastRun}
                </small>
                <br>
                <small class="text-info">
                    <i class="fas fa-robot"></i> AI Ranking: ${lastRun}
                </small>
            `;
        }
    }

    async openPerformanceAnalytics(collectionId) {
        try {
            // Get collection details
            const response = await fetch(`/api/data-collection/collections/${collectionId}`);
            const collection = await response.json();
            
            if (!collection.success) {
                this.showAlert('Error loading collection details', 'error');
                return;
            }

            // Create and show analytics modal
            this.showAnalyticsModal(collectionId, collection);

        } catch (error) {
            console.error('Error opening performance analytics:', error);
            this.showAlert('Error opening performance analytics', 'error');
        }
    }

    async openAIRanking(collectionId) {
        try {
            // Get collection details
            const response = await fetch(`/api/data-collection/collections/${collectionId}`);
            const collection = await response.json();
            
            if (!collection.success) {
                this.showAlert('Error loading collection details', 'error');
                return;
            }

            // Create and show AI ranking modal
            this.showAIRankingModal(collectionId, collection);

        } catch (error) {
            console.error('Error opening AI ranking:', error);
            this.showAlert('Error opening AI ranking', 'error');
        }
    }

    showAnalyticsModal(collectionId, collection) {
        // Create modal HTML
        const modalHtml = `
            <div class="modal fade" id="analyticsModal" tabindex="-1" aria-labelledby="analyticsModalLabel" aria-hidden="true">
                <div class="modal-dialog modal-xl">
                    <div class="modal-content">
                        <div class="modal-header">
                            <h5 class="modal-title" id="analyticsModalLabel">
                                <i class="fas fa-chart-bar"></i> Performance Analytics - ${collectionId}
                            </h5>
                            <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
                        </div>
                        <div class="modal-body">
                            <div class="row">
                                <!-- Advanced Performance Metrics -->
                                <div class="col-12 mb-4">
                                    <div class="card">
                                        <div class="card-header">
                                            <h5 class="card-title mb-0">
                                                <i class="fas fa-chart-line"></i> Advanced Performance Metrics
                                            </h5>
                                        </div>
                                        <div class="card-body">
                                            <div class="row">
                                                <div class="col-md-4 mb-3">
                                                    <div class="metric-card text-center p-3 border rounded">
                                                        <h6 class="text-muted">Sharpe Ratio</h6>
                                                        <div class="metric-value" id="modal-sharpe-ratio">-</div>
                                                        <small class="text-muted">Risk-adjusted return</small>
                                                    </div>
                                                </div>
                                                <div class="col-md-4 mb-3">
                                                    <div class="metric-card text-center p-3 border rounded">
                                                        <h6 class="text-muted">Sortino Ratio</h6>
                                                        <div class="metric-value" id="modal-sortino-ratio">-</div>
                                                        <small class="text-muted">Downside risk-adjusted</small>
                                                    </div>
                                                </div>
                                                <div class="col-md-4 mb-3">
                                                    <div class="metric-card text-center p-3 border rounded">
                                                        <h6 class="text-muted">Calmar Ratio</h6>
                                                        <div class="metric-value" id="modal-calmar-ratio">-</div>
                                                        <small class="text-muted">Return vs max drawdown</small>
                                                    </div>
                                                </div>
                                                <div class="col-md-4 mb-3">
                                                    <div class="metric-card text-center p-3 border rounded">
                                                        <h6 class="text-muted">Max Drawdown</h6>
                                                        <div class="metric-value" id="modal-max-drawdown">-</div>
                                                        <small class="text-muted">Largest peak-to-trough</small>
                                                    </div>
                                                </div>
                                                <div class="col-md-4 mb-3">
                                                    <div class="metric-card text-center p-3 border rounded">
                                                        <h6 class="text-muted">Volatility</h6>
                                                        <div class="metric-value" id="modal-volatility">-</div>
                                                        <small class="text-muted">Annualized std dev</small>
                                                    </div>
                                                </div>
                                                <div class="col-md-4 mb-3">
                                                    <div class="metric-card text-center p-3 border rounded">
                                                        <h6 class="text-muted">Beta</h6>
                                                        <div class="metric-value" id="modal-beta">-</div>
                                                        <small class="text-muted">Market correlation</small>
                                                    </div>
                                                </div>
                                            </div>
                                        </div>
                                    </div>
                                </div>

                                <!-- Risk Management -->
                                <div class="col-12 mb-4">
                                    <div class="card">
                                        <div class="card-header">
                                            <h5 class="card-title mb-0">
                                                <i class="fas fa-shield-alt"></i> Risk Management
                                            </h5>
                                        </div>
                                        <div class="card-body">
                                            <div class="row">
                                                <div class="col-md-6 mb-3">
                                                    <div class="metric-card text-center p-3 border rounded">
                                                        <h6 class="text-muted">Position Size</h6>
                                                        <div class="metric-value" id="modal-position-size">-</div>
                                                        <small class="text-muted">Current position sizing</small>
                                                    </div>
                                                </div>
                                                <div class="col-md-6 mb-3">
                                                    <div class="metric-card text-center p-3 border rounded">
                                                        <h6 class="text-muted">Stop Loss</h6>
                                                        <div class="metric-value" id="modal-stop-loss">-</div>
                                                        <small class="text-muted">Active stop-loss orders</small>
                                                    </div>
                                                </div>
                                                <div class="col-md-6 mb-3">
                                                    <div class="metric-card text-center p-3 border rounded">
                                                        <h6 class="text-muted">Portfolio Limits</h6>
                                                        <div class="metric-value" id="modal-portfolio-limits">-</div>
                                                        <small class="text-muted">Risk limit utilization</small>
                                                    </div>
                                                </div>
                                                <div class="col-md-6 mb-3">
                                                    <div class="metric-card text-center p-3 border rounded">
                                                        <h6 class="text-muted">Sector Exposure</h6>
                                                        <div class="metric-value" id="modal-sector-exposure">-</div>
                                                        <small class="text-muted">Sector concentration</small>
                                                    </div>
                                                </div>
                                            </div>
                                        </div>
                                    </div>
                                </div>

                                <!-- Active Positions -->
                                <div class="col-12 mb-4">
                                    <div class="card">
                                        <div class="card-header">
                                            <h5 class="card-title mb-0">
                                                <i class="fas fa-briefcase"></i> Active Positions
                                            </h5>
                                        </div>
                                        <div class="card-body">
                                            <div id="modal-active-positions">
                                                <div class="text-center">
                                                    <i class="fas fa-spinner fa-spin fa-2x text-muted"></i>
                                                    <p class="mt-2 text-muted">Loading positions...</p>
                                                </div>
                                            </div>
                                        </div>
                                    </div>
                                </div>

                                <!-- Performance Charts -->
                                <div class="col-12 mb-4">
                                    <div class="card">
                                        <div class="card-header">
                                            <h5 class="card-title mb-0">
                                                <i class="fas fa-chart-area"></i> Performance Charts
                                            </h5>
                                        </div>
                                        <div class="card-body">
                                            <div id="modal-performance-charts">
                                                <div class="text-center">
                                                    <i class="fas fa-spinner fa-spin fa-2x text-muted"></i>
                                                    <p class="mt-2 text-muted">Loading charts...</p>
                                                </div>
                                            </div>
                                        </div>
                                    </div>
                                </div>
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
        const existingModal = document.getElementById('analyticsModal');
        if (existingModal) {
            existingModal.remove();
        }

        // Add modal to body
        document.body.insertAdjacentHTML('beforeend', modalHtml);

        // Show modal
        const modal = new bootstrap.Modal(document.getElementById('analyticsModal'));
        modal.show();

        // Load analytics data
        this.loadPerformanceAnalyticsForCollection(collectionId, true);
    }

    showAIRankingModal(collectionId, collection) {
        // Create modal HTML with Syncfusion Grid and real-time updates
        const modalHtml = `
            <div class="modal fade" id="aiRankingModal" tabindex="-1" aria-labelledby="aiRankingModalLabel" aria-hidden="true">
                <div class="modal-dialog modal-fullscreen-lg-down modal-xl">
                    <div class="modal-content">
                        <div class="modal-header">
                            <h5 class="modal-title" id="aiRankingModalLabel">
                                <i class="fas fa-robot"></i> AI Stock Ranking - ${collectionId}
                                <span class="badge bg-info ms-2" id="update-status">Live Updates</span>
                            </h5>
                            <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
                        </div>
                        <div class="modal-body">
                            <div class="row">
                                <!-- Loading State -->
                                <div class="col-12 text-center" id="ai-ranking-loading">
                                    <div class="spinner-border text-primary" role="status">
                                        <span class="visually-hidden">Loading...</span>
                                    </div>
                                    <p class="mt-3">Analyzing stocks with AI...</p>
                                </div>

                                <!-- Ranking Results -->
                                <div class="col-12" id="ai-ranking-results" style="display: none;">
                                    <!-- Summary Statistics -->
                                    <div class="row mb-4">
                                        <div class="col-md-3">
                                            <div class="card text-center">
                                                <div class="card-body">
                                                    <h6 class="card-title">Total Stocks</h6>
                                                    <h4 id="total-stocks-count">-</h4>
                                                </div>
                                            </div>
                                        </div>
                                        <div class="col-md-3">
                                            <div class="card text-center">
                                                <div class="card-body">
                                                    <h6 class="card-title">Strong Buy</h6>
                                                    <h4 id="strong-buy-count" class="text-success">-</h4>
                                                </div>
                                            </div>
                                        </div>
                                        <div class="col-md-3">
                                            <div class="card text-center">
                                                <div class="card-body">
                                                    <h6 class="card-title">Hold</h6>
                                                    <h4 id="hold-count" class="text-warning">-</h4>
                                                </div>
                                            </div>
                                        </div>
                                        <div class="col-md-3">
                                            <div class="card text-center">
                                                <div class="card-body">
                                                    <h6 class="card-title">Avoid</h6>
                                                    <h4 id="avoid-count" class="text-danger">-</h4>
                                                </div>
                                            </div>
                                        </div>
                                    </div>

                                    <!-- Enhanced Stocks Table with Syncfusion Grid -->
                                    <div class="card mb-4">
                                        <div class="card-header d-flex justify-content-between align-items-center">
                                            <h5 class="card-title mb-0">
                                                <i class="fas fa-trophy"></i> All Ranked Stocks
                                            </h5>
                                            <div class="btn-group" role="group">
                                                <button type="button" class="btn btn-sm btn-outline-primary" onclick="refreshAIRanking('${collectionId}')">
                                                    <i class="fas fa-sync-alt"></i> Refresh
                                                </button>
                                                <button type="button" class="btn btn-sm btn-outline-success" onclick="exportAIRankingReport('${collectionId}')">
                                                    <i class="fas fa-download"></i> Export
                                                </button>
                                            </div>
                                        </div>
                                        <div class="card-body p-0">
                                            <div id="ai-ranking-grid" style="height: 500px; overflow: hidden;"></div>
                                        </div>
                                    </div>

                                    <!-- Market Analysis -->
                                    <div class="card mb-4">
                                        <div class="card-header">
                                            <h5 class="card-title mb-0">
                                                <i class="fas fa-chart-line"></i> Market Analysis
                                            </h5>
                                        </div>
                                        <div class="card-body">
                                            <div class="row">
                                                <div class="col-md-6">
                                                    <h6 class="text-primary">Market Regime</h6>
                                                    <p id="market-regime" class="text-muted">-</p>
                                                </div>
                                                <div class="col-md-6">
                                                    <h6 class="text-primary">Market Insight</h6>
                                                    <p id="market-insight" class="text-muted">-</p>
                                                </div>
                                            </div>
                                            <div class="row mt-3">
                                                <div class="col-12">
                                                    <h6 class="text-primary">Recommendations</h6>
                                                    <ul id="market-recommendations" class="list-unstyled">
                                                        <!-- Recommendations will be populated here -->
                                                    </ul>
                                                </div>
                                            </div>
                                        </div>
                                    </div>

                                    <!-- Educational Content -->
                                    <div class="card mb-4">
                                        <div class="card-header">
                                            <h5 class="card-title mb-0">
                                                <i class="fas fa-graduation-cap"></i> Learning Insights
                                            </h5>
                                        </div>
                                        <div class="card-body">
                                            <div class="row">
                                                <div class="col-md-6">
                                                    <h6 class="text-success">Key Insights</h6>
                                                    <ul id="educational-insights" class="list-unstyled">
                                                        <!-- Insights will be populated here -->
                                                    </ul>
                                                </div>
                                                <div class="col-md-6">
                                                    <h6 class="text-info">Learning Recommendations</h6>
                                                    <ul id="learning-recommendations" class="list-unstyled">
                                                        <!-- Learning recommendations will be populated here -->
                                                    </ul>
                                                </div>
                                            </div>
                                        </div>
                                    </div>
                                </div>
                            </div>
                        </div>
                        <div class="modal-footer">
                            <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Close</button>
                            <button type="button" class="btn btn-primary" onclick="exportAIRankingReport('${collectionId}')">
                                <i class="fas fa-download"></i> Export Report
                            </button>
                        </div>
                    </div>
                </div>
            </div>
        `;

        // Remove existing modal if any
        const existingModal = document.getElementById('aiRankingModal');
        if (existingModal) {
            existingModal.remove();
        }

        // Add modal to body
        document.body.insertAdjacentHTML('beforeend', modalHtml);

        // Show modal
        const modal = new bootstrap.Modal(document.getElementById('aiRankingModal'));
        modal.show();

        // Load AI ranking data
        this.loadAIRankingData(collectionId);
    }

    async loadAIRankingData(collectionId) {
        try {
            // Fetch AI ranking data for all stocks
            const response = await fetch(`/api/ai-ranking/collection/${collectionId}/rank?max_stocks=1000`);
            const data = await response.json();
            
            if (data.success) {
                this.displayAIRankingResults(data);
                // Set up real-time updates
                this.setupRealTimeUpdates(collectionId);
            } else {
                this.showAlert('Error loading AI ranking data', 'error');
            }
        } catch (error) {
            console.error('Error loading AI ranking data:', error);
            this.showAlert('Error loading AI ranking data', 'error');
        }
    }

    setupRealTimeUpdates(collectionId) {
        // Check for scheduler status every 30 seconds
        this.updateInterval = setInterval(async () => {
            try {
                const response = await fetch(`/api/data-collection/collections/${collectionId}/scheduler/status`);
                const status = await response.json();
                
                if (status.is_running) {
                    // Update the status badge
                    const statusBadge = document.getElementById('update-status');
                    if (statusBadge) {
                        statusBadge.textContent = `Updated: ${status.last_run_formatted}`;
                        statusBadge.className = 'badge bg-success ms-2';
                    }
                    
                    // Refresh data if there was a recent update
                    const lastUpdate = new Date(status.last_run);
                    const now = new Date();
                    const timeDiff = (now - lastUpdate) / 1000; // seconds
                    
                    if (timeDiff < 120) { // If updated within 2 minutes
                        this.refreshAIRankingData(collectionId);
                    }
                }
            } catch (error) {
                console.error('Error checking real-time updates:', error);
            }
        }, 30000); // Check every 30 seconds
    }

    async refreshAIRankingData(collectionId) {
        try {
            const response = await fetch(`/api/ai-ranking/collection/${collectionId}/rank?max_stocks=1000`);
            const data = await response.json();
            
            if (data.success) {
                this.updateAIRankingGrid(data.top_stocks);
            }
        } catch (error) {
            console.error('Error refreshing AI ranking data:', error);
        }
    }

    displayAIRankingResults(data) {
        // Hide loading, show results
        document.getElementById('ai-ranking-loading').style.display = 'none';
        document.getElementById('ai-ranking-results').style.display = 'block';

        // Update summary statistics
        const summary = data.ranking_summary;
        if (summary) {
            document.getElementById('total-stocks-count').textContent = data.total_stocks || 0;
            document.getElementById('strong-buy-count').textContent = summary.recommendation_summary?.strong_buy || 0;
            document.getElementById('hold-count').textContent = summary.recommendation_summary?.hold || 0;
            document.getElementById('avoid-count').textContent = summary.recommendation_summary?.avoid || 0;
        }

        // Initialize Syncfusion Grid with all stocks
        const allStocks = data.top_stocks || [];
        console.log('Total stocks to display:', allStocks.length);
        console.log('First 5 stocks:', allStocks.slice(0, 5));
        this.initializeAIRankingGrid(allStocks);

        // Update market analysis
        this.updateMarketAnalysis(data.market_analysis || {});

        // Update educational content
        this.updateEducationalContent(data.educational_content || {});
    }

    initializeAIRankingGrid(stocks) {
        console.log('Initializing AI Ranking Grid with', stocks.length, 'stocks');
        
        // Check if Syncfusion Grid is available
        if (typeof ej !== 'undefined' && ej.grids) {
            try {
                this.createSyncfusionGrid(stocks);
            } catch (error) {
                console.error('Error creating Syncfusion Grid:', error);
                console.log('Falling back to regular table');
                this.createFallbackTable(stocks);
            }
        } else {
            // Fallback to regular table
            console.log('Syncfusion Grid not available, using fallback table');
            this.createFallbackTable(stocks);
        }
    }

    createSyncfusionGrid(stocks) {
        const gridElement = document.getElementById('ai-ranking-grid');
        if (!gridElement) return;

        console.log('Creating Syncfusion Grid with', stocks.length, 'stocks');
        console.log('Sample stock data:', stocks[0]);

        // Clear existing content
        gridElement.innerHTML = '';

        // Prepare data for grid
        const gridData = stocks.map(stock => ({
            rank: stock.rank,
            symbol: stock.symbol,
            totalScore: stock.total_score,
            technicalScore: stock.technical_score,
            riskScore: stock.risk_score,
            explanation: stock.explanation,
            recommendation: this.getRecommendation(stock.total_score)
        }));

        console.log('Grid data prepared:', gridData.length, 'items');
        console.log('Sample grid data:', gridData[0]);

        // Create Syncfusion Grid with enhanced features
        const grid = new ej.grids.Grid({
            dataSource: gridData,
            allowPaging: true,
            allowSorting: true,
            allowFiltering: true,
            allowGrouping: true,
            allowResizing: true,
            allowReordering: true,
            allowSelection: true,
            enableHover: true,
            enableVirtualization: false, // Disable virtualization to show all items
            pageSettings: { 
                pageSize: 112, 
                pageSizes: [20, 50, 100, 112, 200],
                currentPage: 1
            },
            // Force show all items on first page
            beforeDataBound: () => {
                console.log('Before data bound. Setting page size to show all items.');
                grid.pageSettings.pageSize = gridData.length;
            },
            dataBound: () => {
                console.log('Grid data bound. Total records:', grid.getCurrentViewRecords().length);
                console.log('Page size:', grid.pageSettings.pageSize);
                console.log('Current page:', grid.pageSettings.currentPage);
            },
            filterSettings: { type: 'Menu' },
            sortSettings: { 
                columns: [{ field: 'rank', direction: 'Ascending' }],
                allowMultiSort: true
            },
            height: '100%',
            width: '100%',
            columns: [
                { 
                    field: 'rank', 
                    headerText: 'Rank', 
                    width: 80, 
                    textAlign: 'Center',
                    type: 'number',
                    allowSorting: true,
                    sortComparer: (x, y) => x - y
                },
                { 
                    field: 'symbol', 
                    headerText: 'Symbol', 
                    width: 100,
                    allowSorting: true,
                    template: (data) => `<strong class="text-primary">${data.symbol}</strong>`
                },
                { 
                    field: 'totalScore', 
                    headerText: 'Total Score', 
                    width: 150,
                    allowSorting: true,
                    template: (data) => {
                        const score = data.totalScore;
                        const colorClass = this.getScoreColorClass(score);
                        return `<div class="d-flex align-items-center">
                                    <div class="progress flex-grow-1 me-2" style="height: 20px;">
                                        <div class="progress-bar ${colorClass}" style="width: ${score}%">
                                            ${score.toFixed(1)}
                                        </div>
                                    </div>
                                    <small class="text-muted">${score.toFixed(1)}</small>
                                </div>`;
                    },
                    sortComparer: (x, y) => x - y
                },
                { 
                    field: 'technicalScore', 
                    headerText: 'Technical', 
                    width: 120, 
                    format: 'N1',
                    allowSorting: true,
                    template: (data) => `<span class="badge bg-info">${data.technicalScore.toFixed(1)}</span>`,
                    sortComparer: (x, y) => x - y
                },
                { 
                    field: 'riskScore', 
                    headerText: 'Risk', 
                    width: 120, 
                    format: 'N1',
                    allowSorting: true,
                    template: (data) => `<span class="badge bg-warning">${data.riskScore.toFixed(1)}</span>`,
                    sortComparer: (x, y) => x - y
                },
                { 
                    field: 'recommendation', 
                    headerText: 'Recommendation', 
                    width: 140,
                    allowSorting: true,
                    template: (data) => {
                        const badgeClass = this.getRecommendationBadgeClass(data.totalScore);
                        return `<span class="badge ${badgeClass}">${data.recommendation}</span>`;
                    }
                },
                { 
                    field: 'explanation', 
                    headerText: 'Explanation', 
                    width: 250,
                    allowSorting: true,
                    template: (data) => `<small class="text-muted" style="white-space: normal;">${data.explanation}</small>`
                },
                {
                    field: 'actions',
                    headerText: 'Actions',
                    width: 100,
                    allowSorting: false,
                    template: (data) => `<button class="btn btn-sm btn-outline-primary" onclick="viewStockAnalysis('${data.symbol}')">
                                            <i class="fas fa-chart-line"></i> View
                                        </button>`
                }
            ],
            toolbar: ['Search', 'Print', 'ExcelExport', 'PdfExport'],
            searchSettings: { fields: ['symbol', 'explanation', 'recommendation'] },
            excelExportComplete: () => {
                console.log('Excel export completed');
            },
            rowSelected: (args) => {
                console.log('Row selected:', args.data);
            },
            dataBound: () => {
                console.log('Grid data bound');
            }
        });

        grid.appendTo(gridElement);
        this.aiRankingGrid = grid;
        
        // Add custom CSS to enhance sorting arrows visibility
        const style = document.createElement('style');
        style.textContent = `
            .e-grid .e-headercell .e-sortfilter {
                opacity: 1 !important;
                visibility: visible !important;
            }
            .e-grid .e-headercell .e-sortfilter .e-sortasc,
            .e-grid .e-headercell .e-sortfilter .e-sortdesc {
                color: #007bff !important;
                font-weight: bold !important;
            }
            .e-grid .e-headercell:hover .e-sortfilter {
                opacity: 1 !important;
            }
        `;
        document.head.appendChild(style);
    }

    createFallbackTable(stocks) {
        const gridElement = document.getElementById('ai-ranking-grid');
        if (!gridElement) return;

        console.log('Creating fallback table with', stocks.length, 'stocks');

        // Create a responsive table as fallback
        const tableHtml = `
            <div class="table-responsive">
                <div class="alert alert-info">
                    <strong>Showing ${stocks.length} stocks</strong> - Using fallback table view
                </div>
                <table class="table table-hover table-striped">
                    <thead>
                        <tr>
                            <th style="cursor: pointer;" onclick="sortTable(0)">
                                Rank <i class="fas fa-sort"></i>
                            </th>
                            <th style="cursor: pointer;" onclick="sortTable(1)">
                                Symbol <i class="fas fa-sort"></i>
                            </th>
                            <th style="cursor: pointer;" onclick="sortTable(2)">
                                Total Score <i class="fas fa-sort"></i>
                            </th>
                            <th style="cursor: pointer;" onclick="sortTable(3)">
                                Technical <i class="fas fa-sort"></i>
                            </th>
                            <th style="cursor: pointer;" onclick="sortTable(4)">
                                Risk <i class="fas fa-sort"></i>
                            </th>
                            <th style="cursor: pointer;" onclick="sortTable(5)">
                                Recommendation <i class="fas fa-sort"></i>
                            </th>
                            <th style="cursor: pointer;" onclick="sortTable(6)">
                                Explanation <i class="fas fa-sort"></i>
                            </th>
                            <th>Actions</th>
                        </tr>
                    </thead>
                    <tbody>
                        ${stocks.map(stock => `
                            <tr>
                                <td><span class="badge bg-primary">${stock.rank}</span></td>
                                <td><strong>${stock.symbol}</strong></td>
                                <td>
                                    <div class="progress" style="height: 20px;">
                                        <div class="progress-bar ${this.getScoreColorClass(stock.total_score)}" 
                                             style="width: ${stock.total_score}%">
                                            ${stock.total_score.toFixed(1)}
                                        </div>
                                    </div>
                                </td>
                                <td>${stock.technical_score.toFixed(1)}</td>
                                <td>${stock.risk_score.toFixed(1)}</td>
                                <td><span class="badge ${this.getRecommendationBadgeClass(stock.total_score)}">${this.getRecommendation(stock.total_score)}</span></td>
                                <td><small class="text-muted">${stock.explanation}</small></td>
                                <td>
                                    <button class="btn btn-sm btn-outline-primary" onclick="viewStockAnalysis('${stock.symbol}')">
                                        <i class="fas fa-chart-line"></i> View
                                    </button>
                                </td>
                            </tr>
                        `).join('')}
                    </tbody>
                </table>
            </div>
        `;

        gridElement.innerHTML = tableHtml;
        
        // Add sorting functionality for fallback table
        window.sortTable = function(columnIndex) {
            const table = gridElement.querySelector('table');
            const tbody = table.querySelector('tbody');
            const rows = Array.from(tbody.querySelectorAll('tr'));
            
            // Toggle sort direction
            const currentDirection = table.getAttribute('data-sort-direction') || 'asc';
            const newDirection = currentDirection === 'asc' ? 'desc' : 'asc';
            table.setAttribute('data-sort-direction', newDirection);
            
            // Update sort icons
            const headers = table.querySelectorAll('th');
            headers.forEach((header, index) => {
                const icon = header.querySelector('i');
                if (icon && index < headers.length - 1) { // Skip Actions column
                    if (index === columnIndex) {
                        icon.className = newDirection === 'asc' ? 'fas fa-sort-up' : 'fas fa-sort-down';
                    } else {
                        icon.className = 'fas fa-sort';
                    }
                }
            });
            
            // Sort rows
            rows.sort((a, b) => {
                const aValue = a.cells[columnIndex].textContent.trim();
                const bValue = b.cells[columnIndex].textContent.trim();
                
                let aNum = parseFloat(aValue);
                let bNum = parseFloat(bValue);
                
                if (!isNaN(aNum) && !isNaN(bNum)) {
                    return newDirection === 'asc' ? aNum - bNum : bNum - aNum;
                } else {
                    return newDirection === 'asc' ? 
                        aValue.localeCompare(bValue) : 
                        bValue.localeCompare(aValue);
                }
            });
            
            // Reorder rows
            rows.forEach(row => tbody.appendChild(row));
        };
    }

    updateAIRankingGrid(stocks) {
        if (this.aiRankingGrid) {
            // Update Syncfusion Grid data
            const gridData = stocks.map(stock => ({
                rank: stock.rank,
                symbol: stock.symbol,
                totalScore: stock.total_score,
                technicalScore: stock.technical_score,
                riskScore: stock.risk_score,
                explanation: stock.explanation,
                recommendation: this.getRecommendation(stock.total_score)
            }));
            this.aiRankingGrid.dataSource = gridData;
            this.aiRankingGrid.refresh();
        } else {
            // Update fallback table
            this.createFallbackTable(stocks);
        }
    }

    getRecommendation(score) {
        if (score >= 80) return 'Strong Buy';
        if (score >= 60) return 'Buy';
        if (score >= 40) return 'Hold';
        if (score >= 20) return 'Sell';
        return 'Strong Sell';
    }

    getRecommendationBadgeClass(score) {
        if (score >= 80) return 'bg-success';
        if (score >= 60) return 'bg-primary';
        if (score >= 40) return 'bg-warning';
        if (score >= 20) return 'bg-danger';
        return 'bg-secondary';
    }

    populateTopStocksTable(stocks) {
        const tbody = document.getElementById('top-stocks-tbody');
        tbody.innerHTML = '';

        stocks.forEach(stock => {
            const row = document.createElement('tr');
            row.innerHTML = `
                <td><span class="badge bg-primary">${stock.rank}</span></td>
                <td><strong>${stock.symbol}</strong></td>
                <td>
                    <div class="progress" style="height: 20px;">
                        <div class="progress-bar ${this.getScoreColorClass(stock.total_score)}" 
                             style="width: ${stock.total_score}%">
                            ${stock.total_score.toFixed(1)}
                        </div>
                    </div>
                </td>
                <td>${stock.technical_score.toFixed(1)}</td>
                <td>${stock.risk_score.toFixed(1)}</td>
                <td>
                    <small class="text-muted">${stock.explanation}</small>
                </td>
                <td>
                    <button class="btn btn-sm btn-outline-primary" onclick="viewStockAnalysis('${stock.symbol}')">
                        <i class="fas fa-chart-line"></i> View
                    </button>
                </td>
            `;
            tbody.appendChild(row);
        });
    }

    updateMarketAnalysis(marketAnalysis) {
        document.getElementById('market-regime').textContent = marketAnalysis.market_regime || 'Unknown';
        document.getElementById('market-insight').textContent = marketAnalysis.market_insight || 'Analysis unavailable';

        const recommendationsList = document.getElementById('market-recommendations');
        recommendationsList.innerHTML = '';
        
        if (marketAnalysis.recommendations) {
            marketAnalysis.recommendations.forEach(rec => {
                const li = document.createElement('li');
                li.textContent = rec;
                recommendationsList.appendChild(li);
            });
        }
    }

    updateEducationalContent(educationalContent) {
        const insightsList = document.getElementById('educational-insights');
        const learningList = document.getElementById('learning-recommendations');
        
        insightsList.innerHTML = '';
        learningList.innerHTML = '';
        
        if (educationalContent.insights) {
            educationalContent.insights.forEach(insight => {
                const li = document.createElement('li');
                li.textContent = insight;
                insightsList.appendChild(li);
            });
        }
        
        if (educationalContent.learning_recommendations) {
            educationalContent.learning_recommendations.forEach(rec => {
                const li = document.createElement('li');
                li.textContent = rec;
                learningList.appendChild(li);
            });
        }
    }

    getScoreColorClass(score) {
        if (score >= 70) return 'bg-success';
        if (score >= 50) return 'bg-warning';
        return 'bg-danger';
    }

    async loadPerformanceAnalyticsForCollection(collectionId, isModal = false) {
        try {
            // Show loading state
            this.showAnalyticsLoading(isModal);

            // Load advanced metrics
            await this.loadAdvancedMetrics(collectionId, isModal);

            // Load risk management data
            await this.loadRiskManagementData(collectionId, isModal);

            // Load active positions
            await this.loadActivePositions(collectionId, isModal);

            // Load performance charts
            await this.loadPerformanceCharts(collectionId, isModal);

        } catch (error) {
            console.error('Error loading performance analytics:', error);
            this.showAlert('Error loading performance analytics', 'error');
        }
    }

    showAnalyticsLoading(isModal = false) {
        const prefix = isModal ? 'modal-' : '';
        
        // Show loading indicators for all metric cards
        const metricIds = ['sharpe-ratio', 'sortino-ratio', 'calmar-ratio', 'max-drawdown', 'volatility', 'beta'];
        metricIds.forEach(id => {
            const element = document.getElementById(prefix + id);
            if (element) {
                element.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Loading...';
            }
        });

        const riskIds = ['position-size', 'stop-loss', 'portfolio-limits', 'sector-exposure'];
        riskIds.forEach(id => {
            const element = document.getElementById(prefix + id);
            if (element) {
                element.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Loading...';
            }
        });
    }

    async loadAdvancedMetrics(collectionId, isModal = false) {
        try {
            const response = await fetch(`/api/performance/collection/${collectionId}/metrics`);
            const data = await response.json();
            
            if (data.success) {
                const prefix = isModal ? 'modal-' : '';
                // Update metric displays
                this.updateMetricDisplay(prefix + 'sharpe-ratio', data.metrics.sharpe_ratio);
                this.updateMetricDisplay(prefix + 'sortino-ratio', data.metrics.sortino_ratio);
                this.updateMetricDisplay(prefix + 'calmar-ratio', data.metrics.calmar_ratio);
                this.updateMetricDisplay(prefix + 'max-drawdown', data.metrics.max_drawdown);
                this.updateMetricDisplay(prefix + 'volatility', data.metrics.volatility);
                this.updateMetricDisplay(prefix + 'beta', data.metrics.beta);
            } else {
                this.showAlert('Error loading advanced metrics', 'error');
            }
        } catch (error) {
            console.error('Error loading advanced metrics:', error);
            this.showAlert('Error loading advanced metrics', 'error');
        }
    }

    async loadRiskManagementData(collectionId, isModal = false) {
        try {
            const response = await fetch(`/api/performance/collection/${collectionId}/risk`);
            const data = await response.json();
            
            if (data.success) {
                const prefix = isModal ? 'modal-' : '';
                // Update risk management displays
                this.updateMetricDisplay(prefix + 'position-size', data.risk.position_size);
                this.updateMetricDisplay(prefix + 'stop-loss', data.risk.stop_loss);
                this.updateMetricDisplay(prefix + 'portfolio-limits', data.risk.portfolio_limits);
                this.updateMetricDisplay(prefix + 'sector-exposure', data.risk.sector_exposure);
            } else {
                this.showAlert('Error loading risk management data', 'error');
            }
        } catch (error) {
            console.error('Error loading risk management data:', error);
            this.showAlert('Error loading risk management data', 'error');
        }
    }

    async loadActivePositions(collectionId, isModal = false) {
        try {
            const response = await fetch(`/api/performance/collection/${collectionId}/positions`);
            const data = await response.json();
            
            if (data.success) {
                this.displayActivePositions(data.positions, isModal);
            } else {
                this.showAlert('Error loading active positions', 'error');
            }
        } catch (error) {
            console.error('Error loading active positions:', error);
            this.showAlert('Error loading active positions', 'error');
        }
    }

    async loadPerformanceCharts(collectionId, isModal = false) {
        try {
            const response = await fetch(`/api/performance/collection/${collectionId}/charts`);
            const data = await response.json();
            
            if (data.success) {
                this.displayPerformanceCharts(data.charts, isModal);
            } else {
                this.showAlert('Error loading performance charts', 'error');
            }
        } catch (error) {
            console.error('Error loading performance charts:', error);
            this.showAlert('Error loading performance charts', 'error');
        }
    }

    updateMetricDisplay(elementId, value) {
        const element = document.getElementById(elementId);
        if (element) {
            if (value !== null && value !== undefined) {
                element.textContent = typeof value === 'number' ? value.toFixed(4) : value;
            } else {
                element.textContent = 'N/A';
            }
        }
    }

    displayActivePositions(positions, isModal = false) {
        const containerId = isModal ? 'modal-active-positions' : 'active-positions';
        const container = document.getElementById(containerId);
        if (!container) return;

        if (!positions || positions.length === 0) {
            container.innerHTML = '<p class="text-muted">No active positions</p>';
            return;
        }

        let html = '<div class="table-responsive"><table class="table table-sm">';
        html += '<thead><tr><th>Symbol</th><th>Position</th><th>Entry Price</th><th>Current Price</th><th>P&L</th></tr></thead><tbody>';
        
        positions.forEach(position => {
            const pnlClass = position.pnl >= 0 ? 'text-success' : 'text-danger';
            html += `
                <tr>
                    <td>${position.symbol}</td>
                    <td>${position.quantity}</td>
                    <td>$${position.entry_price.toFixed(2)}</td>
                    <td>$${position.current_price.toFixed(2)}</td>
                    <td class="${pnlClass}">$${position.pnl.toFixed(2)}</td>
                </tr>
            `;
        });
        
        html += '</tbody></table></div>';
        container.innerHTML = html;
    }

    displayPerformanceCharts(charts, isModal = false) {
        // This would integrate with your charting library
        // For now, we'll just show a placeholder
        const containerId = isModal ? 'modal-performance-charts' : 'performance-charts';
        const container = document.getElementById(containerId);
        if (container) {
            container.innerHTML = '<p class="text-muted">Performance charts will be displayed here</p>';
        }
    }
}

// Make functions globally available
window.startScheduler = (collectionId) => window.dataCollectionManager.startScheduler(collectionId);
window.stopScheduler = (collectionId) => window.dataCollectionManager.stopScheduler(collectionId);
window.calculateCollectionIndicators = (collectionId) => window.dataCollectionManager.calculateCollectionIndicators(collectionId);

// AI Ranking functions
window.exportAIRankingReport = async function(collectionId) {
    try {
        const response = await fetch(`/api/ai-ranking/collection/${collectionId}/export?format=json`);
        const data = await response.json();
        
        if (data.success) {
            // Create and download the file
            const blob = new Blob([JSON.stringify(data.data, null, 2)], { type: 'application/json' });
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `ai-ranking-${collectionId}-${new Date().toISOString().split('T')[0]}.json`;
            document.body.appendChild(a);
            a.click();
            window.URL.revokeObjectURL(url);
            document.body.removeChild(a);
        } else {
            alert('Error exporting report');
        }
    } catch (error) {
        console.error('Error exporting AI ranking report:', error);
        alert('Error exporting report');
    }
};

window.viewStockAnalysis = function(symbol) {
    // Navigate to stock analysis page
    const collectionId = window.currentCollectionId || 'ALL_20250803_160817';
    const url = `/stock-analysis?symbol=${symbol}&collection=${collectionId}`;
    window.open(url, '_blank');
};

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    window.dataCollectionManager = new DataCollectionManager();
}); 