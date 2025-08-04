// Stock Viewer JavaScript
class StockViewer {
    constructor() {
        console.log('StockViewer constructor called - v999999 - CACHE BUSTED!');
        this.currentSymbol = null;
        this.currentChartType = 'line';
        this.currentTimeframe = '1Y';
        this.collectionId = null;
        this.exchange = null;
        this.startDate = null;
        this.endDate = null;
        this.stockList = [];
        
        console.log('StockViewer created:', this);
    }

    initialize() {
        console.log('StockViewer initializing...');
        console.log('Window location:', window.location.href);
        
        // Get URL parameters
        const urlParams = new URLSearchParams(window.location.search);
        this.collectionId = urlParams.get('collection_id');
        this.exchange = urlParams.get('exchange');
        this.startDate = urlParams.get('start_date');
        this.endDate = urlParams.get('end_date');
        
        console.log('URL Parameters:', {
            collectionId: this.collectionId,
            exchange: this.exchange,
            startDate: this.startDate,
            endDate: this.endDate
        });
        
        if (!this.collectionId) {
            console.error('No collection_id found in URL parameters!');
            return;
        }
        
        // Initialize event listeners first
        this.initializeEventListeners();
        
        // Load collection details
        this.loadCollectionDetails();
        
        // Load stock list
        this.loadStockList();
        
        console.log('StockViewer initialization complete');
    }

    initializeEventListeners() {
        console.log('Initializing event listeners...');
        
        // Add event listener for search input
        const searchInput = document.getElementById('stockSearch');
        console.log('Search input element:', searchInput);
        if (searchInput) {
            searchInput.addEventListener('input', () => this.filterStocks());
            console.log('Search input event listener added');
        } else {
            console.error('Search input element not found!');
        }
        
        // Add event listener for dropdown button
        const dropdownButton = document.getElementById('dropdownButton');
        console.log('Dropdown button element:', dropdownButton);
        if (dropdownButton) {
            dropdownButton.addEventListener('click', () => this.toggleDropdown());
            console.log('Dropdown button event listener added');
        } else {
            console.error('Dropdown button element not found!');
        }
        
        // Add event listeners for chart type buttons
        const chartTypeButtons = document.querySelectorAll('[data-chart-type]');
        chartTypeButtons.forEach(button => {
            button.addEventListener('click', () => {
                const chartType = button.getAttribute('data-chart-type');
                this.changeChartType(chartType);
            });
        });
        
        // Add event listeners for timeframe buttons
        const timeframeButtons = document.querySelectorAll('[data-timeframe]');
        timeframeButtons.forEach(button => {
            button.addEventListener('click', () => {
                const timeframe = button.getAttribute('data-timeframe');
                this.changeTimeframe(timeframe);
            });
        });
        
        // Add event listener for refresh button
        const refreshButton = document.getElementById('refreshButton');
        if (refreshButton) {
            refreshButton.addEventListener('click', () => this.refreshData());
        }
        
        // Add event listener for delete collection button
        const deleteButton = document.getElementById('deleteCollectionBtn');
        if (deleteButton) {
            deleteButton.addEventListener('click', () => this.deleteCollection());
        }
        
        // Add event listener for close button
        const closeButton = document.getElementById('closeButton');
        if (closeButton) {
            closeButton.addEventListener('click', () => window.close());
        }
        
        // Add event listener for export button
        const exportButton = document.getElementById('exportButton');
        if (exportButton) {
            exportButton.addEventListener('click', () => this.exportChart());
        }
        
        // Add event listener for refresh data button
        const refreshDataButton = document.getElementById('refreshDataButton');
        if (refreshDataButton) {
            refreshDataButton.addEventListener('click', () => this.refreshData());
        }
    }

    initializeSyncfusion() {
        // Try to initialize Syncfusion license
        if (typeof ej !== 'undefined' && ej.base && ej.base.setLicenseKey) {
            try {
                ej.base.setLicenseKey('Ngo9BigBOggjHTQxAR8/V1JEaF5cXmRCf1FpRmJGdld5fUVHYVZUTXxaS00DNHVRdkdmWXdec3VTRWZfU0BxWENWYE0=');
                console.log('Syncfusion license initialized successfully');
            } catch (error) {
                console.error('Error setting Syncfusion license:', error);
            }
        } else {
            // Wait for Syncfusion to load and retry
            setTimeout(() => {
                this.initializeSyncfusion();
            }, 200);
        }
    }

    updateCollectionInfo() {
        const collectionInfo = document.getElementById('collectionInfo');
        collectionInfo.innerHTML = `
            <div class="text-end">
                <div class="fw-bold">${this.exchange}</div>
                <small>${this.startDate} to ${this.endDate}</small>
            </div>
        `;
    }

    async loadStockList() {
        try {
            console.log('Loading stock list for collection:', this.collectionId);
            console.log('API URL:', `/api/data-collection/collections/${this.collectionId}/symbols`);
            
            const response = await fetch(`/api/data-collection/collections/${this.collectionId}/symbols`);
            console.log('Response status:', response.status);
            console.log('Response headers:', response.headers);
            
            const data = await response.json();
            console.log('Stock list response:', data);
            
            if (data.success) {
                this.allSymbols = data.symbols;
                console.log('All symbols loaded:', this.allSymbols.length);
                console.log('Symbols array:', this.allSymbols);
                
                // Populate the dropdown
                this.populateStockSelect(data.symbols);
                
                console.log('Stock list populated with', data.symbols.length, 'symbols');
            } else {
                console.error('Failed to load stock list:', data.error);
                this.showError('Failed to load stock list: ' + (data.error || 'Unknown error'));
            }
        } catch (error) {
            console.error('Error loading stock list:', error);
            this.showError('Error loading stock list: ' + error.message);
        }
    }

    populateStockSelect(symbols) {
        console.log('Populating stock select with', symbols.length, 'symbols');
        console.log('Symbols array:', symbols);
        
        const dropdown = document.getElementById('stockDropdown');
        const searchInput = document.getElementById('stockSearch');
        
        if (!dropdown || !searchInput) {
            console.error('Dropdown or search input not found');
            console.error('Dropdown element:', dropdown);
            console.error('Search input element:', searchInput);
            return;
        }
        
        console.log('Found dropdown and search input elements');
        
        // Clear existing items
        dropdown.innerHTML = '';
        console.log('Cleared dropdown HTML');
        
        // Add placeholder item
        const placeholderItem = document.createElement('a');
        placeholderItem.className = 'dropdown-item';
        placeholderItem.href = '#';
        placeholderItem.textContent = 'Choose a stock...';
        placeholderItem.addEventListener('click', (e) => {
            e.preventDefault();
            this.selectStock('');
        });
        dropdown.appendChild(placeholderItem);
        console.log('Added placeholder item');
        
        // Add stock items
        symbols.forEach((symbol, index) => {
            console.log(`Adding symbol ${index}: ${symbol}`);
            const item = document.createElement('a');
            item.className = 'dropdown-item';
            item.href = '#';
            item.textContent = symbol;
            item.addEventListener('click', (e) => {
                e.preventDefault();
                this.selectStock(symbol);
            });
            dropdown.appendChild(item);
        });
        
        // Store symbols for filtering
        this.stockList = symbols;
        
        console.log('Stock dropdown populated with', symbols.length, 'items');
        console.log('Final dropdown HTML length:', dropdown.innerHTML.length);
        console.log('Final dropdown children count:', dropdown.children.length);
    }

    selectStock(symbol) {
        console.log('Stock selected:', symbol);
        
        const searchInput = document.getElementById('stockSearch');
        const dropdown = document.getElementById('stockDropdown');
        const dropdownButton = document.getElementById('dropdownButton');
        
        if (!searchInput || !dropdown || !dropdownButton) {
            console.error('Stock selection elements not found');
            return;
        }
        
        // Update search input
        searchInput.value = symbol;
        
        // Hide dropdown
        dropdown.style.display = 'none';
        
        // Reset arrow icon
        const icon = dropdownButton.querySelector('i');
        if (icon) {
            icon.className = 'fas fa-chevron-down';
        }
        
        // Update current symbol and load data
        this.currentSymbol = symbol;
        if (symbol) {
            this.loadStockData();
        }
    }

    toggleDropdown() {
        console.log('toggleDropdown called');
        const dropdown = document.getElementById('stockDropdown');
        const dropdownButton = document.getElementById('dropdownButton');
        const searchInput = document.getElementById('stockSearch');
        
        console.log('Dropdown elements:', { dropdown, dropdownButton, searchInput });
        
        if (!dropdown || !dropdownButton || !searchInput) {
            console.error('Dropdown elements not found');
            return;
        }
        
        const isVisible = dropdown.style.display === 'block';
        const icon = dropdownButton.querySelector('i');
        
        if (isVisible) {
            // Hide dropdown
            dropdown.style.display = 'none';
            if (icon) {
                icon.className = 'fas fa-chevron-down';
            }
        } else {
            // Show dropdown
            dropdown.style.display = 'block';
            if (icon) {
                icon.className = 'fas fa-chevron-up';
            }
            
            // If search is empty, show all items
            if (!searchInput.value) {
                const items = dropdown.querySelectorAll('.dropdown-item');
                items.forEach(item => {
                    item.style.display = 'block';
                });
            }
        }
    }

    filterStocks() {
        console.log('filterStocks called');
        const searchInput = document.getElementById('stockSearch');
        const dropdown = document.getElementById('stockDropdown');
        const dropdownButton = document.getElementById('dropdownButton');
        
        console.log('Filter elements:', { searchInput, dropdown, dropdownButton });
        
        if (!searchInput || !dropdown || !dropdownButton) {
            console.error('Search elements not found');
            return;
        }
        
        const searchTerm = searchInput.value.toLowerCase();
        console.log('Filtering stocks with term:', searchTerm);
        
        // Get all dropdown items (skip the first one which is the placeholder)
        const items = dropdown.querySelectorAll('.dropdown-item');
        console.log('Total dropdown items found:', items.length);
        
        let visibleCount = 0;
        
        items.forEach((item, index) => {
            if (index === 0) {
                // Always show placeholder
                item.style.display = 'block';
                console.log('Placeholder item:', item.textContent);
                return;
            }
            
            const symbol = item.textContent.toLowerCase();
            console.log(`Item ${index}: "${symbol}" - includes "${searchTerm}": ${symbol.includes(searchTerm)}`);
            if (symbol.includes(searchTerm)) {
                item.style.display = 'block';
                visibleCount++;
            } else {
                item.style.display = 'none';
            }
        });
        
        console.log('Filtered to', visibleCount, 'matching symbols');
        
        // Show dropdown if there's a search term or if it's already visible
        if (searchTerm.length > 0 || dropdown.style.display === 'block') {
            dropdown.style.display = 'block';
            // Change arrow to up
            const icon = dropdownButton.querySelector('i');
            if (icon) {
                icon.className = 'fas fa-chevron-up';
            }
        }
    }

    // filterStocks function removed - now using Syncfusion's built-in filtering

    async loadStockData() {
        console.log('loadStockData called');
        
        const selectedSymbol = this.currentSymbol;
        
        console.log('Selected symbol:', selectedSymbol);
        
        if (!selectedSymbol) {
            console.log('No symbol selected, hiding stock info');
            document.getElementById('stockInfo').style.display = 'none';
            document.getElementById('chartContainer').innerHTML = '';
            return;
        }
        
        this.currentSymbol = selectedSymbol;
        this.showLoading(true);
        
        try {
            console.log('Fetching data for symbol:', selectedSymbol);
            const response = await fetch(`/api/data-collection/collections/${this.collectionId}/symbols/${selectedSymbol}`);
            const data = await response.json();
            
            console.log('Stock data response:', data);
            console.log('Response status:', response.status);
            console.log('Data keys:', Object.keys(data));
            
            if (data.success && data.stock_data && data.stock_data.length > 0) {
                console.log('Data points received:', data.stock_data.length);
                this.displayStockInfo(selectedSymbol, data.stock_data);
                this.createStockChart(data.stock_data);
            } else {
                console.error('Failed to load stock data:', data);
                if (data.stock_data && data.stock_data.length === 0) {
                    this.showError('No data available for this symbol');
                } else {
                    this.showError('Failed to load stock data: ' + (data.error || 'Unknown error'));
                }
            }
        } catch (error) {
            console.error('Error loading stock data:', error);
            this.showError('Error loading stock data: ' + error.message);
        } finally {
            this.showLoading(false);
        }
    }

    displayStockInfo(symbol, stockData) {
        const stockInfo = document.getElementById('stockInfo');
        const stockSymbol = document.getElementById('stockSymbol');
        const stockPrice = document.getElementById('stockPrice');
        const stockChange = document.getElementById('stockChange');
        const stockStats = document.getElementById('stockStats');
        
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
            const volatility = this.calculateVolatility(stockData);
            const totalReturn = ((currentPrice - stockData[0].Close) / stockData[0].Close) * 100;
            
            stockPrice.innerHTML = `$${currentPrice.toFixed(2)}`;
            stockChange.innerHTML = `
                <span class="${change >= 0 ? 'change-positive' : 'change-negative'}">
                    ${change >= 0 ? '+' : ''}${change.toFixed(2)} (${changePercent.toFixed(2)}%)
                </span>
            `;
            
            // Update stats grid
            stockStats.innerHTML = `
                <div class="stat-item">
                    <div class="stat-value">$${high.toFixed(2)}</div>
                    <div class="stat-label">52-Week High</div>
                </div>
                <div class="stat-item">
                    <div class="stat-value">$${low.toFixed(2)}</div>
                    <div class="stat-label">52-Week Low</div>
                </div>
                <div class="stat-item">
                    <div class="stat-value">${Math.round(avgVolume).toLocaleString()}</div>
                    <div class="stat-label">Avg Volume</div>
                </div>
                <div class="stat-item">
                    <div class="stat-value">${volatility.toFixed(2)}%</div>
                    <div class="stat-label">Volatility</div>
                </div>
                <div class="stat-item">
                    <div class="stat-value ${totalReturn >= 0 ? 'change-positive' : 'change-negative'}">${totalReturn >= 0 ? '+' : ''}${totalReturn.toFixed(2)}%</div>
                    <div class="stat-label">Total Return</div>
                </div>
                <div class="stat-item">
                    <div class="stat-value">${stockData.length}</div>
                    <div class="stat-label">Data Points</div>
                </div>
            `;
            
            // Show the stock info
            stockInfo.style.display = 'block';
        }
    }

    calculateVolatility(stockData) {
        if (stockData.length < 2) return 0;
        
        const returns = [];
        for (let i = 1; i < stockData.length; i++) {
            const dailyReturn = (stockData[i].Close - stockData[i-1].Close) / stockData[i-1].Close;
            returns.push(dailyReturn);
        }
        
        const mean = returns.reduce((sum, ret) => sum + ret, 0) / returns.length;
        const variance = returns.reduce((sum, ret) => sum + Math.pow(ret - mean, 2), 0) / returns.length;
        const volatility = Math.sqrt(variance) * Math.sqrt(252) * 100; // Annualized volatility
        
        return volatility;
    }

    createStockChart(stockData) {
        this.currentChartData = stockData;
        this.renderChart(stockData);
    }

    renderChart(data) {
        console.log('renderChart called with', data.length, 'data points');
        
        // Set license key immediately before chart creation
        this.setLicenseKey();
        
        const chartContainer = document.getElementById('chartContainer');
        if (!chartContainer) {
            console.error('Chart container not found');
            return;
        }
        
        // Clear previous chart
        chartContainer.innerHTML = '';
        
        // Create chart based on current type
        switch (this.currentChartType) {
            case 'line':
                this.createLineChart(data);
                break;
            case 'candlestick':
                this.createCandlestickChart(data);
                break;
            case 'ohlc':
                this.createOHLCChart(data);
                break;
            case 'volume':
                this.createVolumeChart(data);
                break;
            case 'combined':
                this.createCombinedChart(data);
                break;
            default:
                this.createLineChart(data);
        }
    }

    createLineChart(data) {
        // Set license key before creating line chart
        this.setLicenseKey();
        
        // Filter data based on timeframe
        const filteredData = this.filterDataByTimeframe(data, this.currentTimeframe);
        
        // Transform data for Syncfusion
        const chartData = filteredData.map(d => ({
            date: new Date(d.Date),
            close: d.Close
        }));
        
        const chartContainer = document.getElementById('chartContainer');
        
        try {
            const chart = new ej.charts.Chart({
                primaryXAxis: {
                    valueType: 'DateTime',
                    majorGridLines: { width: 0 },
                    intervalType: 'Months',
                    labelFormat: 'MMM yyyy'
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
                    format: 'Date: ${point.x}<br/>Price: $${point.y}',
                    header: 'Stock Data'
                },
                series: [{
                    dataSource: chartData,
                    xName: 'date',
                    yName: 'close',
                    type: 'Line',
                    width: 2,
                    fill: '#0066FF',
                    border: { width: 2, color: '#0066FF' }
                }],
                width: '100%',
                height: '400px'
            });
            
            chart.appendTo(chartContainer);
            console.log('Line chart created successfully');
        } catch (error) {
            console.error('Error creating line chart:', error);
            chartContainer.innerHTML = '<div class="alert alert-danger">Error creating line chart</div>';
        }
    }

    createCandlestickChart(data) {
        // Set license key before creating candlestick chart
        if (typeof ej !== 'undefined' && ej.base && ej.base.setLicenseKey) {
            try {
                ej.base.setLicenseKey('Ngo9BigBOggjHTQxAR8/V1JEaF5cXmRCf1FpRmJGdld5fUVHYVZUTXxaS00DNHVRdkdmWXdec3VTRWZfU0BxWENWYE0=');
                console.log('License set before candlestick chart creation');
            } catch (error) {
                console.error('Error setting license before candlestick chart:', error);
            }
        }
        
        // Filter data based on timeframe
        const filteredData = this.filterDataByTimeframe(data, this.currentTimeframe);
        
        // Transform data for Syncfusion
        const chartData = filteredData.map(d => ({
            date: new Date(d.Date),
            close: d.Close,
            high: d.High,
            low: d.Low,
            open: d.Open,
            volume: d.Volume
        }));
        
        const chartContainer = document.getElementById('chartContainer');
        
        // Create candlestick chart using Syncfusion
        const chart = new ej.charts.Chart({
            primaryXAxis: {
                valueType: 'DateTime',
                majorGridLines: { width: 0 }
            },
            primaryYAxis: {
                labelFormat: '${value}',
                majorTickLines: { width: 0 },
                lineStyle: { width: 0 }
            },
            chartArea: {
                border: {
                    width: 0
                }
            },
            tooltip: {
                enable: true,
                format: 'Date: ${point.x}<br/>Open: $${point.open}<br/>High: $${point.high}<br/>Low: $${point.low}<br/>Close: $${point.close}',
                header: 'Candlestick Data'
            },
            series: [{
                dataSource: chartData,
                xName: 'date',
                low: 'low',
                high: 'high',
                open: 'open',
                close: 'close',
                type: 'Candle',
                name: 'Price'
            }],
            width: '100%',
            height: '600px'
        });
        
        chart.appendTo(chartContainer);
    }

    createOHLCChart(data) {
        // Set license key before creating OHLC chart
        if (typeof ej !== 'undefined' && ej.base && ej.base.setLicenseKey) {
            try {
                ej.base.setLicenseKey('Ngo9BigBOggjHTQxAR8/V1JEaF5cXmRCf1FpRmJGdld5fUVHYVZUTXxaS00DNHVRdkdmWXdec3VTRWZfU0BxWENWYE0=');
                console.log('License set before OHLC chart creation');
            } catch (error) {
                console.error('Error setting license before OHLC chart:', error);
            }
        }
        
        // Filter data based on timeframe
        const filteredData = this.filterDataByTimeframe(data, this.currentTimeframe);
        
        // Transform data for Syncfusion
        const chartData = filteredData.map(d => ({
            date: new Date(d.Date),
            close: d.Close,
            high: d.High,
            low: d.Low,
            open: d.Open,
            volume: d.Volume
        }));
        
        const chartContainer = document.getElementById('chartContainer');
        
        // Create OHLC chart using Syncfusion
        const chart = new ej.charts.Chart({
            primaryXAxis: {
                valueType: 'DateTime',
                majorGridLines: { width: 0 }
            },
            primaryYAxis: {
                labelFormat: '${value}',
                majorTickLines: { width: 0 },
                lineStyle: { width: 0 }
            },
            chartArea: {
                border: {
                    width: 0
                }
            },
            tooltip: {
                enable: true,
                format: 'Date: ${point.x}<br/>Open: $${point.open}<br/>High: $${point.high}<br/>Low: $${point.low}<br/>Close: $${point.close}',
                header: 'OHLC Data'
            },
            series: [{
                dataSource: chartData,
                xName: 'date',
                low: 'low',
                high: 'high',
                open: 'open',
                close: 'close',
                type: 'HiloOpenClose',
                name: 'Price'
            }],
            width: '100%',
            height: '600px'
        });
        
        chart.appendTo(chartContainer);
    }

    createVolumeChart(data) {
        // Set license key before creating volume chart
        this.setLicenseKey();
        
        // Filter data based on timeframe
        const filteredData = this.filterDataByTimeframe(data, this.currentTimeframe);
        
        // Transform data for Syncfusion
        const chartData = filteredData.map(d => ({
            date: new Date(d.Date),
            volume: d.Volume
        }));
        
        const chartContainer = document.getElementById('chartContainer');
        
        // Create volume chart using Syncfusion
        const chart = new ej.charts.Chart({
            primaryXAxis: {
                valueType: 'DateTime',
                majorGridLines: { width: 0 }
            },
            primaryYAxis: {
                labelFormat: '{value}',
                majorTickLines: { width: 0 },
                lineStyle: { width: 0 }
            },
            chartArea: {
                border: {
                    width: 0
                }
            },
            tooltip: {
                enable: true,
                format: 'Date: ${point.x}<br/>Volume: ${point.y}',
                header: 'Volume Data'
            },
            series: [{
                dataSource: chartData,
                xName: 'date',
                yName: 'volume',
                type: 'Column',
                name: 'Volume',
                fill: '#4CAF50',
                opacity: 0.7
            }],
            width: '100%',
            height: '400px'
        });
        
        chart.appendTo(chartContainer);
    }

    createCombinedChart(data) {
        // Set license key before creating combined chart
        this.setLicenseKey();
        
        // Filter data based on timeframe
        const filteredData = this.filterDataByTimeframe(data, this.currentTimeframe);
        
        // Transform data for Syncfusion
        const chartData = filteredData.map(d => ({
            date: new Date(d.Date),
            close: d.Close,
            volume: d.Volume
        }));
        
        const chartContainer = document.getElementById('chartContainer');
        
        // Create combined chart with price and volume
        const chart = new ej.charts.Chart({
            primaryXAxis: {
                valueType: 'DateTime',
                majorGridLines: { width: 0 }
            },
            primaryYAxis: {
                labelFormat: '${value}',
                majorTickLines: { width: 0 },
                lineStyle: { width: 0 }
            },
            axes: [{
                name: 'secondary',
                opposedPosition: true,
                majorTickLines: { width: 0 },
                lineStyle: { width: 0 }
            }],
            chartArea: {
                border: {
                    width: 0
                }
            },
            tooltip: {
                enable: true,
                format: 'Date: ${point.x}<br/>Price: $${point.y}',
                header: 'Combined Data'
            },
            series: [
                {
                    dataSource: chartData,
                    xName: 'date',
                    yName: 'close',
                    type: 'Line',
                    name: 'Price',
                    fill: '#0066FF',
                    border: { width: 2, color: '#0066FF' }
                },
                {
                    dataSource: chartData,
                    xName: 'date',
                    yName: 'volume',
                    type: 'Column',
                    name: 'Volume',
                    yAxisName: 'secondary',
                    fill: '#4CAF50',
                    opacity: 0.3
                }
            ],
            width: '100%',
            height: '600px'
        });
        
        chart.appendTo(chartContainer);
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

    showLoading(show) {
        const spinner = document.getElementById('loadingSpinner');
        if (spinner) {
            if (show) {
                spinner.style.display = 'block';
            } else {
                spinner.style.display = 'none';
            }
        }
    }

    showError(message) {
        const chartContainer = document.getElementById('chartContainer');
        if (chartContainer) {
            chartContainer.innerHTML = `
                <div class="text-center text-danger p-5">
                    <i class="fas fa-exclamation-triangle fa-3x mb-3"></i>
                    <h4>Error</h4>
                    <p>${message}</p>
                </div>
            `;
        }
        
        // Also show in console for debugging
        console.error('Stock Viewer Error:', message);
    }

    exportChart() {
        if (!this.currentSymbol) {
            alert('Please select a stock first');
            return;
        }
        
        // Create a canvas element for export
        const canvas = document.createElement('canvas');
        const ctx = canvas.getContext('2d');
        canvas.width = 1200;
        canvas.height = 800;
        
        // Draw chart to canvas (simplified version)
        ctx.fillStyle = 'white';
        ctx.fillRect(0, 0, canvas.width, canvas.height);
        
        ctx.fillStyle = 'black';
        ctx.font = '24px Arial';
        ctx.fillText(`${this.currentSymbol} - ${this.currentChartType.toUpperCase()} Chart`, 50, 50);
        ctx.font = '16px Arial';
        ctx.fillText(`Timeframe: ${this.currentTimeframe}`, 50, 80);
        ctx.fillText(`Generated: ${new Date().toLocaleString()}`, 50, 100);
        
        // Convert to blob and download
        canvas.toBlob((blob) => {
            const url = URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `${this.currentSymbol}_${this.currentChartType}_${this.currentTimeframe}_${new Date().toISOString().split('T')[0]}.png`;
            a.click();
            URL.revokeObjectURL(url);
        });
    }

    refreshData() {
        if (this.currentSymbol) {
            this.loadStockData();
        }
    }

    async loadCollectionDetails() {
        try {
            console.log('Loading collection details for:', this.collectionId);
            const response = await fetch(`/api/data-collection/collections/${this.collectionId}`);
            const data = await response.json();
            
            console.log('Collection details response:', data);
            
            if (data.success) {
                this.collectionData = data.collection;
                console.log('Collection data:', this.collectionData);
                this.displayCollectionSummary(data.collection);
            } else {
                console.error('Failed to load collection details:', data.error);
            }
        } catch (error) {
            console.error('Error loading collection details:', error);
        }
    }

    displayCollectionSummary(collection) {
        console.log('displayCollectionSummary called with:', collection);
        
        const summarySection = document.getElementById('collectionSummary');
        if (!summarySection) {
            console.error('Collection summary section not found!');
            return;
        }
        
        console.log('Found summary section, updating fields...');
        
        // Update summary fields
        const exchangeElement = document.getElementById('summaryExchange');
        const dateRangeElement = document.getElementById('summaryDateRange');
        const collectionDateElement = document.getElementById('summaryCollectionDate');
        const statusElement = document.getElementById('summaryStatus');
        
        if (exchangeElement) {
            exchangeElement.textContent = collection.exchange || collection.config?.exchange || 'N/A';
            console.log('Updated exchange element:', exchangeElement.textContent);
        }
        if (dateRangeElement) {
            dateRangeElement.textContent = `${collection.start_date || collection.config?.start_date || 'N/A'} to ${collection.end_date || collection.config?.end_date || 'N/A'}`;
            console.log('Updated date range element:', dateRangeElement.textContent);
        }
        if (collectionDateElement) {
            collectionDateElement.textContent = new Date(collection.collection_date || collection.created_at || Date.now()).toLocaleString();
            console.log('Updated collection date element:', collectionDateElement.textContent);
        }
        if (statusElement) {
            statusElement.textContent = collection.status || 'Completed';
            console.log('Updated status element:', statusElement.textContent);
        }
        
        // Update statistics badges
        const totalSymbolsElement = document.getElementById('summaryTotalSymbols');
        const successfulElement = document.getElementById('summarySuccessful');
        const failedElement = document.getElementById('summaryFailed');
        const successRateElement = document.getElementById('summarySuccessRate');
        
        const totalSymbols = collection.total_symbols || collection.symbols_count || 0;
        const successfulSymbols = collection.successful_symbols || collection.successful_count || 0;
        const failedCount = collection.failed_count || 0;
        const successRate = totalSymbols > 0 ? Math.round((successfulSymbols / totalSymbols) * 100) : 0;
        
        if (totalSymbolsElement) {
            totalSymbolsElement.textContent = `Total: ${totalSymbols}`;
            console.log('Updated total symbols element:', totalSymbolsElement.textContent);
        }
        if (successfulElement) {
            successfulElement.textContent = `Success: ${successfulSymbols}`;
            console.log('Updated successful element:', successfulElement.textContent);
        }
        if (failedElement) {
            failedElement.textContent = `Failed: ${failedCount}`;
            console.log('Updated failed element:', failedElement.textContent);
        }
        if (successRateElement) {
            successRateElement.textContent = `Rate: ${successRate}%`;
            console.log('Updated success rate element:', successRateElement.textContent);
        }
        
        // Show the summary section
        summarySection.style.display = 'block';
        console.log('Collection summary displayed successfully');
        console.log('Summary section display style:', summarySection.style.display);
    }

    async deleteCollection() {
        if (!this.collectionId) {
            this.showError('No collection ID available for deletion');
            return;
        }

        // Show confirmation dialog
        const confirmed = confirm('Are you sure you want to delete this collection? This action cannot be undone.');
        
        if (!confirmed) {
            return;
        }

        try {
            console.log('Deleting collection:', this.collectionId);
            const response = await fetch(`/api/data-collection/collections/${this.collectionId}`, {
                method: 'DELETE'
            });

            const result = await response.json();

            if (result.success) {
                alert('Collection deleted successfully');
                // Close the window or redirect
                window.close();
            } else {
                this.showError(`Error deleting collection: ${result.error}`);
            }
        } catch (error) {
            console.error('Error deleting collection:', error);
            this.showError('Error deleting collection');
        }
    }

    setLicenseKey() {
        const licenseKey = 'Ngo9BigBOggjHTQxAR8/V1JEaF5cXmRCf1FpRmJGdld5fUVHYVZUTXxaS00DNHVRdkdmWXdec3VTRWZfU0BxWENWYE0=';
        
        // Only set license when charts are created
        if (typeof ej !== 'undefined' && ej.base) {
            try {
                if (ej.base.setLicenseKey) {
                    ej.base.setLicenseKey(licenseKey);
                    console.log('License set via setLicenseKey method');
                }
            } catch (error) {
                console.error('Error setting license via setLicenseKey:', error);
            }
        }
        
        // Also set it on window object
        try {
            window.SyncfusionLicenseKey = licenseKey;
            console.log('License set on window.SyncfusionLicenseKey');
        } catch (error) {
            console.error('Error setting license on window object:', error);
        }
    }
}

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    console.log('DOM loaded, creating StockViewer...');
    window.stockViewer = new StockViewer();
    console.log('StockViewer created:', window.stockViewer);
});

// Global function for HTML access
window.filterStocks = function() {
    if (window.stockViewer) {
        window.stockViewer.filterStocks();
    } else {
        console.error('StockViewer not initialized yet');
    }
}; 