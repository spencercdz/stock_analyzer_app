# main.py

from flask_cors import CORS
from flask import Flask, request, render_template, jsonify
from datetime import datetime
import os
import yfinance as yf
import pandas as pd
import matplotlib.pyplot as plt
import dcf_calculator as dcf
import numpy as np
import json
import time
import requests

app = Flask(__name__, template_folder=os.path.join(os.path.dirname(__file__), '..', 'templates'))
app.secret_key = os.getenv('FLASK_SECRET_KEY', 'default_secret_key')
CORS(app)

# Simple cache to store stock data
cache = {}

@app.route('/', methods=['GET'])
def index():
    return {"message": "Flask backend is running"}

@app.route('/api/stock/<ticker>', methods=['GET'])
def get_stock_details(ticker):
    # Check if the data is already in the cache
    if ticker in cache:
        return jsonify(cache[ticker])

    # Fetch data from yfinance
    stock_data = fetch_stock_data(ticker)

    # Error handling
    if stock_data is None:
        return jsonify({"error": "Stock data not found"}), 404
    
    # Store the result in the cache
    cache[ticker] = stock_data
    return jsonify(stock_data)

def fetch_stock_data(ticker):
    max_retries = 5
    for attempt in range(max_retries):
        try:
            # Introduce a delay to avoid hitting the rate limit
            time.sleep(2)  # Adjust the delay as needed

            # Fetch stock info using requests
            url = f'https://query1.finance.yahoo.com/v7/finance/quote?symbols={ticker}'
            response = requests.get(url)
            response.raise_for_status()  # Raise an error for bad responses

            stock_data = response.json()
            print(stock_data)  # Debugging output

            # Process the stock data as needed
            if 'quoteResponse' in stock_data and stock_data['quoteResponse']['result']:
                filtered_stock_info = filter_stock_summary(stock_data['quoteResponse']['result'][0])

                # Fetch financials (you may need to adjust this based on your requirements)
                filtered_stock_financials, fcf = filter_stock_financials(ticker, filtered_stock_info)

                # Calculate intrinsic value
                intrinsic_value = calculate_intrinsic_value_dcf(filtered_stock_financials, fcf)

                return filtered_stock_info, filtered_stock_financials, fcf
            else:
                print(f"No data found for ticker: {ticker}")
                return None
        except requests.exceptions.HTTPError as e:
            if response.status_code == 401:  # Unauthorized
                print(f"Unauthorized access for ticker {ticker}: {e}")
                return None
            print(f"Attempt {attempt + 1} failed: {e}")
            if "Too Many Requests" in str(e):
                # Exponential backoff
                time.sleep(2 ** attempt)  # Wait longer with each attempt
            else:
                raise  # Raise other exceptions immediately
    return None  # Return None if all attempts fail

def scrape_country_industry_data():
    Country = 'United States'
    Industry = 'Banking'
    with open('country_industry_data.json', 'r') as file:
        data = json.load(file)
        treasury_rate = data['countries'][Country]['10y_treasury_rate']
        benchmark_etf = data['countries'][Country]['benchmark_etf']
        benchmark_etf_return = data['countries'][Country]['benchmark_etf_return']
        industry_rate = data['industries'][Industry]['growth_rate']
    print(treasury_rate, benchmark_etf, benchmark_etf_return, industry_rate)
    pass


def filter_stock_summary(stock: dict):
    keys_map = {
        'longName': 'Name',
        'symbol': 'Symbol',
        'currentPrice': 'Current Price',
        'currency': 'Currency',
        'marketCap': 'Market Cap',
        'volume': 'Volume',
        'dayHigh': 'Day High',
        'dayLow': 'Day Low',
        'trailingPE': 'Trailing PE',
        'trailingEps': 'Trailing EPS',
        'fiftyTwoWeekHigh': '52 Week High',
        'fiftyTwoWeekLow': '52 Week Low',
        'longBusinessSummary': 'Summary',
        'beta': 'Beta',
        'country' : 'Country',
    }
    return {value: stock[key] for key, value in keys_map.items() if key in stock}

def filter_stock_financials(ticker: str, filtered_stock_info: dict):
    keys_income_statement = {
        'InterestExpense': 'interest_expense',
        'TaxProvision' : 'tax_provision',
        'PretaxIncome': 'pretax_income',
        'DilutedAverageShares': 'diluted_average_shares',
        'EBIT': 'ebit'
    }

    keys_balance_sheet = {
        'TotalDebt': 'total_debt',
        'CashAndCashEquivalents': 'cash_and_cash_equivalents',
        'InvestedCapital': 'invested_capital'
    }

    keys_cash_flow = {
        'CapitalExpenditure': 'capex',
        'ChangeInWorkingCapital': 'change_in_working_capital'
    }

    # add in income statement variables
    income_statement = ticker.get_income_stmt(as_dict=True, freq='yearly')
    income_statement_key = next(iter(income_statement))
    print(income_statement[income_statement_key])
    results = {value: income_statement[income_statement_key][key] for key, value in keys_income_statement.items() if key in income_statement[income_statement_key]}

    # add in balance_sheet variables
    balance_sheet = ticker.get_balance_sheet(as_dict=True, freq='yearly')
    balance_sheet_key = next(iter(balance_sheet))
    results.update({value: balance_sheet[balance_sheet_key][key] for key, value in keys_balance_sheet.items() if key in balance_sheet[balance_sheet_key]})

    # add in cash_flow variables
    cash_flow = ticker.get_cashflow(as_dict=True, freq='yearly')
    cash_flow_key = next(iter(cash_flow))
    results.update({value: cash_flow[cash_flow_key][key] for key, value in keys_cash_flow.items() if key in cash_flow[cash_flow_key]})

    # add in stock info
    results['market_cap'] = filtered_stock_info['Market Cap']
    results['beta'] = filtered_stock_info['Beta']

    # perform and add some calculations
    results['cost_of_equity'] = dcf.calculate_cost_of_equity((4.0/100), results['beta'], (9.5/100)) # rfr = 4, mr = 9.5. for now we fix the Treasury Rate and Market Return, have to make a separate scraper to get these values for the specific country the company is in
    results['cost_of_debt'] = dcf.calculate_cost_of_debt(results['interest_expense'], results['total_debt'])
    results['tax_rate'] = dcf.calculate_tax_rate(results['tax_provision'], results['pretax_income'])
    results['net_debt'] = results['total_debt'] - results['cash_and_cash_equivalents']

    # calculate fcf from cash flow list
    fcf = {}
    for timestamp, data in cash_flow.items():
        free_cash_flow = data.get('FreeCashFlow', None)
        if free_cash_flow and not pd.isna(free_cash_flow):
            year = timestamp.year
            fcf[year] = data['FreeCashFlow']
    return results, fcf

def calculate_intrinsic_value_dcf(data_source: dict, fcf_list):#
    market_cap, total_debt, cost_of_equity, cost_of_debt, tax_rate, net_debt, shares_outstanding = data_source['market_cap'], data_source['total_debt'], data_source['cost_of_equity'], data_source['cost_of_debt'], data_source['tax_rate'], data_source['net_debt'], data_source['diluted_average_shares']

    # Calculate growth rates from FCF list
    fcf_list = list(fcf_list.values())
    future_fcf_list = dcf.estimate_future_fcf(fcf_list)

    # lets estimate our chosen growth rate
    chosen_growth_rate = estimate_growth_rate(data_source, fcf_list)

    # Calculate WACC
    wacc = dcf.discount_rate(market_cap, total_debt, cost_of_equity, cost_of_debt, tax_rate)

    equity_value = dcf.calculate_equity_value(future_fcf_list, wacc, chosen_growth_rate, net_debt)
    intrinsic_value = dcf.calculate_intrinsic_value(equity_value, shares_outstanding)
    print(chosen_growth_rate)
    print(wacc)
    print(intrinsic_value)
    return intrinsic_value

def estimate_growth_rate(data_source: dict, fcf_list):
    """
    Estimates a Growth Rate between the Calculated CAGR, Calculated Reinvestment x ROIC, or Long-Term Industry Growth Rate for the particular company

    First, get all 3 rates. Then 
    """
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

    # calculate mean, median and std for testing
    rates_list = [estimated_cagr, estimated_reinvestment_x_roic, estimated_industry_rate]
    rates_mean, rates_median, rates_std = np.mean(rates_list), np.median(rates_list), np.std(rates_list)
    
    # Filter out extreme outliers
    filtered_rates_list = [
        rate for rate in rates_list 
        if abs(rate - rates_mean) < (2 * rates_std)  # Remove rates that deviate more than 2 std devs
    ]
    
    # Ensure the filtered list isn't empty, and that the rates are smaller than WACC. Otherwise, use a fallback rate that is below WACC (e.g., 3% or WACC - a small buffer)
    if not filtered_rates_list:
        fallback_rate = max(wacc - 0.015, 0.03)
        return fallback_rate
    
    # Use median since there is likely variability in growth rates, as it is more robust to outliers
    estimated_growth_rate = np.median(filtered_rates_list)
    
    # If the chosen growth rate is still lower than WACC, adjust WACC (safeguard)
    if estimated_growth_rate < wacc:
        estimated_growth_rate = max(estimated_growth_rate, wacc - 0.015)
    
    return estimated_growth_rate

def scrape_stock_price(ticker: str):
    # stock_data.history(period="5y")
    pass

def scrape_sp500_price(tickers: list):
    pass

if __name__ == '__main__':
    app.run(debug=True)