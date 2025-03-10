# Spencer's Stock Analyzer (Work in Progress)

Welcome to the Spencer's Stock Analyzer repository! This project aims to provide a comprehensive tool for analyzing stocks by determining their intrinsic value using **Discounted Cash Flow (DCF) modeling** and historical growth metrics. While still under development, the project already offers several powerful features and promises more enhancements in the near future.

## Key Features

- **Stock Ticker Input:**  
  Enter a stock ticker to instantly retrieve detailed stock information.

- **DCF Calculations:**  
  Leverages a **C++ module** to perform the arithmetic calculations behind the DCF model.

- **Intrinsic Value Estimation:**  
  Calculates the intrinsic value of a stock using **DCF modeling with historical CAGR as the average growth rate**.

- **Data Retrieval via Yfinance API:**  
  Scrapes stock information such as **price, financials, and beta** for an up-to-date analysis.

- **Comprehensive Data Integration:**  
  Incorporates **JSON data** including various countries’ **10Y Treasury Rates**, **benchmark index long-term returns**, **industry data**, and **long-term growth rates**.

## Planned Enhancements

- **Stock Price Visualization:**  
  Implement **Matplotlib** to generate dynamic plots of historical stock prices.

- **Detailed DCF Breakdown:**  
  Provide an in-depth explanation and visualization of each component in the DCF valuation process.

- **Predictive Modelling:**  
  Develop **advanced predictive analytics** based on key financial metrics to forecast future stock performance.

## Technologies Used

- **C++** – For efficient and robust DCF arithmetic calculations.  
- **Python** – Integration with the Yfinance API and data handling.  
- **JSON** – Data storage for treasury rates, industry growth metrics, and additional benchmarks.  
- **Matplotlib (Planned)** – To be used for plotting stock price trends and visualizing analytical data.  

## What the Project Does

**Spencer's Stock Analyzer** is designed for **investors and financial analysts** to help evaluate whether a stock is **undervalued or overvalued**. By combining real-time data with historical financial metrics, the tool computes a stock's **intrinsic value** based on a tailored **DCF model**, providing users with actionable insights into their investment decisions.

## How It Works

1. **User Input:**  
   The user inputs a **stock ticker**.
2. **Data Scraping:**  
   The system retrieves stock details from the **Yfinance API**.
3. **DCF Calculation:**  
   A dedicated **C++ module** carries out the arithmetic necessary for the **DCF valuation**.
4. **Intrinsic Value Computation:**  
   The intrinsic value is calculated using the **historical CAGR as the average growth rate**.
5. **Output:**  
   The tool outputs the **intrinsic value** along with a range of detailed financial information.

## Challenges Encountered

- **Data Integration:**  
  Merging data from multiple sources (**Yfinance API and JSON data**) into a unified framework.

- **Performance & Integration:**  
  Ensuring smooth and efficient communication between the **C++ module and Python components**.

- **Advanced Modelling:**  
  Refining predictive models to provide **reliable forecasts** based on fluctuating market metrics.

## What’s Next

- **Visualization Enhancements:**  
  Adding **interactive charts with Matplotlib** to visualize **stock price trends and valuation components**.

- **Enhanced DCF Details:**  
  Breaking down the **DCF analysis** into a more **detailed and understandable format**.

- **Predictive Analytics Development:**  
  Integrating **machine learning models** to offer **predictive insights** based on comprehensive financial data.
