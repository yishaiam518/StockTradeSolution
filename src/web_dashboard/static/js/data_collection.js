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

class DataCollectionManager {
    constructor() {
        this.initializeEventListeners();
        this.loadExchanges();
        this.loadCollections();
    }

    initializeEventListeners() {
        // Form submission
        document.getElementById('dataCollectionForm').addEventListener('submit', (e) => {
            e.preventDefault();
            this.startDataCollection();
        });

        // Time period change
        document.getElementById('timePeriod').addEventListener('change', (e) => {
            const customRange = document.getElementById('customDateRange');
            if (e.target.value === 'custom') {
                customRange.style.display = 'block';
            } else {
                customRange.style.display = 'none';
            }
        });

        // Delete confirmation
        document.getElementById('confirmDelete').addEventListener('click', () => {
            this.deleteConfirmedCollection();
        });

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
        const container = document.getElementById('collectionsList');
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
                                            <span id="last-run-${collection.collection_id}">Last: ${collection.last_run ? new Date(collection.last_run).toLocaleString() : 'Never'}</span> | 
                                            <span id="next-run-${collection.collection_id}">Next: ${collection.auto_update ? (collection.next_run ? new Date(collection.next_run).toLocaleString() : 'Not scheduled') : 'Not scheduled'}</span>
                                        </div>

                                        <div class="small text-muted">
                                            <span class="text-success">✓ ${collection.successful_symbols || 0} successful</span> | 
                                            <span class="text-danger">✗ ${collection.failed_count || 0} failed</span>
                                        </div>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            `;
            
            row.appendChild(card);
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
        const form = document.getElementById('dataCollectionForm');
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
            
            const data = await response.json();
            
            if (data.success) {
                this.showAlert(`Scheduler stopped for collection ${collectionId}`, 'success');
                document.getElementById(`start-${collectionId}`).style.display = 'inline-block';
                document.getElementById(`stop-scheduler-${collectionId}`).style.display = 'none';
                document.getElementById(`status-${collectionId}`).textContent = 'Stopped';
            } else {
                this.showAlert('Error stopping scheduler: ' + data.error, 'danger');
            }
        } catch (error) {
            console.error('Error stopping collection scheduler:', error);
            this.showAlert('Error stopping collection scheduler', 'danger');
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
            
            statusContainer.innerHTML = `Last: ${lastRun} | Next: ${nextRun}`;
        }
    }
}

// Make functions globally available
window.startScheduler = (collectionId) => window.dataCollectionManager.startScheduler(collectionId);
window.stopScheduler = (collectionId) => window.dataCollectionManager.stopScheduler(collectionId);

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    window.dataCollectionManager = new DataCollectionManager();
}); 