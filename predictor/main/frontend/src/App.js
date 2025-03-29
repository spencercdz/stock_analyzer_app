import React, { useState } from "react";
import './App.css';

function App() {
  const [ticker, setTicker] = useState("");
  const [stockData, setStockData] = useState(null);

  const fetchStockData = async () => {
    try {
      const response = await fetch(`http://127.0.0.1:5000/api/stock/${ticker}`);
      const data = await response.json();
      setStockData(data);
    } catch (error) {
      console.error("Error fetching stock data:", error);
    }
  };

  return (
    <div className="container">
      <div className="grid-container">
        <div className='box'>
          <h1>Spencer's Stock Analysis</h1>
          <input
            type="text"
            placeholder="Enter stock ticker"
            value={ticker}
            onChange={(e) => setTicker(e.target.value)}
          />
          <button onClick={fetchStockData}>Fetch Stock Data</button>
          {stockData && <pre>{JSON.stringify(stockData, null, 2)}</pre>}
        </div>
        <div className='box'>
          <h1>Ticker Information</h1>
          {stockData && <pre>{JSON.stringify(stockData, null, 2)}</pre>}
        </div>
        <div className='box'>
          <h1>Valuation Summary</h1>
          {stockData && <pre>{JSON.stringify(stockData, null, 2)}</pre>}
        </div>
        <div className='box'>
          <h1>Stock Price</h1>
          {stockData && <pre>{JSON.stringify(stockData, null, 2)}</pre>}
        </div>
      </div>
    </div>
  );
}

export default App;
