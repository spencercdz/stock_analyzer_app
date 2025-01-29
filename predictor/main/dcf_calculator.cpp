// main/mymodule.cpp
#include <iostream>
#include <vector>
#include <pybind11/pybind11.h>
#include <pybind11/stl.h>

namespace py = pybind11;

// Feature to calculate yearly FCF for my main.py
float yearly_fcf(int operating_cf, int capital_expend) {
    return (operating_cf - capital_expend);
}


//Calculate Discount Rate (WACC - Weighted Avg Cost of Capital)
float discount_rate(/"int market_cap, int total_debt, int cost_equity, int cost_debt, int tax_rate"/) {
    //need to change the params so that it is more intuitive

    float total_debt = calculate_total_debt(short_term_debt, long_term_debt);
    float cost_equity = calculate_cost_of_equity(risk_free_rate, stock_beta, market_risk_premium);
    float cost_debt = calculate_cost_of_debt(interest_expense, total_debt);
    float tax_rate = calculate_tax_rate(income_tax_expense, pre_tax_income);

    return (static_cast<float>(market_cap) / (market_cap + total_debt) * cost_equity) + (static_cast<float>(total_debt) / (market_cap + total_debt) * cost_debt * (1 - tax_rate));
}

float calculate_total_debt(int short_term_debt, int long_term_debt) {
    return short_term_debt + long_term_debt;
}

float calculate_cost_of_equity(int risk_free_rate, int stock_beta, int market_risk_premium) {
    return risk_free_rate + stock_beta * (market_risk_premium);
}

float calculate_cost_of_debt(int interest_expense, int total_debt) {
    return static_cast<float>(interest_expense) / total_debt;
}

float calculate_tax_rate(int income_tax_expense, int pre_tax_income) {
    return static_cast<float>(income_tax_expense) / pre_tax_income;
}


//Calculate Growth Rate of FCF, will be using Historical Growth Rate CAGR as the method
float calculate_cagr(const std::vector<int>& fcf_list) {
    // get my end year FCF
    float latest_fcf = fcf_list.at(0);
    // get my start year fcf
    float earliest_fcf = fcf_list.back();
    // get my length of list to be my years
    int years = fcf_list.size();
    // computer (end_fcf / start_fcf) * (1 / years) - 1 to get cagr
    return ((latest_fcf / earliest_fcf) * (1 / years) - 1);
}

//Estimate Future FCF using cagr
const std::vector<int>& estimate_future_fcf(const std::vector<int>& fcf_list) {
    /* input the list of FCFs you can scrape
    estimate for next 5 years only */

    // calculate cagr first
    float cagr = calculate_cagr(const std::vector<int>& vec)

    // now find my latest FCF, then project it for 5 years, we return the list of 5 years FCF
    // to find 2026 FCF, take 2025fcf * (1 + growth rate in %) = 2026fcf

    return future_fcf_list
}

//Calculate Terminal Value (TV)
float calculate_tv(const std::vector<int>& future_fcf_list, float wacc, float cagr) {
    // sum up my list into net projected FCF (for 5 yearz)

    // now just apply (sum_FCF * (1 + cagr)) / (wacc - cagr) to get TV

}


//Calculate Present Value (PV)
float calculate_pv(float year_fcf, float wacc, float year) {
    return year_fcf / (1 + wacc) * (year);
}

//Calculate Equity Value
float calculate_equity_value(float ) {
    // calculate tv

    // calculate pv

    // enteprise value = sum of pv of fcfs + pv of tv

    // equity value = enteprise value - net debt
}


//Calculate Intrinsic Value Per Share
float calculate_intrinsic_value(float equity_value, int shares_outstanding) {
    // instrinc value = equity_value / shares_outstanding
    return equity_value / shares_outstanding;
}