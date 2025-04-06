# Backend: main.py
from flask_cors import CORS
from flask import Flask, request, render_template, jsonify
import os
import yfinance as yf
import pandas as pd
import dcf_calculator as dcf
import numpy as np
import json
import time
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__, template_folder=os.path.join(os.path.dirname(__file__), '..', 'templates'))
app.secret_key = os.getenv('FLASK_SECRET_KEY', 'default_secret_key')

# Configure CORS properly
CORS(app, resources={r"/api/*": {"origins": "*"}})

# Simple cache to store stock data
cache = {}

@app.route('/', methods=['GET'])
def index():
    logger.info("Root endpoint accessed")
    return {"message": "Flask backend is running"}

@app.route('/api/stock/<ticker>', methods=['GET'])
def get_stock_details(ticker):
    logger.info(f"Stock details requested for ticker: {ticker}")
    # Check if the data is already in the cache
    if ticker in cache and (time.time() - cache[ticker]['timestamp']) < 300:  # 5 minutes cache
        logger.info(f"Returning cached data for {ticker}")
        return jsonify(cache[ticker]['data'])

    # Fetch data from yfinance
    stock_data = fetch_stock_data(ticker)

    # Error handling
    if stock_data is None:
        return jsonify({"error": "Stock data not found"}), 404

    return stock_data

def fetch_stock_data(ticker):
    try:
        stock = yf.Ticker(ticker)
        info = stock.info
        
        if not info or 'symbol' not in info:
            logger.error(f"No data found for ticker: {ticker}")
            return jsonify({"error": "Stock data not found"}), 404
        
        # Format data to match frontend expectations
        stock_data = {
            "symbol": info.get('symbol', ''),
            "companyName": info.get('longName', ''),
            "industry": info.get('industry', ''),
            "currentPrice": info.get('currentPrice', 0),
            "marketCap": info.get('marketCap', 0),
            "open": info.get('regularMarketOpen', 0),
            "high": info.get('dayHigh', 0),
            "low": info.get('dayLow', 0),
            "volume": info.get('volume', 0),
            "dividendYield": info.get('dividendYield', 0) / 100 or 0,
            "beta": info.get('beta', 0) or 0,
            "fiftyTwoWeekHigh": info.get('fiftyTwoWeekHigh', 0)
        }
        
        # Store in cache with timestamp
        cache[ticker] = {
            'data': stock_data,
            'timestamp': time.time()
        }
        
        logger.info(f"Successfully fetched and returning data for {ticker}")
        return jsonify(stock_data)
        
    except Exception as e:
        logger.error(f"Error fetching stock data for {ticker}: {str(e)}")
        return jsonify({"error": f"Failed to fetch stock data: {str(e)}"}), 500

@app.route('/api/stock/<ticker>/history', methods=['GET'])
def get_stock_history(ticker):
    logger.info(f"Stock history requested for ticker: {ticker}")
    
    # Define all timeframes and their corresponding yfinance parameters
    timeframe_configs = {
        '1D': {'period': '1d', 'interval': '30m'},
        '1W': {'period': '1wk', 'interval': '1d'},
        '1M': {'period': '1mo', 'interval': '1d'},
        '3M': {'period': '3mo', 'interval': '1wk'},
        '1Y': {'period': '1y', 'interval': '1mo'}
    }
    
    try:
        stock = yf.Ticker(ticker)
        all_history_data = {}
        
        for timeframe, config in timeframe_configs.items():
            hist = stock.history(period=config['period'], interval=config['interval'])
            
            if hist.empty:
                logger.warning(f"No historical data found for {ticker} with timeframe {timeframe}")
                all_history_data[timeframe] = {"error": "No historical data available"}
                continue
            
            # Format data for the frontend
            prices = hist['Close'].tolist()
            timestamps = hist.index.strftime('%Y-%m-%d %H:%M:%S').tolist()
            
            all_history_data[timeframe] = {
                "prices": prices,
                "timestamps": timestamps
            }
        
        logger.info(f"Successfully fetched all timeframes for {ticker}")
        return jsonify(all_history_data)
        
    except Exception as e:
        logger.error(f"Error fetching stock history for {ticker}: {str(e)}")
        return jsonify({"error": f"Failed to fetch stock history: {str(e)}"}), 500

# Frontend: get_stock_valuation
@app.route('/api/stock/<ticker>/valuation', methods=['GET'])
def get_stock_valuation(ticker):
    logger.info(f"Stock valuation requested for ticker: {ticker}")

    try:
        stock_financials = filter_stock_financials(ticker)
        if not stock_financials:
            return jsonify({"error": "Failed to fetch stock financials"}), 500
        return jsonify(stock_financials)

    except Exception as e:
        logger.error(f"Error fetching stock valuation for {ticker}: {str(e)}")
        return jsonify({"error": str(e)}), 500

def scrape_country_industry_data(stock_data: dict):
    try:
        # Get country and industry from the stock data
        country = stock_data.get('country', 'US')  # Default to US if not found
        industry = stock_data.get('industry', 'Technology')  # Default to Technology if not found
        
        with open('country_industry_data.json', 'r') as file:
            data = json.load(file)
            result = {
                'treasury_rate': data['countries'].get(country, {}).get('10y_treasury_rate', 0.05),
                'benchmark_etf': data['countries'].get(country, {}).get('benchmark_etf', 'SPY'),
                'benchmark_etf_return': data['countries'].get(country, {}).get('benchmark_etf_return', 0.05),
                'industry_rate': data['industries'].get(industry, {}).get('growth_rate', 0.05),
            }
        return result

    except Exception as e:
        logger.error(f"Error scraping country industry data: {str(e)}. Using default values.")
        
        # Default values
        return {
            'treasury_rate': 0.05,
            'benchmark_etf': 'SPY',
            'benchmark_etf_return': 0.05,
            'industry_rate': 0.05,
        }

def filter_stock_financials(ticker: str):
    try:
        stock = yf.Ticker(ticker)
        info = stock.info
        
        if not info:
            raise Exception("No stock information available")
            
        # Create initial stock data with basic info
        stock_data = {
            "ticker": ticker,
            "marketCap": info.get('marketCap', 0),
            "beta": info.get('beta', 0) or 0,
            "industry": info.get('industry', 'Technology'),
            "country": info.get('country', 'US'),
            "peRatio": info.get('trailingPE', 0) or 0,
            "peRatioForward": info.get('forwardPE', 0) or 0,
        }
        
        # Get country and industry data
        country_industry_data = scrape_country_industry_data(stock_data)
        
        # Update stock data with country/industry data
        stock_data.update(country_industry_data)
        
        # Get financial statements
        income_statement = stock.get_income_stmt(as_dict=True, freq='yearly')
        balance_sheet = stock.get_balance_sheet(as_dict=True, freq='yearly')
        cash_flow = stock.get_cashflow(as_dict=True, freq='yearly')
        
        # Update with financial data
        stock_data.update({
            "interestExpense": income_statement.get('InterestExpense', 0),
            "taxProvision": income_statement.get('TaxProvision', 0),
            "pretaxIncome": income_statement.get('PretaxIncome', 0),
            "dilutedAverageShares": income_statement.get('DilutedAverageShares', 0),
            "ebit": income_statement.get('EBIT', 0),
            "totalDebt": balance_sheet.get('TotalDebt', 0),
            "cashAndCashEquivalents": balance_sheet.get('CashAndCashEquivalents', 0),
            "investedCapital": balance_sheet.get('InvestedCapital', 0),
            "capex": cash_flow.get('CapitalExpenditure', 0),
            "changeInWorkingCapital": cash_flow.get('ChangeInWorkingCapital', 0),
        })

        # Calculate financial metrics
        stock_data['equityCost'] = dcf.calculate_cost_of_equity(
            (stock_data['treasury_rate']/100), 
            stock_data['beta'], 
            (stock_data['benchmark_etf_return']/100)
        )
        stock_data['debtCost'] = dcf.calculate_cost_of_debt(
            stock_data['interestExpense'], 
            stock_data['totalDebt']
        )
        stock_data['taxRate'] = dcf.calculate_tax_rate(
            stock_data['taxProvision'], 
            stock_data['pretaxIncome']
        )
        stock_data['netDebt'] = stock_data['totalDebt'] - stock_data['cashAndCashEquivalents']

        # Calculate FCF
        fcf = {}
        for timestamp, data in cash_flow.items():
            free_cash_flow = data.get('FreeCashFlow', None)
            if free_cash_flow and not pd.isna(free_cash_flow):
                year = timestamp.year
                fcf[year] = data['FreeCashFlow']

        # Calculate intrinsic value
        intrinsic_value = calculate_intrinsic_value_dcf(stock_data, fcf)
        stock_data.update(intrinsic_value)

        return stock_data
    
    except Exception as e:
        logger.error(f"Error fetching stock financials for {ticker}: {str(e)}")
        raise Exception(f"Failed to fetch stock financials: {str(e)}")

def calculate_intrinsic_value_dcf(data_source: dict, fcf_list):
    market_cap, total_debt, cost_of_equity, cost_of_debt, tax_rate, net_debt, shares_outstanding = data_source['market_cap'], data_source['total_debt'], data_source['cost_of_equity'], data_source['cost_of_debt'], data_source['tax_rate'], data_source['net_debt'], data_source['diluted_average_shares']

    # Calculate growth rates from FCF list
    fcf_list = list(fcf_list.values())
    future_fcf_list = dcf.estimate_future_fcf(fcf_list)

    # Load Data
    market_cap, total_debt, cost_of_equity, cost_of_debt, tax_rate, net_debt, shares_outstanding = data_source['market_cap'], data_source['total_debt'], data_source['cost_of_equity'], data_source['cost_of_debt'], data_source['tax_rate'], data_source['net_debt'], data_source['diluted_average_shares']
    ebit, invested_capital, capex, change_in_working_capital = data_source['ebit'], data_source['invested_capital'], data_source['capex'], data_source['change_in_working_capital']

    # estimate CAGR using dcf.calculator.cpp
    estimated_cagr = dcf.calculate_cagr(fcf_list)

    # estimate Reinvestment x ROIC using dcf.calculator.cpp
    estimated_reinvestment_x_roic = dcf.calculate_reinvestment_x_roic(ebit, tax_rate, invested_capital, capex, change_in_working_capital)

    # estimate industry return
    estimated_industry_rate = 0.05 # need to change to scraping my json data

    # calculate wacc for comparison with growth rates
    wacc = dcf.discount_rate(market_cap, total_debt, cost_of_equity, cost_of_debt, tax_rate)

    # lets estimate our chosen growth rate
    estimated_growth_rate = estimate_growth_rate(data_source, fcf_list)

    # Calculate WACC
    wacc = dcf.discount_rate(market_cap, total_debt, cost_of_equity, cost_of_debt, tax_rate)

    # Calculate Intrinsic Value
    equity_value = dcf.calculate_equity_value(future_fcf_list, wacc, estimated_growth_rate, net_debt)
    intrinsic_value = dcf.calculate_intrinsic_value(equity_value, shares_outstanding)

    data = {
        'wacc': wacc,
        'industryRate': estimated_industry_rate,
        'reinvestmentRate': estimated_reinvestment_x_roic,
        'cagr': estimated_cagr,
        'chosenGrowthRate': estimated_growth_rate,
        'intrinsicValue': intrinsic_value,
        'equityValue': equity_value,
    }
    
    return data

def estimate_growth_rate(data_source: dict, fcf_list):
    """
    Estimates a Growth Rate between the Calculated CAGR, Calculated Reinvestment x ROIC, 
    and Long-Term Industry Growth Rate for the particular company.
    
    The function uses a weighted approach that considers:
    1. Historical performance (CAGR)
    2. Company's reinvestment efficiency (Reinvestment x ROIC)
    3. Industry growth expectations
    4. Company's competitive position (beta)
    
    Returns a growth rate that is:
    - Conservative (below WACC)
    - Realistic (based on multiple factors)
    - Industry-appropriate
    """
    try:
        # Load Data
        market_cap = data_source.get('marketCap', 0)
        total_debt = data_source.get('totalDebt', 0)
        cost_of_equity = data_source.get('equityCost', 0)
        cost_of_debt = data_source.get('debtCost', 0)
        tax_rate = data_source.get('taxRate', 0)
        beta = data_source.get('beta', 1.0)
        industry_rate = data_source.get('industry_rate', 0.05)
        
        # Calculate WACC for reference
        wacc = dcf.discount_rate(market_cap, total_debt, cost_of_equity, cost_of_debt, tax_rate)
        
        # Calculate historical CAGR
        fcf_values = list(fcf_list.values())
        if len(fcf_values) >= 2:
            estimated_cagr = dcf.calculate_cagr(fcf_values)
        else:
            estimated_cagr = industry_rate * 0.8  # Conservative estimate if not enough data
            
        # Calculate Reinvestment x ROIC
        ebit = data_source.get('ebit', 0)
        invested_capital = data_source.get('investedCapital', 0)
        capex = data_source.get('capex', 0)
        change_in_working_capital = data_source.get('changeInWorkingCapital', 0)
        
        estimated_reinvestment_x_roic = dcf.calculate_reinvestment_x_roic(
            ebit, tax_rate, invested_capital, capex, change_in_working_capital
        )
        
        # Calculate weights based on data quality and company characteristics
        weights = {
            'cagr': 0.4 if len(fcf_values) >= 3 else 0.2,  # Higher weight if more historical data
            'reinvestment': 0.3,
            'industry': 0.3
        }
        
        # Adjust weights based on beta (risk)
        if beta > 1.5:
            weights['industry'] *= 0.8  # Reduce industry weight for high-beta companies
            weights['cagr'] *= 1.2     # Increase historical weight
        elif beta < 0.8:
            weights['industry'] *= 1.2  # Increase industry weight for low-beta companies
            weights['cagr'] *= 0.8     # Reduce historical weight
            
        # Calculate weighted growth rate
        weighted_growth = (
            weights['cagr'] * estimated_cagr +
            weights['reinvestment'] * estimated_reinvestment_x_roic +
            weights['industry'] * industry_rate
        )
        
        # Apply conservative constraints
        max_growth = min(wacc - 0.01, industry_rate * 1.2)  # Cap at WACC-1% or 120% of industry rate
        min_growth = max(0.01, industry_rate * 0.5)         # Floor at 1% or 50% of industry rate
        
        # Final growth rate with constraints
        final_growth = min(max(weighted_growth, min_growth), max_growth)
        
        logger.info(f"Growth rate estimation for {data_source.get('ticker', 'unknown')}:")
        logger.info(f"  - CAGR: {estimated_cagr:.2%}")
        logger.info(f"  - Reinvestment x ROIC: {estimated_reinvestment_x_roic:.2%}")
        logger.info(f"  - Industry Rate: {industry_rate:.2%}")
        logger.info(f"  - WACC: {wacc:.2%}")
        logger.info(f"  - Final Growth Rate: {final_growth:.2%}")
        
        return final_growth
        
    except Exception as e:
        logger.error(f"Error in estimate_growth_rate: {str(e)}")
        # Fallback to conservative estimate
        return min(wacc - 0.015, 0.03)  # 3% or WACC-1.5%, whichever is lower

if __name__ == '__main__':
    # For testing purposes
    if os.getenv('FLASK_ENV') == 'development':
        print("Running in development mode...")
        print("Available functions to test:")
        print("1. get_stock_details(ticker)")
        print("2. get_stock_history(ticker)")
        print("3. get_stock_valuation(ticker)")
        print("4. filter_stock_financials(ticker)")
        print("5. estimate_growth_rate(data_source, fcf_list)")
        print("\nType 'exit' to quit")
        
        while True:
            try:
                choice = input("\nEnter function number to test (1-5): ")
                
                if choice.lower() == 'exit':
                    break
                    
                if choice not in ['1', '2', '3', '4', '5']:
                    print("Invalid choice. Please enter a number between 1 and 5.")
                    continue
                
                ticker = input("Enter stock ticker: ").upper()
                
                if choice == '1':
                    # Test get_stock_details
                    result = fetch_stock_data(ticker)
                    print("\nStock Details:")
                    print(json.dumps(result, indent=2))
                
                elif choice == '2':
                    # Test get_stock_history
                    timeframe_configs = {
                        '1D': {'period': '1d', 'interval': '30m'},
                        '1W': {'period': '1wk', 'interval': '1d'},
                        '1M': {'period': '1mo', 'interval': '1d'},
                        '3M': {'period': '3mo', 'interval': '1wk'},
                        '1Y': {'period': '1y', 'interval': '1mo'}
                    }
                    
                    stock = yf.Ticker(ticker)
                    all_history_data = {}
                    
                    for timeframe, config in timeframe_configs.items():
                        hist = stock.history(period=config['period'], interval=config['interval'])
                        if not hist.empty:
                            prices = hist['Close'].tolist()
                            timestamps = hist.index.strftime('%Y-%m-%d %H:%M:%S').tolist()
                            all_history_data[timeframe] = {
                                "prices": prices,
                                "timestamps": timestamps
                            }
                    
                    print("\nStock History:")
                    print(json.dumps(all_history_data, indent=2))
                
                elif choice == '3':
                    # Test get_stock_valuation
                    result = filter_stock_financials(ticker)
                    print("\nStock Valuation:")
                    print(json.dumps(result, indent=2))
                
                elif choice == '4':
                    # Test filter_stock_financials
                    result = filter_stock_financials(ticker)
                    print("\nStock Financials:")
                    print(json.dumps(result, indent=2))
                
                elif choice == '5':
                    # Test estimate_growth_rate
                    stock_data = filter_stock_financials(ticker)
                    if stock_data:
                        stock = yf.Ticker(ticker)
                        cash_flow = stock.get_cashflow(as_dict=True, freq='yearly')
                        fcf = {}
                        for timestamp, data in cash_flow.items():
                            free_cash_flow = data.get('FreeCashFlow', None)
                            if free_cash_flow and not pd.isna(free_cash_flow):
                                year = timestamp.year
                                fcf[year] = data['FreeCashFlow']
                        
                        growth_rate = estimate_growth_rate(stock_data, fcf)
                        print("\nEstimated Growth Rate:")
                        print(f"{growth_rate:.2%}")
                
            except Exception as e:
                print(f"Error: {str(e)}")
                continue
    
    # For production
    else:
        app.run(debug=False)