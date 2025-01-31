from flask import Flask, request, render_template
from datetime import datetime
import os
import yfinance as yf
import pandas as pd
import matplotlib.pyplot as plt
import dcf_calculator as dcf
import numpy as np

app = Flask(__name__, template_folder=os.path.join(os.path.dirname(__file__), '..', 'templates'))
app.secret_key = 'owadio'

@app.route('/', methods = ['GET', 'POST'])
def home():
    if request.method == 'POST':
        stock_ticker = request.form.get('ticker')
        stock_ticker = stock_ticker.upper()
        stock_info, stock_financials, fcf_dict = scrape_stock_details(stock_ticker)
    return render_template('home.html')

def scrape_stock_details(ticker: str):
    stock_ticker = yf.Ticker(ticker)

    filtered_stock_info = filter_stock_summary(stock_ticker.info)
    filtered_stock_financials, fcf = filter_stock_financials(stock_ticker, filtered_stock_info)
    intrinsic_value = calculate_intrinsic_value_dcf(filtered_stock_financials, fcf)
    

    return filtered_stock_info, filtered_stock_financials, fcf

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
        'beta': 'Beta'
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
    
    # CALCUALTE GROWTH RATE G
    ebit, invested_capital, capex, change_in_working_capital = data_source['ebit'], data_source['invested_capital'], data_source['capex'], data_source['change_in_working_capital']
    g = ((ebit * (1 - tax_rate)) / invested_capital) * ((capex + change_in_working_capital) / (ebit * (1 - tax_rate)))
    print(f"g = {g}")

    # calculate industry growth rate
    industry_growth_rate = 0.05 # fix it for now, later we can scrape it out no worries

    # Calculate growth rates from FCF list
    fcf_list = list(fcf_list.values())
    future_fcf_list = dcf.estimate_future_fcf(fcf_list)
    wacc = dcf.discount_rate(market_cap, total_debt, cost_of_equity, cost_of_debt, tax_rate)
    cagr = dcf.calculate_cagr(fcf_list)
    chosen_growth_rate = estimate_growth_rate(fcf_list, cagr, g, industry_growth_rate, wacc)
    equity_value = dcf.calculate_equity_value(future_fcf_list, wacc, chosen_growth_rate, net_debt)
    intrinsic_value = dcf.calculate_intrinsic_value(equity_value, shares_outstanding)
    print(intrinsic_value)
    return intrinsic_value

def estimate_growth_rate(fcf_list, cagr, g, industry_growth_rate, wacc):
    return wacc - 0.02


def scrape_stock_price(ticker: str):
    # stock_data.history(period="5y")
    pass

def scrape_sp500_price(tickers: list):
    pass

if __name__ == '__main__':
    app.run(debug=True)