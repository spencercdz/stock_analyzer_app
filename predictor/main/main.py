from flask import Flask, request, render_template
from datetime import datetime
import os
import yfinance as yf
import pandas as pd
import matplotlib.pyplot as plt
import dcf_calculator as dcf

app = Flask(__name__, template_folder=os.path.join(os.path.dirname(__file__), '..', 'templates'))
app.secret_key = 'owadio'

@app.route('/', methods = ['GET', 'POST'])
def home():
    if request.method == 'POST':
        stock_ticker = request.form.get('ticker')
        stock_ticker = stock_ticker.upper()
        stock_info, stock_financials = scrape_stock_details(stock_ticker)
    return render_template('home.html')

def scrape_stock_details(ticker: str):
    stock_ticker = yf.Ticker(ticker)

    filtered_stock_info = filter_stock_summary(stock_ticker.info)
    filtered_stock_financials, fcf = filter_stock_financials(stock_ticker)
    print(filtered_stock_financials)
    print(fcf)

    return filtered_stock_info, filtered_stock_financials

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
        'longBusinessSummary': 'Summary'
    }
    return {value: stock[key] for key, value in keys_map.items() if key in stock}

def filter_stock_financials(ticker: str):
    keys_income_statement = {
        'InterestExpense': 'interest_expense',
        'TaxProvision' : 'tax_provision',
        'PretaxIncome': 'pretax_income',
        'DilutedAverageShares': 'diluted_average_shares'
    }

    keys_balance_sheet = {
        'TotalDebt': 'total_debt',
        'CashAndCashEquivalents': 'cash_and_cash_equivalents',
    }

    income_statement = ticker.get_income_stmt(as_dict=True, freq='yearly')
    income_statement_key = next(iter(income_statement))

    balance_sheet = ticker.get_balance_sheet(as_dict=True, freq='yearly')
    balance_sheet_key = next(iter(balance_sheet))

    cash_flow = ticker.get_cashflow(as_dict=True, freq='yearly')
    
    results = {value: income_statement[income_statement_key][key] for key, value in keys_income_statement.items() if key in income_statement[income_statement_key]}
    results.update({value: balance_sheet[balance_sheet_key][key] for key, value in keys_balance_sheet.items() if key in balance_sheet[balance_sheet_key]})
    
    fcf = {}
    for timestamp, data in cash_flow.items():
        year = timestamp.year
        fcf[year] = data['FreeCashFlow']

    return results, fcf

def generate_fcf_over_years(ticker):
    pass

def calculate_intrinsic_value_dcf(data_source: dict):
    market_cap, total_debt, cost_equity, cost_debt, tax_rate, net_debt, shares_outstanding = data_source['market_cap'], data_source['total_debt'], data_source['cost_equity'], data_source['cost_debt'], data_source['tax_rate'], data_source['net_debt'], data_source['shares_outstanding']
    fcf_list = generate_fcf_over_years(data_source['ticker'])

    wacc = dcf.discount_rate(market_cap, total_debt, cost_equity, cost_debt, tax_rate)
    cagr = dcf.calculate_cagr(fcf_list)
    future_fcf_list = dcf.estimate_future_fcf(fcf_list)
    equity_value = dcf.calculate_equity_value(future_fcf_list, wacc, cagr, net_debt)
    intrinsic_value = dcf.calculate_intrinsic_value(equity_value, shares_outstanding)
    return intrinsic_value

def scrape_stock_price(ticker: str):
    # stock_data.history(period="5y")
    pass

def scrape_sp500_price(tickers: list):
    pass

if __name__ == '__main__':
    app.run(debug=True)