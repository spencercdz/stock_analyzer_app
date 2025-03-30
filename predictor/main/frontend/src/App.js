import React, { useState, useRef, useEffect } from "react";
import './App.css';
import GridLayout from './components/GridLayout';
import Box from './components/Box';
import { Line } from 'react-chartjs-2';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend
} from 'chart.js';

ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend
);

function App() {
  const [ticker, setTicker] = useState("");
  const [stockData, setStockData] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);
  const [timeframe, setTimeframe] = useState('1D');
  const [priceHistory, setPriceHistory] = useState(null);
  const [retryCount, setRetryCount] = useState(0);
  const videoRef = useRef(null);
  const cacheRef = useRef({});

  useEffect(() => {
    if (videoRef.current) {
      videoRef.current.playbackRate = 0.85;
    }
  }, []);

  useEffect(() => {
    console.log("API URL:", process.env.REACT_APP_API_URL);
  }, []);

  const apiUrl = process.env.REACT_APP_API_URL || 'https://spencer-stock-analyzer.onrender.com';

  const delay = (ms) => new Promise(resolve => setTimeout(resolve, ms));

  const fetchWithRetry = React.useCallback(async (url, options = {}, retryCount = 0, maxRetries = 3) => {
    console.log(`Attempting to fetch from: ${url}`);
    try {
      const response = await fetch(url, options);
      if (!response.ok) {
        throw new Error('Failed to fetch data');
      }
      return response;
    } catch (error) {
      console.error(`Fetch error: ${error.message}`);
      if (retryCount < maxRetries) {
        const backoffDelay = Math.min(1000 * Math.pow(2, retryCount), 10000); // Exponential backoff, max 10 seconds
        console.log(`Retrying in ${backoffDelay}ms (attempt ${retryCount + 1}/${maxRetries})`);
        await delay(backoffDelay);
        return fetchWithRetry(url, options, retryCount + 1, maxRetries);
      }
      throw error;
    }
  }, []);

  const fetchStockData = React.useCallback(async () => {
    if (!ticker.trim()) {
      setError("Please enter a valid stock ticker");
      return;
    }

    setIsLoading(true);
    setError(null);
    setRetryCount(0);
    
    // Check cache first
    const cacheKey = `${ticker}-${timeframe}`;
    const cachedData = cacheRef.current[cacheKey];
    if (cachedData && Date.now() - cachedData.timestamp < 5 * 60 * 1000) { // Cache for 5 minutes
      console.log(`Using cached data for ${ticker}`);
      setStockData(cachedData.stockData);
      setPriceHistory(cachedData.priceHistory);
      setIsLoading(false);
      return;
    }

    try {
      // Fetch stock data
      const stockUrl = `${apiUrl}/api/stock/${ticker.toUpperCase()}`;
      console.log(`Fetching stock data from: ${stockUrl}`);
      
      // Fetch stock data
      const response = await fetchWithRetry(stockUrl);
      const data = await response.json();
      console.log("Stock data received:", data);

      // Add delay between requests
      await delay(1000);
      
      // Fetch price history
      const historyUrl = `${apiUrl}/api/stock/${ticker.toUpperCase()}/history?timeframe=${timeframe}`;
      console.log(`Fetching price history from: ${historyUrl}`);
      const historyResponse = await fetchWithRetry(historyUrl);
      const historyData = await historyResponse.json();
      console.log("History data received:", historyData);

      // Update state
      setStockData(data);
      setPriceHistory(historyData);
      
      // Update cache
      cacheRef.current[cacheKey] = {
        stockData: data,
        priceHistory: historyData,
        timestamp: Date.now()
      };
    } catch (error) {
      console.error("Error fetching stock data:", error);
      setError(error.message === 'Failed to fetch data' 
        ? 'Too many requests. Please wait a moment and try again.'
        : 'An error occurred while fetching stock data. Please try again.');
      setStockData(null);
      setPriceHistory(null);
    } finally {
      setIsLoading(false);
    }
  }, [ticker, timeframe, fetchWithRetry, apiUrl]);

  const handleTimeframeChange = React.useCallback((newTimeframe) => {
    setTimeframe(newTimeframe);
    if (stockData) { // Only fetch if we already have data
      fetchStockData();
    }
  }, [stockData, fetchStockData]);

  const formatNumber = (num) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 2,
      maximumFractionDigits: 2
    }).format(num);
  };

  const formatPercent = (num) => {
    return `${(num * 100).toFixed(2)}%`;
  };

  const chartData = priceHistory ? {
    labels: priceHistory.timestamps,
    datasets: [
      {
        label: 'Stock Price',
        data: priceHistory.prices,
        borderColor: 'rgb(147, 0, 255)',
        backgroundColor: 'rgba(147, 0, 255, 0.1)',
        tension: 0.4,
        fill: true
      }
    ]
  } : null;

  const chartOptions = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        display: false
      }
    },
    scales: {
      y: {
        beginAtZero: false,
        grid: {
          color: 'rgba(255, 255, 255, 0.1)'
        },
        ticks: {
          color: 'rgba(255, 255, 255, 0.8)'
        }
      },
      x: {
        grid: {
          color: 'rgba(255, 255, 255, 0.1)'
        },
        ticks: {
          color: 'rgba(255, 255, 255, 0.8)'
        }
      }
    }
  };

  return (
    <div className="App">
      <video
        ref={videoRef}
        autoPlay
        loop
        muted
        playsInline
        className="video-background"
      >
        <source src="/background.mp4" type="video/mp4" />
      </video>
      <GridLayout>
        <Box title="Spencer's Stock Analysis">
          <div className="search-container">
            <input
              type="text"
              placeholder="Enter stock ticker"
              value={ticker}
              onChange={(e) => setTicker(e.target.value)}
              disabled={isLoading}
            />
            <button 
              onClick={fetchStockData}
              disabled={isLoading || !ticker}
              className={isLoading ? 'loading' : ''}
            >
              {isLoading ? 'Loading...' : 'Search'}
            </button>
          </div>
          {error && <div className="error-message">{error}</div>}
          {retryCount > 0 && (
            <div className="retry-message">
              Retrying... (Attempt {retryCount}/3)
            </div>
          )}
        </Box>
        <Box title="Ticker Information">
          {isLoading ? (
            <div className="loading-message">Loading stock data...</div>
          ) : stockData ? (
            <div className="stock-info">
              <div className="info-row">
                <span className="label">Symbol:</span>
                <span className="value">{stockData.symbol}</span>
              </div>
              <div className="info-row">
                <span className="label">Company Name:</span>
                <span className="value">{stockData.companyName}</span>
              </div>
              <div className="info-row">
                <span className="label">Current Price:</span>
                <span className="value">{formatNumber(stockData.currentPrice)}</span>
              </div>
              <div className="info-row">
                <span className="label">Market Cap:</span>
                <span className="value">{formatNumber(stockData.marketCap)}</span>
              </div>
              <div className="info-row">
                <span className="label">Open:</span>
                <span className="value">{formatNumber(stockData.open)}</span>
              </div>
              <div className="info-row">
                <span className="label">High:</span>
                <span className="value">{formatNumber(stockData.high)}</span>
              </div>
              <div className="info-row">
                <span className="label">Low:</span>
                <span className="value">{formatNumber(stockData.low)}</span>
              </div>
              <div className="info-row">
                <span className="label">Volume:</span>
                <span className="value">{stockData.volume.toLocaleString()}</span>
              </div>
            </div>
          ) : (
            <div className="placeholder-message">Enter a stock ticker to view information</div>
          )}
        </Box>
        <Box title="Valuation Summary">
          {isLoading ? (
            <div className="loading-message">Loading valuation data...</div>
          ) : stockData ? (
            <div className="stock-info">
              <div className="info-row">
                <span className="label">P/E Ratio:</span>
                <span className="value">{stockData.peRatio.toFixed(2)}</span>
              </div>
              <div className="info-row">
                <span className="label">Dividend Yield:</span>
                <span className="value">{formatPercent(stockData.dividendYield)}</span>
              </div>
              <div className="info-row">
                <span className="label">Beta:</span>
                <span className="value">{stockData.beta.toFixed(2)}</span>
              </div>
              <div className="info-row">
                <span className="label">52 Week High:</span>
                <span className="value">{formatNumber(stockData.fiftyTwoWeekHigh)}</span>
              </div>
            </div>
          ) : (
            <div className="placeholder-message">Enter a stock ticker to view valuation data</div>
          )}
        </Box>
        <Box title="Stock Price Chart">
          {isLoading ? (
            <div className="loading-message">Loading price chart...</div>
          ) : stockData ? (
            <div className="chart-container">
              <div className="timeframe-selector">
                <button 
                  className={timeframe === '1D' ? 'active' : ''} 
                  onClick={() => handleTimeframeChange('1D')}
                  disabled={isLoading}
                >
                  1D
                </button>
                <button 
                  className={timeframe === '1W' ? 'active' : ''} 
                  onClick={() => handleTimeframeChange('1W')}
                  disabled={isLoading}
                >
                  1W
                </button>
                <button 
                  className={timeframe === '1M' ? 'active' : ''} 
                  onClick={() => handleTimeframeChange('1M')}
                  disabled={isLoading}
                >
                  1M
                </button>
                <button 
                  className={timeframe === '3M' ? 'active' : ''} 
                  onClick={() => handleTimeframeChange('3M')}
                  disabled={isLoading}
                >
                  3M
                </button>
                <button 
                  className={timeframe === '1Y' ? 'active' : ''} 
                  onClick={() => handleTimeframeChange('1Y')}
                  disabled={isLoading}
                >
                  1Y
                </button>
              </div>
              <div className="chart-wrapper">
                {chartData && <Line data={chartData} options={chartOptions} />}
              </div>
            </div>
          ) : (
            <div className="placeholder-message">Enter a stock ticker to view price chart</div>
          )}
        </Box>
      </GridLayout>
    </div>
  );
}

export default App;
