from flask import Flask, request, render_template
from datetime import datetime
import os
import yahoo_fin.stock_info as si
import pandas as pd
import matplotlib.pyplot as plt

app = Flask(__name__)
app.secret_key = 'owadio'

def scrape_time():
    pass

def scrape_stock_info(ticker: str):
    # si.get_financials
    # si.get_quote_table
    stock_data = {}
    stock_data['stock_ticker'] = ticker
    stock_data['stock_live_price'] = si.get_live_price(ticker)
    stock_data['stock_market_status'] = si.get_live_price(ticker)

    return stock_data

def scrape_stock_price(ticker: str):
    # si.get_data
    pass

def scrape_sp500_price(tickers: list):
    # si.get_data
    # tickers_sp500
    pass

def discounted_cash_flow_calculator(stock_data):
    pass

@app.route('/', methods = ['GET', 'POST'])
def home():
    if request.method == 'POST':
        stock_ticker = request.form.get('ticker')
        stock_ticker = stock_ticker.upper()
        stock_data = scrape_stock_info(stock_ticker)
        print(stock_data)
    return render_template('home.html')

if __name__ == '__main__':
    app.run(debug=True)