import React, { useState } from "react";

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
    <div class='center'>
      <h1 class="App-header">Spencer's Stock Analysis</h1>
      <input
        type="text"
        placeholder="Enter stock ticker"
        value={ticker}
        onChange={(e) => setTicker(e.target.value)}
      />
      <button onClick={fetchStockData}>Fetch Stock Data</button>
      {stockData && <pre>{JSON.stringify(stockData, null, 2)}</pre>}
    </div>
  );
}

export default App;
