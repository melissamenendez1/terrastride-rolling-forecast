"""
Bad Harvest scenario: the current 13-week forecast under a crop failure that
raises Ananatex fiber costs and caps weekly production. Demand comes from the
forecast; the shock only limits how much of it can be filled and what it costs.

Run rolling_forecast.py first; it produces the forecast this script reads.
"""
import pandas as pd

# ==============================================================================
# COST ASSUMPTIONS
# ==============================================================================
CACTEX_COST_PER_UNIT = 28.00   # Cactus leather upper
ANANATEX_BASE_COST = 14.00     # Pineapple-leaf fiber lining
OTHER_PACKAGING_COST = 10.00
ORGANIC_RATIO = 0.40           # Share of sessions that cost nothing to acquire
COST_PER_CLICK = 0.45          # Paid sessions
REPEAT_ORDER_RATE = 0.30       # Orders from returning customers, excluded from CAC

# ==============================================================================
# SUPPLY CHAIN RISK PROFILE
# ==============================================================================
CROP_SHOCK_SETTINGS = {
    "start_week": "2026-11-02",
    "end_week": "2027-01-25",
    "ananatex_cost_increase": 0.25,  # 25% raw material price spike
    "max_weekly_production": 600     # Pairs per week during the shortage
}

FORECAST_FILE = "terrastride_13_week_forecast.csv"


def apply_scenario(forecast, shock_config=None):
    """Calculates fulfilment, costs and margin for each forecast week, with an optional supply shock."""
    weeks = forecast.copy()
    in_shock = pd.Series(False, index=weeks.index)
    if shock_config is not None:
        in_shock = weeks["Week_Start"].between(shock_config["start_week"], shock_config["end_week"])

    capacity = shock_config["max_weekly_production"] if shock_config is not None else float("inf")
    cost_increase = shock_config["ananatex_cost_increase"] if shock_config is not None else 0.0

    weeks["Customer_Demand_Orders"] = weeks["Orders"]
    weeks["Orders_Fulfilled"] = weeks["Orders"].where(~in_shock, weeks["Orders"].clip(upper=capacity))
    weeks["Lost_Orders"] = weeks["Customer_Demand_Orders"] - weeks["Orders_Fulfilled"]

    ananatex_cost = ANANATEX_BASE_COST * (1 + cost_increase * in_shock)
    weeks["Unit_COGS"] = (CACTEX_COST_PER_UNIT + ananatex_cost + OTHER_PACKAGING_COST).round(2)

    # Order value from the forecast's own revenue, so the Normal scenario matches it to the cent
    aov = forecast["Gross_Revenue"] / forecast["Orders"]
    weeks["Gross_Revenue"] = (weeks["Orders_Fulfilled"] * aov).round(2)
    weeks["Lost_Revenue"] = (weeks["Lost_Orders"] * aov).round(2)
    weeks["Total_COGS"] = (weeks["Orders_Fulfilled"] * weeks["Unit_COGS"]).round(2)
    weeks["Gross_Profit"] = (weeks["Gross_Revenue"] - weeks["Total_COGS"]).round(2)
    weeks["Gross_Margin_Pct"] = (weeks["Gross_Profit"] / weeks["Gross_Revenue"]).round(4)

    # Ad spend follows traffic, which the shock doesn't touch; new customers follow fulfilled orders
    paid_sessions = weeks["Total_Sessions"] - (weeks["Total_Sessions"] * ORGANIC_RATIO).astype(int)
    weeks["Marketing_Spend"] = (paid_sessions * COST_PER_CLICK).round(2)
    new_customer_orders = weeks["Orders_Fulfilled"] - (weeks["Orders_Fulfilled"] * REPEAT_ORDER_RATE).astype(int)
    weeks["CAC"] = (weeks["Marketing_Spend"] / new_customer_orders.clip(lower=1)).round(2)

    weeks["Supply_Status"] = in_shock.map({True: "SUPPLY SHOCK", False: "Normal"})
    return weeks


# ==============================================================================
# BUILD BOTH SCENARIOS FROM THE CURRENT FORECAST
# ==============================================================================
df_forecast = pd.read_csv(FORECAST_FILE)
current = df_forecast[df_forecast["Version_Number"] == df_forecast["Version_Number"].max()]
current = current[["Forecast_Version", "Week_Start", "Total_Sessions", "Orders",
                   "Average_Order_Value", "Gross_Revenue"]]

normal = apply_scenario(current).assign(Scenario="Normal")
shock = apply_scenario(current, CROP_SHOCK_SETTINGS).assign(Scenario="Bad Harvest")

columns = ["Scenario", "Forecast_Version", "Week_Start", "Supply_Status", "Total_Sessions",
           "Customer_Demand_Orders", "Orders_Fulfilled", "Lost_Orders", "Average_Order_Value",
           "Gross_Revenue", "Lost_Revenue", "Unit_COGS", "Total_COGS", "Gross_Profit",
           "Gross_Margin_Pct", "Marketing_Spend", "CAC"]
df_scenarios = pd.concat([normal, shock])[columns]

# ==============================================================================
# EXPORT
# ==============================================================================
df_scenarios.to_csv("terrastride_bad_harvest_scenario.csv", index=False)


def summarize(df):
    revenue, profit = df["Gross_Revenue"].sum(), df["Gross_Profit"].sum()
    new_customers = (df["Orders_Fulfilled"] - (df["Orders_Fulfilled"] * REPEAT_ORDER_RATE).astype(int)).sum()
    return revenue, profit / revenue, df["Marketing_Spend"].sum() / new_customers


normal_revenue, normal_margin, normal_cac = summarize(normal)
shock_revenue, shock_margin, shock_cac = summarize(shock)

print("Bad Harvest scenario saved.")
print(f"Lost revenue: ${shock['Lost_Revenue'].sum():,.0f} "
      f"({shock['Lost_Orders'].sum():,} lost orders, {1 - shock_revenue / normal_revenue:.0%} of forecast revenue)")
print(f"Gross margin: {normal_margin:.2%} -> {shock_margin:.2%}")
print(f"CAC: ${normal_cac:.2f} -> ${shock_cac:.2f}")
