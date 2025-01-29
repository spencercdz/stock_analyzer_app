// main/mymodule.cpp
#include <iostream>
#include <vector>
#include <cmath>
#include <pybind11/pybind11.h>
#include <pybind11/stl.h>

namespace py = pybind11;

// Feature: calculate yearly FCF for my main.py
float yearly_fcf(int operating_cf, int capital_expend) {
    return (operating_cf - capital_expend);
}


// Feature: Calculate Discount Rate (WACC - Weighted Avg Cost of Capital)
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


// Feature: Calculate Growth Rate of FCF, will be using historical growth rate CAGR as the method
float calculate_cagr(const std::vector<int>& fcf_list) {
    float latest_fcf = static_cast<float>(fcf_list.at(0)); // get my latest FCF
    float earliest_fcf = static_cast<float>(fcf_list.back()); // get my earliest fcf
    int years = fcf_list.size(); // get my length of list to be my years

    return std::pow(latest_fcf / earliest_fcf, 1.0f / (years - 1)) - 1.0f; // compute (end_fcf / start_fcf) to power of (1 / years) - 1 to get cagr
}


// Feature: Estimate Future FCF using cagr, estimate for next 5 years only
std::vector<float> estimate_future_fcf(const std::vector<int>& fcf_list) {
    float cagr = calculate_cagr(fcf_list); // calculate cagr first
    float latest_fcf = static_cast<float>(fcf_list.back()); // now find my latest FCF, then project it for 5 years, we return the list of 5 years FCF
    std::vector<float> future_fcf_list; // to find 2026 FCF, take 2025fcf * (1 + growth rate in %) = 2026fcf
    future_fcf_list.reserve(5);

    for (int i = 0; i < 5; i++) {
        latest_fcf *= (1 + cagr);
        future_fcf_list.push_back(latest_fcf);
    } // calculate fcf for the years

    return future_fcf_list;
}


// Feature: Calculate Equity Value
float calculate_equity_value(const std::vector<float>& future_fcf_list, float wacc, float cagr, float net_debt) {
    float tv = calculate_tv(future_fcf_list, wacc, cagr); // calculate tv
    float discounted_tv = calculate_pv(tv, wacc, future_fcf_list.size());
    float sum_of_discounted_pv = 0; // calculate sum of pv

    for (size_t i = 0; i < future_fcf_list.size(); ++i) {
        sum_of_discounted_pv += calculate_pv(future_fcf_list[i], wacc, (i + 1));
    }

    float enterprise_value = sum_of_discounted_pv + discounted_tv; // enterprise_value = sum of pv of fcfs + pv of tv
    return (enterprise_value - net_debt); // equity value = enterprise_value - net debt
}

float calculate_tv(const std::vector<float>& future_fcf_list, float wacc, float cagr) { //Calculate Terminal Value (TV)
    float last_future_fcf = future_fcf_list.back(); // get last projected FCF (for 5 yearz)

    return (last_future_fcf * (1 + cagr)) / (wacc - cagr); // now just apply (last_fcf * (1 + cagr)) / (wacc - cagr) to get TV
}

float calculate_pv(float year_fcf, float wacc, float year) { //Calculate Present Value (PV)
    return year_fcf / (std::pow((1 + wacc), (year)));
}


// Feature: Calculate Intrinsic Value Per Share
float calculate_intrinsic_value(float equity_value, int shares_outstanding) {
    return equity_value / shares_outstanding; // instrinc value = equity_value / shares_outstanding
}