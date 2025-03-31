# Spencer's Stock Analyzer

[![Visit My Website](https://i.imgur.com/YKeSv7l.gif)](https://spencer-analyzer.vercel.app/)

**NOTE: It may take over a minute when the first stock ticker is input due to Render's winding down after inactivity. After the Render backend has been restarted fully, the subsequent ticker searches should be instantaneous!**

## Overview

**Spencer's Stock Analyzer** is a full-stack financial tool designed to help investors and analysts assess stock valuations using **Discounted Cash Flow (DCF) modeling**. By integrating **real-time market data** with **historical financial metrics**, this application determines whether a stock is **undervalued or overvalued**, providing actionable insights for informed investment decisions.

## Features

### Current Features
- **Interactive Stock Search:** Enter a ticker symbol to retrieve real-time stock data.
- **Real-Time Market Data:** Displays price, market cap, volume, and more.
- **Stock Price Visualization:** View price charts across multiple timeframes (1D, 1W, 1M, 3M, 1Y).
- **Valuation Metrics:** Provides P/E ratio, dividend yield, beta, and 52-week high/low.
- **Discounted Cash Flow (DCF) Model:** Uses a **C++-powered DCF engine** for accurate intrinsic value estimation.
- **Efficient Caching:** Stores API responses to reduce redundant calls and enhance performance.
- **Responsive UI:** Optimized for both **desktop and mobile** viewing.

### Backend Capabilities
- **Financial Data Retrieval:** Fetches stock data using the **Yahoo Finance API**.
- **Custom DCF Calculator:** Leverages a **C++ module** for high-performance financial modeling.
- **Growth Rate Estimation:** Uses **CAGR, Reinvestment Rate × ROIC, and industry benchmarks**.
- **Market Benchmark Analysis:** Compares stocks to **Treasury rates and benchmark ETFs**.
- **RESTful API:** Provides structured endpoints for seamless front-end communication.

## Tech Stack

### Frontend
- **React.js:** Component-based UI development.
- **Chart.js:** Interactive stock price visualization.
- **CSS:** Custom styling for responsive design.

### Backend
- **Flask:** Python-based web framework for API development.
- **C++:** Performance-optimized DCF calculation module.
- **Pybind11:** For seamless integration between Python and C++.
- **yfinance:** Yahoo Finance API wrapper for stock data retrieval.

### Development Tools
- **npm:** Frontend package management.
- **setuptools:** Python package distribution.
- **Gunicorn:** WSGI HTTP server for production deployment.

## Architecture

The application follows a **client-server architecture**:
- **Frontend:** A React application provides the user interface and makes API calls to the backend.
- **Backend API:** A Flask server processes requests, retrieves stock data, and performs calculations.
- **Calculation Engine:** A **C++ module** (integrated with Python via Pybind11) performs efficient DCF calculations.
- **Data Sources:** Yahoo Finance API and local JSON data provide market benchmarks.

## Installation

### Prerequisites
- **Python 3.8+**
- **Node.js 14+**
- **C++ Compiler** (supporting C++11)
- **pybind11**

### Backend Setup
```bash
# Clone the repository
git clone https://github.com/yourusername/stock-analyzer.git
cd stock-analyzer

# Install backend dependencies
pip install -e .

# Set environment variables
export FLASK_APP=main
export FLASK_ENV=development
export FLASK_DEBUG=1
export FLASK_SECRET_KEY=your_secret_key
export REACT_APP_API_URL=http://localhost:5000

# Run the Flask server
flask run
```

### Frontend Setup
```bash
# Navigate to the frontend directory
cd frontend

# Install dependencies
npm install

# Start the development server
npm start
```

## API Endpoints

| Endpoint                        | Method | Description                                          |
|---------------------------------|--------|------------------------------------------------------|
| `/api/stock/<ticker>`           | GET    | Retrieves general stock information                  |
| `/api/stock/<ticker>/history`   | GET    | Retrieves historical price data with timeframe parameter |

## DCF Calculation Methodology

The **Discounted Cash Flow (DCF) Model** calculates intrinsic value using the following steps:

1. **Growth Rate Estimation:** Based on:
   - Historical **CAGR of free cash flows**
   - **Reinvestment Rate × ROIC**
   - **Industry growth benchmarks**
2. **Discount Rate (WACC):** Includes:
   - **Cost of Equity** (via CAPM model)
   - **Cost of Debt** (interest expense / total debt)
   - Market cap and debt weightings
3. **Future Cash Flow Projection:** Projects for 5 years with an estimated growth rate.
4. **Terminal Value Calculation:** Uses the **Gordon Growth Model**.
5. **Present Value Calculation:** Discounts all future cash flows to present value.
6. **Intrinsic Value Computation:** Determines per-share valuation.

## Future Enhancements

- **Enhanced Visualization:** Integrate **Matplotlib** for interactive charts.
- **Detailed DCF Breakdown:** Provide a visual step-by-step breakdown of the DCF model.
- **Machine Learning Integration:** Incorporate predictive analytics based on historical trends.
- **Portfolio Analysis:** Enable analysis of multiple stocks for diversification.
- **Sensitivity Analysis:** Examine the impact of changes in growth/discount rates.
- **Export Functionality:** Allow downloading of reports in PDF or Excel format.
- **User Accounts:** Enable saving of favorite stocks and custom analysis parameters.

## Contributing

Contributions are welcome! Please follow these steps:
1. **Fork** the repository.
2. Create your **feature branch**:
   ```bash
   git checkout -b feature/AmazingFeature
   ```
3. **Commit** your changes:
   ```bash
   git commit -m 'Add some AmazingFeature'
   ```
4. **Push** to the branch:
   ```bash
   git push origin feature/AmazingFeature
   ```
5. Open a **Pull Request**!

## Acknowledgments

- **Yahoo Finance API** for providing comprehensive stock data.
- The **financial modeling community** for insights into DCF methodologies.
- The **open-source community** for various tools and libraries.
