import numpy as np
import pandas as pd

# Random number generator with a fixed seed, so every run produces the same actuals
rng = np.random.default_rng(42)

# ==============================================================================
# BASELINE OPERATIONAL ASSUMPTIONS
# ==============================================================================
BASE_TRAFFIC = 50000
ORGANIC_RATIO = 0.40
BASE_CONVERSION_RATE = 0.025
AVERAGE_ORDER_VALUE = 120
COST_PER_CLICK = 0.45
BASE_FIXED_OVERHEAD = 15000
REPEAT_ORDER_RATE = 0.30
MONTHLY_GROWTH_RATE = 0.03

CACTEX_COST_PER_UNIT = 28.00
ANANATEX_BASE_COST = 14.00
OTHER_PACKAGING_COST = 10.00

# Month-to-month variation applied to simulated actuals (multiplier ranges)
TRAFFIC_NOISE_RANGE = (0.92, 1.04)
CONVERSION_NOISE_RANGE = (0.95, 1.05)
AOV_NOISE_RANGE = (0.97, 1.03)

# Number of closed months averaged to set each forecast's starting point
ANCHOR_WINDOW_MONTHS = 3

# ==============================================================================
# SUPPLY CHAIN RISK PROFILE
# ==============================================================================
CROP_SHOCK_SETTINGS = {
    "start_month": 13,
    "end_month": 18,
    "ananatex_cost_increase": 0.25,  # 25% raw material price spike
    "max_monthly_inventory": 1100    # Production cap during the shortage
}

# Generate 24-month timeline (Jan 2025 to Dec 2026)
master_months = pd.date_range(start="2025-01-01", periods=24, freq="MS")


HOLIDAY_SEASONALITY = {11: 1.6, 12: 1.4}  # November +60%, December +40%
HOLIDAY_CONVERSION_FACTOR = 0.9           # Holiday conversion runs 10% lower: more casual browsers


def get_seasonality(month_obj):
    """Returns the holiday traffic multiplier (1.0 outside the holidays)."""
    return HOLIDAY_SEASONALITY.get(month_obj.month, 1.0)


def get_conversion_seasonality(month_obj):
    """Returns the holiday conversion multiplier (1.0 outside the holidays)."""
    return HOLIDAY_CONVERSION_FACTOR if month_obj.month in HOLIDAY_SEASONALITY else 1.0


# ==============================================================================
# DTC FINANCIAL AND OPERATIONAL DRIVER ENGINE
# ==============================================================================
def execute_driver_pipeline(month_idx, month_obj, base_traffic_override=None,
                            growth_periods=None, base_conversion=BASE_CONVERSION_RATE,
                            base_aov=AVERAGE_ORDER_VALUE, traffic_noise=1.00,
                            conversion_noise=1.00, aov_noise=1.00, shock_config=None):
    """
    Calculates one month of the DTC financial model.

    month_idx             Calendar month number (1 = Jan 2025). Drives the shock
                          window and fixed overhead.
    base_traffic_override Starting traffic level for a re-anchored forecast.
    growth_periods        Months of growth to apply from the starting traffic.
                          Defaults to month_idx - 1 (growth from Jan 2025).
    base_conversion       Underlying (non-holiday) conversion rate.
    base_aov              Average order value.
    *_noise               Random multipliers applied to actuals only.
    shock_config          Supply shock settings; applied only when provided.
    """
    seasonality = get_seasonality(month_obj)

    effective_base_traffic = base_traffic_override if base_traffic_override is not None else BASE_TRAFFIC
    periods = growth_periods if growth_periods is not None else month_idx - 1

    growth_factor = (1 + MONTHLY_GROWTH_RATE) ** periods
    total_traffic = int(effective_base_traffic * growth_factor * seasonality * traffic_noise)

    organic_sessions = int(total_traffic * ORGANIC_RATIO)
    paid_sessions = total_traffic - organic_sessions

    cvr = base_conversion * get_conversion_seasonality(month_obj) * conversion_noise
    aov = base_aov * aov_noise

    customer_demand_orders = int(total_traffic * cvr)

    is_shock_active = False
    ananatex_cost_modifier = 0.00
    max_production_capacity = float('inf')

    if shock_config is not None and shock_config["start_month"] <= month_idx <= shock_config["end_month"]:
        is_shock_active = True
        ananatex_cost_modifier = shock_config["ananatex_cost_increase"]
        max_production_capacity = shock_config["max_monthly_inventory"]

    harvest_cost_status = "SUPPLY SHOCK (PRICE SPIKE)" if is_shock_active else "Normal"

    if is_shock_active and customer_demand_orders > max_production_capacity:
        total_orders = max_production_capacity
        inventory_shortfall = customer_demand_orders - max_production_capacity
        harvest_revenue_impact = "REVENUE LOSS (STOCKOUT)"
    else:
        total_orders = customer_demand_orders
        inventory_shortfall = 0
        harvest_revenue_impact = "None"

    repeat_orders = int(total_orders * REPEAT_ORDER_RATE)
    new_customer_orders = total_orders - repeat_orders

    current_ananatex = ANANATEX_BASE_COST * (1 + ananatex_cost_modifier)
    unit_cogs = CACTEX_COST_PER_UNIT + current_ananatex + OTHER_PACKAGING_COST

    gross_revenue = total_orders * aov
    lost_revenue = inventory_shortfall * aov
    cogs = total_orders * unit_cogs
    gross_profit = gross_revenue - cogs

    marketing_spend = paid_sessions * COST_PER_CLICK
    fixed_overhead = BASE_FIXED_OVERHEAD * (1 + 0.01 * (month_idx - 1))
    total_opex = marketing_spend + fixed_overhead

    cac = marketing_spend / max(1, new_customer_orders)

    return {
        "Harvest_Cost_Status": harvest_cost_status,
        "Total_Sessions": total_traffic,
        "Customer_Demand_Orders": customer_demand_orders,
        "Total_Orders_Fulfilled": total_orders,
        "Lost_Orders_Shortfall": inventory_shortfall,
        "Gross_Revenue": round(gross_revenue, 2),
        "Lost_Revenue": round(lost_revenue, 2),
        "Unit_COGS": round(unit_cogs, 2),
        "Total_COGS": round(cogs, 2),
        "Gross_Profit": round(gross_profit, 2),
        "Gross_Margin_Pct": round(gross_profit / max(1, gross_revenue), 4),
        "Marketing_Spend": round(marketing_spend, 2),
        "Fixed_Overhead": round(fixed_overhead, 2),
        "Total_OpEx": round(total_opex, 2),
        "Net_Operating_Income": round(gross_profit - total_opex, 2),
        "CAC": round(cac, 2),
        "Revenue_Impact_Status": harvest_revenue_impact,
        "Conversion_Rate": round(cvr, 5),
        "Average_Order_Value": round(aov, 2)
    }


# ==============================================================================
# STEP 1: GENERATE HISTORICAL ACTUALS POOLS
# ==============================================================================
# Traffic noise is drawn first so traffic actuals stay identical to earlier runs
traffic_noise = rng.uniform(*TRAFFIC_NOISE_RANGE, size=24)
conversion_noise = rng.uniform(*CONVERSION_NOISE_RANGE, size=24)
aov_noise = rng.uniform(*AOV_NOISE_RANGE, size=24)

actuals_pool_normal = {}
actuals_pool_shock = {}

for idx, month_obj in enumerate(master_months):
    month_num = idx + 1
    month_noise = {
        "traffic_noise": traffic_noise[idx],
        "conversion_noise": conversion_noise[idx],
        "aov_noise": aov_noise[idx]
    }

    actuals_pool_normal[month_num] = execute_driver_pipeline(
        month_idx=month_num,
        month_obj=month_obj,
        **month_noise
    )

    actuals_pool_shock[month_num] = execute_driver_pipeline(
        month_idx=month_num,
        month_obj=month_obj,
        shock_config=CROP_SHOCK_SETTINGS,
        **month_noise
    )


def get_anchor_drivers(actuals_pool, actuals_cutoff, window=ANCHOR_WINDOW_MONTHS):
    """
    Sets each forecast's starting point from the last `window` closed months.

    Traffic:          holiday boost removed, older months grown forward to the
                      latest month so all are comparable, then averaged.
    Conversion rate:  holiday dip removed, then averaged.
    Order value:      averaged.

    Returns None when no months have closed, so the forecast uses the original plan.
    """
    if actuals_cutoff == 0:
        return None

    start = max(1, actuals_cutoff - window + 1)
    traffic_levels, conversion_levels, aov_levels = [], [], []

    for m in range(start, actuals_cutoff + 1):
        month_obj = master_months[m - 1]
        actual = actuals_pool[m]

        base_traffic = actual["Total_Sessions"] / get_seasonality(month_obj)
        traffic_levels.append(base_traffic * (1 + MONTHLY_GROWTH_RATE) ** (actuals_cutoff - m))
        conversion_levels.append(actual["Conversion_Rate"] / get_conversion_seasonality(month_obj))
        aov_levels.append(actual["Average_Order_Value"])

    return {
        "base_traffic_override": sum(traffic_levels) / len(traffic_levels),
        "base_conversion": sum(conversion_levels) / len(conversion_levels),
        "base_aov": sum(aov_levels) / len(aov_levels)
    }


# ==============================================================================
# STEP 2: ROLLING FORECAST COMPILATION WITH RE-ANCHORING
# ==============================================================================
normal_records = []
shock_records = []

for cycle_idx, cycle_month in enumerate(master_months):
    actuals_cutoff = cycle_idx
    version_label = f"v{cycle_idx + 1}.0_{cycle_month.strftime('%b_%Y')}_Forecast"
    version_sequence_number = cycle_idx + 1

    total_horizon_length = actuals_cutoff + 12

    # Each forecast starts from the average of the latest closed months
    anchors_normal = get_anchor_drivers(actuals_pool_normal, actuals_cutoff) or {}
    anchors_shock = get_anchor_drivers(actuals_pool_shock, actuals_cutoff) or {}

    for current_idx in range(total_horizon_length):
        if current_idx >= len(master_months):
            break

        target_month = master_months[current_idx]
        month_number = current_idx + 1
        is_actual = month_number <= actuals_cutoff
        data_type = "Actual" if is_actual else "Forecast"

        # Months of growth from the anchor month (None = grow from Jan 2025)
        growth_periods = (month_number - actuals_cutoff) if actuals_cutoff > 0 else None

        # --- SCENARIO A: NORMAL OPERATIONS ---
        if is_actual:
            metrics_normal = actuals_pool_normal[month_number].copy()
        else:
            metrics_normal = execute_driver_pipeline(
                month_idx=month_number,
                month_obj=target_month,
                growth_periods=growth_periods,
                **anchors_normal
            )

        record_normal = {
            "Version_Number": version_sequence_number,
            "Forecast_Version": version_label,
            "Timeline_Month": target_month.strftime("%Y-%m-01"),
            "Data_Segment": data_type
        }
        record_normal.update(metrics_normal)
        normal_records.append(record_normal)

        # --- SCENARIO B: SUPPLY SHOCK ---
        if is_actual:
            metrics_shock = actuals_pool_shock[month_number].copy()
        else:
            metrics_shock = execute_driver_pipeline(
                month_idx=month_number,
                month_obj=target_month,
                growth_periods=growth_periods,
                shock_config=CROP_SHOCK_SETTINGS,
                **anchors_shock
            )

        record_shock = {
            "Version_Number": version_sequence_number,
            "Forecast_Version": version_label,
            "Timeline_Month": target_month.strftime("%Y-%m-01"),
            "Data_Segment": data_type
        }
        record_shock.update(metrics_shock)
        shock_records.append(record_shock)

# ==============================================================================
# STEP 3: EXPORT
# ==============================================================================
df_normal = pd.DataFrame(normal_records)
df_normal.to_csv("terrastride_forecast_normal.csv", index=False)

df_shock = pd.DataFrame(shock_records)
df_shock.to_csv("terrastride_forecast_bad_harvest.csv", index=False)

print("Rolling forecast matrix saved.")