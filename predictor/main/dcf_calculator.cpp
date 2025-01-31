// main/dcf_calculator.cpp
#include <iostream>
#include <vector>
#include <cmath>
#include <pybind11/pybind11.h>
#include <pybind11/stl.h>

namespace py = pybind11;

// Feature: calculate yearly FCF for my main.py
double yearly_fcf(double operating_cf, double capital_expend) {
    return (operating_cf - capital_expend);
}

// Feature: Calculate Discount Rate (WACC - Weighted Avg Cost of Capital)
double discount_rate(double market_cap, double total_debt, double cost_equity, double cost_debt, double tax_rate) {

    return (static_cast<double>(market_cap) / (market_cap + total_debt) * cost_equity) + (static_cast<double>(total_debt) / (market_cap + total_debt) * cost_debt * (1 - tax_rate));
}

double calculate_total_debt(double short_term_debt, double long_term_debt) {
    return short_term_debt + long_term_debt;
}

double calculate_cost_of_equity(double risk_free_rate, double stock_beta, double market_return) {
    return risk_free_rate + stock_beta * (market_return - risk_free_rate);
}

double calculate_cost_of_debt(double interest_expense, double total_debt) {
    return static_cast<double>(interest_expense) / total_debt;
}

double calculate_tax_rate(double income_tax_expense, double pre_tax_income) {
    return static_cast<double>(income_tax_expense) / pre_tax_income;
}


// Feature: Calculate Growth Rate of FCF, will be using historical growth rate CAGR as the method
double calculate_cagr(const std::vector<double>& fcf_list) {
    double latest_fcf = static_cast<double>(fcf_list.at(0)); // get my latest FCF
    double earliest_fcf = static_cast<double>(fcf_list.back()); // get my earliest fcf
    size_t num_years = fcf_list.size(); // get my length of list to be my years
    double exponent = 1.0f / (num_years - 1);
    return std::pow(latest_fcf / earliest_fcf, exponent) - 1.0f; // compute (end_fcf / start_fcf) to power of (1 / years) - 1 to get cagr
}


// Feature: Estimate Future FCF using cagr, estimate for next 5 years only
std::vector<double> estimate_future_fcf(const std::vector<double>& fcf_list) {
    double cagr = calculate_cagr(fcf_list); // calculate cagr first
    double latest_fcf = static_cast<double>(fcf_list.back()); // now find my latest FCF, then project it for 5 years, we return the list of 5 years FCF
    std::vector<double> future_fcf_list; // to find 2026 FCF, take 2025fcf * (1 + growth rate in %) = 2026fcf
    future_fcf_list.reserve(5);

    for (int i = 0; i < 5; i++) {
        latest_fcf *= (1 + cagr);
        future_fcf_list.push_back(latest_fcf);
    } // calculate fcf for the years

    return future_fcf_list;
}

double calculate_tv(const std::vector<double>& future_fcf_list, double wacc, double cagr) { //Calculate Terminal Value (TV)
    double last_future_fcf = future_fcf_list.back(); // get last projected FCF (for 5 yearz)

    return (last_future_fcf * (1 + cagr)) / (wacc - cagr); // now just apply (last_fcf * (1 + cagr)) / (wacc - cagr) to get TV
}

double calculate_pv(double year_fcf, double wacc, double year) { //Calculate Present Value (PV)
    return year_fcf / (std::pow((1 + wacc), (year)));
}

// Feature: Calculate Equity Value
double calculate_equity_value(const std::vector<double>& future_fcf_list, double wacc, double cagr, double net_debt) {
    double tv = calculate_tv(future_fcf_list, wacc, cagr); // calculate tv
    double discounted_tv = calculate_pv(tv, wacc, static_cast<double>(future_fcf_list.size()));
    double sum_of_discounted_pv = 0; // calculate sum of pv

    for (size_t i = 0; i < future_fcf_list.size(); ++i) {
        sum_of_discounted_pv += calculate_pv(future_fcf_list[i], wacc, static_cast<double>(i + 1));
    }

    double enterprise_value = sum_of_discounted_pv + discounted_tv; // enterprise_value = sum of pv of fcfs + pv of tv
    return (enterprise_value - net_debt); // equity value = enterprise_value - net debt
}

// Feature: Calculate Intrinsic Value Per Share
double calculate_intrinsic_value(double equity_value, double shares_outstanding) {
    return equity_value / shares_outstanding; // instrinc value = equity_value / shares_outstanding
}

PYBIND11_MODULE(dcf_calculator, m) {
    m.def("yearly_fcf", &yearly_fcf, "Feature: calculate yearly FCF for my main.py. Usage: double yearly_fcf(double operating_cf, double capital_expend)");
    m.def("discount_rate", &discount_rate, "Feature: Calculate Discount Rate/WACC: Usage: double discount_rate(double market_cap, double total_debt, double cost_equity, double cost_debt, double tax_rate)");
    m.def("calculate_total_debt", &calculate_total_debt, "Usage: double calculate_total_debt(double short_term_debt, double long_term_debt))");
    m.def("calculate_cost_of_equity", &calculate_cost_of_equity, "Usage: double calculate_cost_of_equity(double risk_free_rate, double stock_beta, double market_risk_premium)");
    m.def("calculate_cost_of_debt", &calculate_cost_of_debt, "Usage: double calculate_cost_of_debt(double interest_expense, double total_debt)");
    m.def("calculate_tax_rate", &calculate_tax_rate, "Usage: double calculate_tax_rate(double income_tax_expense, double pre_tax_income)");
    m.def("calculate_cagr", &calculate_cagr, "Feature: Calculate Growth Rate of FCF, will be using historical growth rate CAGR as the method. Usage: double calculate_cagr(const std::vector<int>& fcf_list)");
    m.def("estimate_future_fcf", &estimate_future_fcf, "Feature: Estimate Future FCF using cagr, estimate for next 5 years only. Usage: std::vector<double> estimate_future_fcf(const std::vector<int>& fcf_list)");
    m.def("calculate_equity_value", &calculate_equity_value, "Feature: Calculate Equity Value. Usage: double calculate_equity_value(const std::vector<double>& future_fcf_list, double wacc, double cagr, double net_debt)");
    m.def("calculate_tv", &calculate_tv, "Usage: double calculate_tv(const std::vector<double>& future_fcf_list, double wacc, double cagr)");
    m.def("calculate_pv", &calculate_pv, "Usage: double calculate_pv(double year_fcf, double wacc, double year)");
    m.def("calculate_intrinsic_value", &calculate_intrinsic_value, "// Feature: Calculate Intrinsic Value Per Share. Usage: double calculate_intrinsic_value(double equity_value, double shares_outstanding)");
}