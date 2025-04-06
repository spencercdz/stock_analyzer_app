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
    try:
        # Check if the data is already in the cache
        if ticker in cache and (time.time() - cache[ticker]['timestamp']) < 300:  # 5 minutes cache
            logger.info(f"Returning cached data for {ticker}")
            return jsonify(cache[ticker]['data'])

        # Fetch data from yfinance
        stock_data = fetch_stock_data(ticker)

        # Error handling
        if stock_data is None:
            logger.error(f"No stock data found for ticker: {ticker}")
            return jsonify({"error": "Stock data not found"}), 404

        return stock_data

    except Exception as e:
        logger.error(f"Error in get_stock_details for {ticker}: {str(e)}")
        return jsonify({"error": f"Failed to fetch stock details: {str(e)}"}), 500

def fetch_stock_data(ticker):
    try:
        stock = yf.Ticker(ticker)
        info = stock.info
        
        if not info or 'symbol' not in info:
            logger.error(f"No data found for ticker: {ticker}")
            return None
        
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
        return None

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
            logger.error(f"No financial data found for ticker: {ticker}")
            return jsonify({"error": "Failed to fetch stock financials"}), 500
            
        logger.info(f"Successfully calculated valuation for {ticker}")
        return jsonify(stock_financials)

    except Exception as e:
        logger.error(f"Error fetching stock valuation for {ticker}: {str(e)}")
        return jsonify({"error": str(e)}), 500

def scrape_country_industry_data(ticker):
    """
    Scrapes country and industry data for a given ticker.
    
    Args:
        ticker (str): Stock ticker symbol
        
    Returns:
        dict: Dictionary containing:
            - country (str): Country name
            - industry (str): Industry name
            - treasuryRate (float): 10-year treasury rate for the country
            - benchmarkEtf (str): Benchmark ETF for the country
            - benchmarkEtfReturn (float): Expected return of the benchmark ETF
            - industryRate (float): Expected growth rate for the industry
    """
    try:
        # Get the directory of the current script
        current_dir = os.path.dirname(os.path.abspath(__file__))
        data_file = os.path.join(current_dir, 'country_industry_data.json')
        
        with open(data_file, 'r') as file:
            data = json.load(file)
            
        # Get stock info to determine country and industry
        stock = yf.Ticker(ticker)
        info = stock.info
        
        # Get country and industry from stock info
        country = info.get('country', 'United States')  # Default to US if not found
        industry = info.get('industry', 'Technology')   # Default to Technology if not found
        
        # Validate country and industry against our data
        if country not in data['countries']:
            country = 'United States'  # Default to US if country not in our data
        if industry not in data['industries']:
            industry = 'Technology'    # Default to Technology if industry not in our data
            
        # Get country-specific data
        country_data = data['countries'].get(country, data['countries']['United States'])
        industry_data = data['industries'].get(industry, data['industries']['Technology'])
        
        # Convert percentage values to decimals
        treasury_rate = country_data.get('10y_treasury_rate', 4.4970) / 100
        benchmark_etf_return = country_data.get('benchmark_etf_return', 7.5) / 100
        industry_rate = industry_data.get('growth_rate', 5.0) / 100
        
        result = {
            'country': country,
            'industry': industry,
            'treasuryRate': treasury_rate,
            'benchmarkEtf': country_data.get('benchmark_etf', 'SPY'),
            'benchmarkEtfReturn': benchmark_etf_return,
            'industryRate': industry_rate
        }
        
        logger.info(f"Country/Industry data for {ticker}:")
        logger.info(f"  Country: {country}")
        logger.info(f"  Industry: {industry}")
        logger.info(f"  Treasury Rate: {treasury_rate:.4f}")
        logger.info(f"  Benchmark ETF: {result['benchmarkEtf']}")
        logger.info(f"  Benchmark Return: {benchmark_etf_return:.4f}")
        logger.info(f"  Industry Rate: {industry_rate:.4f}")
        
        return result
        
    except Exception as e:
        logger.error(f"Error scraping country industry data: {str(e)}. Using default values.")
        # Return default US values
        return {
            'country': 'United States',
            'industry': 'Technology',
            'treasuryRate': 0.04497,  # 4.497%
            'benchmarkEtf': 'SPY',
            'benchmarkEtfReturn': 0.075,  # 7.5%
            'industryRate': 0.05  # 5%
        }

def filter_stock_financials(ticker: str) -> dict:
    """
    Retrieves and processes financial data for a given stock ticker.
    
    Args:
        ticker (str): Stock ticker symbol (e.g., 'AAPL').
        
    Returns:
        dict: Dictionary containing processed financial data including:
            - Basic stock information (ticker, market cap, beta, etc.)
            - Financial metrics (P/E ratios, debt, cash, etc.)
            - Calculated values (cost of equity, cost of debt, etc.)
            - Valuation metrics (WACC, growth rates, intrinsic value)
            
    Raises:
        Exception: If stock information is not available or if there's an error processing the data.
    """
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
        country_data = scrape_country_industry_data(ticker)
        
        # Update stock data with country/industry data
        stock_data.update({
            "country": country_data['country'],
            "industry": country_data['industry'],
            "treasuryRate": country_data['treasuryRate'],
            "benchmarkEtf": country_data['benchmarkEtf'],
            "benchmarkEtfReturn": country_data['benchmarkEtfReturn'],
            "industryRate": country_data['industryRate']
        })
        
        # Get financial statements
        try:
            income_stmt = stock.financials
            balance_sheet = stock.balance_sheet
            cash_flow = stock.cashflow
            
            # Get the most recent year's data
            if not income_stmt.empty:
                stock_data.update({
                    "interestExpense": income_stmt.loc['Interest Expense'].iloc[0] if 'Interest Expense' in income_stmt.index else 0,
                    "taxProvision": income_stmt.loc['Income Tax Expense'].iloc[0] if 'Income Tax Expense' in income_stmt.index else 0,
                    "pretaxIncome": income_stmt.loc['Pretax Income'].iloc[0] if 'Pretax Income' in income_stmt.index else 0,
                    "ebit": income_stmt.loc['EBIT'].iloc[0] if 'EBIT' in income_stmt.index else 0,
                })
            
            if not balance_sheet.empty:
                stock_data.update({
                    "totalDebt": balance_sheet.loc['Total Debt'].iloc[0] if 'Total Debt' in balance_sheet.index else 0,
                    "cashAndCashEquivalents": balance_sheet.loc['Cash And Cash Equivalents'].iloc[0] if 'Cash And Cash Equivalents' in balance_sheet.index else 0,
                    "investedCapital": balance_sheet.loc['Total Assets'].iloc[0] - balance_sheet.loc['Total Current Liabilities'].iloc[0] if 'Total Assets' in balance_sheet.index and 'Total Current Liabilities' in balance_sheet.index else 0,
                    "dilutedAverageShares": info.get('sharesOutstanding', 0),
                })
            
            if not cash_flow.empty:
                stock_data.update({
                    "capex": abs(cash_flow.loc['Capital Expenditure'].iloc[0]) if 'Capital Expenditure' in cash_flow.index else 0,
                    "changeInWorkingCapital": cash_flow.loc['Change In Working Capital'].iloc[0] if 'Change In Working Capital' in cash_flow.index else 0,
                })
                
                # Calculate FCF
                fcf = {}
                for year in cash_flow.columns:
                    operating_cash_flow = cash_flow.loc['Operating Cash Flow', year] if 'Operating Cash Flow' in cash_flow.index else 0
                    capital_expenditure = abs(cash_flow.loc['Capital Expenditure', year]) if 'Capital Expenditure' in cash_flow.index else 0
                    free_cash_flow = operating_cash_flow - capital_expenditure
                    if not pd.isna(free_cash_flow):
                        fcf[year.year] = free_cash_flow
        except Exception as e:
            logger.error(f"Error processing financial statements: {str(e)}")
            # Set default values if financial statements can't be processed
            stock_data.update({
                "interestExpense": 0,
                "taxProvision": 0,
                "pretaxIncome": 0,
                "ebit": 0,
                "totalDebt": 0,
                "cashAndCashEquivalents": 0,
                "investedCapital": 0,
                "dilutedAverageShares": info.get('sharesOutstanding', 0),
                "capex": 0,
                "changeInWorkingCapital": 0,
            })
            fcf = {}

        # Calculate financial metrics
        stock_data['equityCost'] = dcf.calculate_cost_of_equity(
            stock_data['treasuryRate'], 
            stock_data['beta'], 
            stock_data['benchmarkEtfReturn']
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

        # Calculate intrinsic value
        intrinsic_value = calculate_intrinsic_value_dcf(stock_data, fcf)
        stock_data.update(intrinsic_value)

        return stock_data
    
    except Exception as e:
        logger.error(f"Error fetching stock financials for {ticker}: {str(e)}")
        raise Exception(f"Failed to fetch stock financials: {str(e)}")

def calculate_intrinsic_value_dcf(data_source: dict, fcf_list: dict) -> dict:
    """
    Calculates the intrinsic value of a stock using the Discounted Cash Flow (DCF) method.
    """
    try:
        # Extract and validate data
        def safe_get(key, default=0):
            value = data_source.get(key, default)
            try:
                value = float(value)
                return value if not np.isnan(value) and not np.isinf(value) else default
            except (ValueError, TypeError):
                return default

        # Extract and validate all required values
        market_cap = safe_get('marketCap')
        total_debt = safe_get('totalDebt')
        ebit = safe_get('ebit')
        tax_rate = safe_get('taxRate')
        net_debt = safe_get('netDebt')
        shares_outstanding = safe_get('dilutedAverageShares')
        invested_capital = safe_get('investedCapital')
        capex = safe_get('capex')
        change_in_working_capital = safe_get('changeInWorkingCapital')
        treasury_rate = safe_get('treasuryRate', 0.04497)
        benchmark_etf_return = safe_get('benchmarkEtfReturn', 0.075)
        industry_rate = safe_get('industryRate', 0.05)
        beta = safe_get('beta', 1.0)
        interest_expense = safe_get('interestExpense', 0)

        # Log input values for debugging
        logger.info("Input Values:")
        logger.info(f"  Market Cap: {market_cap:.2f}")
        logger.info(f"  Total Debt: {total_debt:.2f}")
        logger.info(f"  EBIT: {ebit:.2f}")
        logger.info(f"  Tax Rate: {tax_rate:.4f}")
        logger.info(f"  Net Debt: {net_debt:.2f}")
        logger.info(f"  Shares Outstanding: {shares_outstanding:.2f}")
        logger.info(f"  Invested Capital: {invested_capital:.2f}")
        logger.info(f"  Capex: {capex:.2f}")
        logger.info(f"  Change in WC: {change_in_working_capital:.2f}")
        logger.info(f"  Treasury Rate: {treasury_rate:.4f}")
        logger.info(f"  Benchmark Return: {benchmark_etf_return:.4f}")
        logger.info(f"  Industry Rate: {industry_rate:.4f}")
        logger.info(f"  Beta: {beta:.2f}")
        logger.info(f"  Interest Expense: {interest_expense:.2f}")

        # Calculate cost of equity using CAPM
        try:
            if total_debt <= 0:
                total_debt = 1
            if interest_expense <= 0:
                interest_expense = total_debt * 0.05  # Assume 5% interest rate
            
            cost_of_equity = dcf.calculate_cost_of_equity(treasury_rate, beta, benchmark_etf_return)
            cost_of_equity = max(min(cost_of_equity, 0.5), 0.01)  # Constrain between 1% and 50%
            logger.info(f"Cost of Equity: {cost_of_equity:.4f}")
        except Exception as e:
            logger.error(f"Error calculating cost of equity: {str(e)}")
            cost_of_equity = 0.1  # Default cost of equity

        # Calculate cost of debt
        try:
            cost_of_debt = dcf.calculate_cost_of_debt(interest_expense, total_debt)
            cost_of_debt = max(min(cost_of_debt, 0.5), 0.01)  # Constrain between 1% and 50%
            logger.info(f"Cost of Debt: {cost_of_debt:.4f}")
        except Exception as e:
            logger.error(f"Error calculating cost of debt: {str(e)}")
            cost_of_debt = 0.05  # Default cost of debt

        # Calculate WACC
        try:
            if market_cap <= 0:
                market_cap = 1
            if total_debt <= 0:
                total_debt = 1
            if tax_rate < 0 or tax_rate > 1:
                tax_rate = 0.21
                
            wacc = dcf.discount_rate(market_cap, total_debt, cost_of_equity, cost_of_debt, tax_rate)
            wacc = max(min(wacc, 0.5), 0.01)  # Constrain between 1% and 50%
            logger.info(f"WACC: {wacc:.4f}")
        except Exception as e:
            logger.error(f"Error calculating WACC: {str(e)}")
            wacc = 0.1  # Default WACC

        # Handle FCF data
        fcf_values = []
        if isinstance(fcf_list, dict):
            fcf_values = [safe_get(v) for v in fcf_list.values()]
        elif isinstance(fcf_list, list):
            fcf_values = [safe_get(v) for v in fcf_list]

        # Ensure we have valid FCF values
        if not fcf_values or all(v == 0 for v in fcf_values):
            fcf_values = [0]
        logger.info(f"FCF Values: {fcf_values}")

        # Calculate CAGR
        try:
            if len(fcf_values) >= 2 and all(v > 0 for v in fcf_values):
                estimated_cagr = dcf.calculate_cagr(fcf_values)
            else:
                estimated_cagr = industry_rate
            estimated_cagr = max(min(estimated_cagr, 0.5), -0.5)  # Constrain between -50% and 50%
            logger.info(f"CAGR: {estimated_cagr:.4f}")
        except Exception as e:
            logger.error(f"Error calculating CAGR: {str(e)}")
            estimated_cagr = industry_rate

        # Calculate reinvestment rate
        try:
            if invested_capital > 0 and ebit > 0:
                estimated_reinvestment_x_roic = dcf.calculate_reinvestment_x_roic(
                    ebit, tax_rate, invested_capital, capex, change_in_working_capital
                )
            else:
                estimated_reinvestment_x_roic = 0.0
            estimated_reinvestment_x_roic = max(min(estimated_reinvestment_x_roic, 0.5), -0.5)
            logger.info(f"Reinvestment Rate: {estimated_reinvestment_x_roic:.4f}")
        except Exception as e:
            logger.error(f"Error calculating reinvestment rate: {str(e)}")
            estimated_reinvestment_x_roic = 0.0

        # Calculate growth rate
        try:
            # Weighted average of CAGR and reinvestment rate
            estimated_growth_rate = (0.7 * estimated_cagr) + (0.3 * estimated_reinvestment_x_roic)
            estimated_growth_rate = max(min(estimated_growth_rate, wacc - 0.01), 0.01)
            logger.info(f"Growth Rate: {estimated_growth_rate:.4f}")
        except Exception as e:
            logger.error(f"Error calculating growth rate: {str(e)}")
            estimated_growth_rate = min(wacc - 0.01, 0.03)

        # Calculate future FCF
        try:
            if fcf_values and fcf_values[-1] > 0:
                future_fcf_list = dcf.estimate_future_fcf(fcf_values)
            else:
                future_fcf_list = [0]
            logger.info(f"Future FCF List: {future_fcf_list}")
        except Exception as e:
            logger.error(f"Error calculating future FCF: {str(e)}")
            future_fcf_list = [0]

        # Calculate equity value
        try:
            if future_fcf_list and wacc > estimated_growth_rate:
                equity_value = dcf.calculate_equity_value(future_fcf_list, wacc, estimated_growth_rate, net_debt)
            else:
                equity_value = market_cap
            equity_value = max(min(equity_value, 1e15), -1e15)
            logger.info(f"Equity Value: {equity_value:.2f}")
        except Exception as e:
            logger.error(f"Error calculating equity value: {str(e)}")
            equity_value = market_cap

        # Calculate intrinsic value
        try:
            if shares_outstanding > 0:
                intrinsic_value = dcf.calculate_intrinsic_value(equity_value, shares_outstanding)
            else:
                intrinsic_value = 0.0
            intrinsic_value = max(min(intrinsic_value, 1e6), -1e6)
            logger.info(f"Intrinsic Value: {intrinsic_value:.2f}")
        except Exception as e:
            logger.error(f"Error calculating intrinsic value: {str(e)}")
            intrinsic_value = 0.0

        # Prepare response
        data = {
            'wacc': wacc,
            'industryRate': industry_rate,
            'reinvestmentRate': estimated_reinvestment_x_roic,
            'cagr': estimated_cagr,
            'chosenGrowthRate': estimated_growth_rate,
            'intrinsicValue': intrinsic_value,
            'equityValue': equity_value,
        }

        # Log results
        logger.info("DCF Calculation Results:")
        for key, value in data.items():
            logger.info(f"  {key}: {value:.4f}")

        return data

    except Exception as e:
        logger.error(f"Error in calculate_intrinsic_value_dcf: {str(e)}")
        return {
            'wacc': 0.1,
            'industryRate': 0.05,
            'reinvestmentRate': 0.0,
            'cagr': 0.0,
            'chosenGrowthRate': 0.03,
            'intrinsicValue': 0.0,
            'equityValue': 0.0,
        }

def estimate_growth_rate(data_source: dict, fcf_list: dict) -> float:
    """
    Estimates the growth rate for a company using multiple factors.
    
    Args:
        data_source (dict): Dictionary containing company financial data.
        fcf_list (dict): Dictionary of historical free cash flows by year.
        
    Returns:
        float: Estimated growth rate as a decimal (e.g., 0.05 for 5%).
        
    Note:
        The growth rate is estimated using a weighted approach considering:
        1. Historical performance (CAGR)
        2. Company's reinvestment efficiency (Reinvestment x ROIC)
        3. Industry growth expectations
        4. Company's competitive position (beta)
        
        The final growth rate is constrained to be:
        - Below the company's WACC
        - Realistic based on industry standards
        - Conservative for high-risk companies
    """
    try:
        # Load Data using consistent camelCase keys
        market_cap = data_source.get('marketCap', 0)
        total_debt = data_source.get('totalDebt', 0)
        cost_of_equity = data_source.get('equityCost', 0)
        cost_of_debt = data_source.get('debtCost', 0)
        tax_rate = data_source.get('taxRate', 0)
        beta = data_source.get('beta', 1.0)
        industry_rate = data_source.get('industryRate', 0.05)
        
        # Calculate WACC for reference
        wacc = dcf.discount_rate(market_cap, total_debt, cost_of_equity, cost_of_debt, tax_rate)
        
        # Handle FCF data - convert to list if it's a dictionary
        if isinstance(fcf_list, dict):
            fcf_values = list(fcf_list.values())
        else:
            fcf_values = fcf_list if isinstance(fcf_list, list) else []
            
        # Calculate historical CAGR
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
        
        logger.info(f"Growth rate estimation:")
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