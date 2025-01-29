from flask import Flask, request, render_template
from datetime import datetime
import os
import yfinance as yf
import pandas as pd
import matplotlib.pyplot as plt
#import dcf_calculator (have not set up module yet)

app = Flask(__name__)
app.secret_key = 'owadio'

def scrape_time():
    pass

def scrape_stock_details(ticker: str):
    stock_data = yf.Ticker(ticker)
    stock_info = stock_data.info
    filtered_stock_info = filter_stock_info(stock_info)
    stock_cash_flow = stock_data.get_cashflow(proxy=None, as_dict=True, pretty=False, freq='yearly')


    #for key,value in filtered_stock_info.items():
        #print(f"{key}: {value}")
    print(stock_cash_flow)
    pass

def filter_stock_info(stock: dict):
    filtered_info = {}
    filtered_info['Name'] = stock['longName']
    filtered_info['Symbol'] = stock['symbol']
    filtered_info['Current Price'] = stock['currentPrice']
    filtered_info['Currency'] = stock['currency']
    filtered_info['Market Cap'] = stock['marketCap']
    filtered_info['Volume'] = stock['volume']
    filtered_info['Day High'] = stock['dayHigh']
    filtered_info['Day Low'] = stock['dayLow']
    filtered_info['Trailing PE'] = stock['trailingPE']
    filtered_info['Trailing EPS'] = stock['trailingEps']
    filtered_info['52 Week High'] = stock['fiftyTwoWeekHigh']
    filtered_info['52 Week Low'] = stock['fiftyTwoWeekLow']
    filtered_info['Summary'] = stock['longBusinessSummary']
    return filtered_info

def dcf_valuation():
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