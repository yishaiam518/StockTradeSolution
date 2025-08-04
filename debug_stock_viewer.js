// Debug script for stock viewer
async function debugStockViewer() {
    console.log('🔍 DEBUGGING STOCK VIEWER');
    
    const collectionId = 'AMEX_20250803_161652';
    const symbol = 'BND';
    
    try {
        console.log('Testing API endpoint...');
        const response = await fetch(`/api/data-collection/collections/${collectionId}/symbols/${symbol}/data-with-indicators`);
        const data = await response.json();
        
        console.log('API Response:', data);
        console.log('Success:', data.success);
        console.log('Indicators available:', data.indicators_available);
        console.log('Data points:', data.data ? data.data.length : 0);
        console.log('Columns:', data.columns);
        
        if (data.data && data.data.length > 0) {
            const latest = data.data[data.data.length - 1];
            console.log('Latest data point:', latest);
            
            // Check for indicator columns
            const indicatorColumns = data.columns.filter(col => 
                col.includes('SMA') || col.includes('EMA') || col.includes('RSI') || 
                col.includes('MACD') || col.includes('Bollinger') || col.includes('ATR') ||
                col.includes('Stochastic') || col.includes('Williams') || col.includes('OBV') ||
                col.includes('VWAP') || col.includes('MFI')
            );
            
            console.log('Found indicator columns:', indicatorColumns);
            
            // Check if latest point has indicator values
            indicatorColumns.forEach(col => {
                if (latest[col] !== undefined) {
                    console.log(`${col}: ${latest[col]}`);
                }
            });
        }
        
    } catch (error) {
        console.error('Error in debug:', error);
    }
}

// Run debug when page loads
if (typeof window !== 'undefined') {
    window.debugStockViewer = debugStockViewer;
    console.log('Debug function available as window.debugStockViewer()');
} 