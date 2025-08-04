// Data Collection JavaScript
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
            this.handleTimePeriodChange(e.target.value);
        });

        // Delete confirmation
        document.getElementById('confirmDelete').addEventListener('click', () => {
            this.deleteCollection();
        });
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
            const response = await fetch('/api/data-collection/collections');
            const data = await response.json();
            
            if (data.success) {
                this.displayCollections(data.collections);
            } else {
                this.showAlert('Error loading collections', 'danger');
            }
        } catch (error) {
            console.error('Error loading collections:', error);
            this.showAlert('Error loading collections', 'danger');
        }
    }

    displayCollections(collections) {
        const container = document.getElementById('collectionsList');
        
        if (collections.length === 0) {
            container.innerHTML = `
                <div class="text-center">
                    <i class="fas fa-database fa-3x text-muted"></i>
                    <p class="mt-3 text-muted">No data collections found</p>
                    <p class="text-muted">Start by creating a new data collection above</p>
                </div>
            `;
            return;
        }

        const html = collections.map(collection => `
            <div class="card collection-card mb-3">
                <div class="card-body">
                    <div class="row align-items-center">
                        <div class="col-md-8">
                            <h6 class="card-title">
                                <i class="fas fa-building text-primary"></i> ${collection.exchange}
                            </h6>
                            <p class="card-text text-muted mb-1">
                                <i class="fas fa-calendar"></i> ${collection.start_date} to ${collection.end_date}
                            </p>
                            <p class="card-text text-muted mb-1">
                                <i class="fas fa-chart-bar"></i> ${collection.successful_symbols} symbols collected
                            </p>
                            <p class="card-text text-muted mb-0">
                                <i class="fas fa-clock"></i> Collected on ${new Date(collection.collection_date).toLocaleString()}
                            </p>
                        </div>
                        <div class="col-md-4 text-end">
                            <span class="badge bg-success status-badge">
                                <i class="fas fa-check"></i> Completed
                            </span>
                            <div class="mt-2">
                                <button class="btn btn-sm btn-outline-primary" onclick="dataCollectionManager.viewCollection('${collection.collection_id}')">
                                    <i class="fas fa-eye"></i> View
                                </button>
                                <button class="btn btn-sm btn-outline-danger" onclick="dataCollectionManager.confirmDelete('${collection.collection_id}')">
                                    <i class="fas fa-trash"></i> Delete
                                </button>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        `).join('');

        container.innerHTML = html;
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
                this.showAlert(`Error: ${result.error}`, 'danger');
            }
        } catch (error) {
            console.error('Error deleting collection:', error);
            this.showAlert('Error deleting collection', 'danger');
        }

        // Close modal
        const modal = bootstrap.Modal.getInstance(document.getElementById('deleteModal'));
        modal.hide();
        this.collectionToDelete = null;
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
}

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.dataCollectionManager = new DataCollectionManager();
}); 