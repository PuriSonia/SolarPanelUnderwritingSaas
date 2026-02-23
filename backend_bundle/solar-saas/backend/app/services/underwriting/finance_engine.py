
import numpy as np

class FinancialEngine:

    @staticmethod
    def calculate_irr(cash_flows):
        return np.irr(cash_flows)

    @staticmethod
    def calculate_npv(discount_rate, cash_flows):
        return np.npv(discount_rate, cash_flows)

    @staticmethod
    def build_cash_flows(capex, energy_rev, carbon_rev, opex, years):
        cash_flows = [-capex]
        for _ in range(years):
            net = energy_rev + carbon_rev - opex
            cash_flows.append(net)
        return cash_flows

    def base_case(self, capex, energy_revenue, carbon_revenue, opex, years, discount_rate):
        cash_flows = self.build_cash_flows(capex, energy_revenue, carbon_revenue, opex, years)
        irr = self.calculate_irr(cash_flows)
        npv = self.calculate_npv(discount_rate, cash_flows)
        return {"irr": irr, "npv": npv, "cash_flows": cash_flows}

    def risk_adjusted_case(
        self,
        capex,
        energy_revenue,
        carbon_revenue,
        opex,
        years,
        discount_rate,
        issuance_probability,
        delay_years=1,
        risk_premium_bps=200
    ):
        adjusted_carbon = carbon_revenue * issuance_probability
        delayed_carbon = adjusted_carbon / ((1 + discount_rate) ** delay_years)
        adjusted_discount_rate = discount_rate + (risk_premium_bps / 10000)

        cash_flows = self.build_cash_flows(capex, energy_revenue, delayed_carbon, opex, years)
        irr = self.calculate_irr(cash_flows)
        npv = self.calculate_npv(adjusted_discount_rate, cash_flows)

        return {
            "irr": irr,
            "npv": npv,
            "adjusted_discount_rate": adjusted_discount_rate,
            "cash_flows": cash_flows
        }
