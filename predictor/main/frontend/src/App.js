import React, { useState } from "react";
import './App.css';
import GridLayout from './components/GridLayout';
import Box from './components/Box';

function App() {
  const [ticker, setTicker] = useState("");
  const [stockData, setStockData] = useState(null);

  const fetchStockData = async () => {
    try {
      const response = await fetch(`/api/stock/${ticker}`);
      const data = await response.json();
      setStockData(data);
    } catch (error) {
      console.error("Error fetching stock data:", error);
    }
  };

  return (
    <div className="App">
      <video
        autoPlay
        loop
        muted
        playsInline
        className="video-background"
        onError={(e) => console.error("Error loading video:", e)}
      >
        <source src="/background.mp4" type="video/mp4" />
        Your browser does not support the video tag or the video file is missing.
      </video>
      <GridLayout>
        <Box title="Spencer's Stock Analysis">
          <div className="search-container">
            <input
              type="text"
              placeholder="Enter stock ticker"
              value={ticker}
              onChange={(e) => setTicker(e.target.value)}
            />
            <button onClick={fetchStockData}>Search</button>
          </div>
        </Box>
        <Box title="Ticker Information">
          {stockData && <pre>{JSON.stringify(stockData, null, 2)}</pre>}
        </Box>
        <Box title="Valuation Summary">
          {stockData && <pre>{JSON.stringify(stockData, null, 2)}</pre>}
        </Box>
        <Box title="Stock Price">
          {stockData && <pre>{JSON.stringify(stockData, null, 2)}</pre>}
        </Box>
      </GridLayout>
    </div>
  );
}

export default App;
