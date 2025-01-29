from flask import Flask, request, render_template
from datetime import datetime
import os
import yfinance as yf
import pandas as pd
import matplotlib.pyplot as plt
import dcf_calculator as dcf

app = Flask(__name__)
app.secret_key = 'owadio'

def scrape_stock_details(ticker: str):
    stock_data = yf.Ticker(ticker)
    stock_info = stock_data.info
    filtered_stock_info = filter_stock_info(stock_info)
    #stock_cash_flow = stock_data.get_cashflow(proxy=None, as_dict=True, pretty=False, freq='yearly')


    #for key,value in filtered_stock_info.items():
        #print(f"{key}: {value}")
    #print(stock_cash_flow)
    pass

def filter_stock_info(stock: dict):
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

def dcf_valuation():
    # total_debt, cost_of_equity, cost_of_debt, tax_rate = 
    #
    #
    #
    #
    pass

def scrape_stock_price(ticker: str):
    # stock_data.history(period="5y")
    pass

def scrape_sp500_price(tickers: list):
    pass

def discounted_cash_flow_calculator(stock_data):
    pass

@app.route('/', methods = ['GET', 'POST'])
def home():
    if request.method == 'POST':
        stock_ticker = request.form.get('ticker')
        stock_ticker = stock_ticker.upper()
        stock_data = scrape_stock_details(stock_ticker)
        print(stock_data)
    return render_template('home.html')

if __name__ == '__main__':
    app.run(debug=True)