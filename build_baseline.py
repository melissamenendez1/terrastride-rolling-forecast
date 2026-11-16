"""
Part 1 (already in place): TerraStride's weekly sales history and the 5-year
exponential smoothing baseline fit to it. The 13-week rolling forecast
(rolling_forecast.py) builds on these outputs.
"""
import numpy as np
import pandas as pd

from smoothing_model import (
    ACTUALS_FILE,
    LOOKBACK_WEEKS,
    ROLLING_VERSIONS,
    calculate_revenue,
    fit_driver_models,
)

# Random number generator with a fixed seed, so every run produces the same actuals
rng = np.random.default_rng(42)

# ==============================================================================
# ASSUMPTIONS BEHIND THE SIMULATED ACTUALS (the forecast never sees these)
# ==============================================================================
WEEKS_PER_MONTH = 52 / 12
BASE_WEEKLY_SESSIONS = 50000 / WEEKS_PER_MONTH            # 50,000 sessions/month in Jan 2025
WEEKLY_GROWTH_RATE = 1.03 ** (12 / 52) - 1                # 3% monthly growth, compounded weekly
GROWTH_ANCHOR_DATE = pd.Timestamp("2025-01-01")
BASE_CONVERSION_RATE = 0.025
AVERAGE_ORDER_VALUE = 120

HOLIDAY_SEASONALITY = {11: 1.6, 12: 1.4}  # November +60%, December +40%
HOLIDAY_CONVERSION_FACTOR = 0.9           # Holiday conversion runs 10% lower: more casual browsers

# Week-to-week variation applied to simulated actuals (multiplier ranges)
TRAFFIC_NOISE_RANGE = (0.92, 1.04)
CONVERSION_NOISE_RANGE = (0.95, 1.05)
AOV_NOISE_RANGE = (0.97, 1.03)

# Most recent closed week (weeks start on Monday). Fixed so runs are reproducible.
LAST_CLOSED_WEEK = pd.Timestamp("2026-10-26")

# 5 years behind the earliest rolling version, through the latest close
total_actual_weeks = LOOKBACK_WEEKS + ROLLING_VERSIONS - 1
actual_weeks = pd.date_range(end=LAST_CLOSED_WEEK, periods=total_actual_weeks, freq="W-MON")


def get_seasonality(week_start):
    """Returns the holiday traffic multiplier, based on the month of the week's Thursday."""
    return HOLIDAY_SEASONALITY.get((week_start + pd.Timedelta(days=3)).month, 1.0)


def get_conversion_seasonality(week_start):
    """Returns the holiday conversion multiplier (1.0 outside the holidays)."""
    return HOLIDAY_CONVERSION_FACTOR if get_seasonality(week_start) != 1.0 else 1.0


# ==============================================================================
# STEP 1: WEEKLY SALES HISTORY
# ==============================================================================
traffic_noise = rng.uniform(*TRAFFIC_NOISE_RANGE, size=total_actual_weeks)
conversion_noise = rng.uniform(*CONVERSION_NOISE_RANGE, size=total_actual_weeks)
aov_noise = rng.uniform(*AOV_NOISE_RANGE, size=total_actual_weeks)

actual_records = []
for idx, week_start in enumerate(actual_weeks):
    weeks_from_anchor = (week_start - GROWTH_ANCHOR_DATE).days / 7
    sessions = (BASE_WEEKLY_SESSIONS * (1 + WEEKLY_GROWTH_RATE) ** weeks_from_anchor
                * get_seasonality(week_start) * traffic_noise[idx])
    cvr = BASE_CONVERSION_RATE * get_conversion_seasonality(week_start) * conversion_noise[idx]
    aov = AVERAGE_ORDER_VALUE * aov_noise[idx]

    record = {"Week_Start": week_start}
    record.update(calculate_revenue(sessions, cvr, aov))
    actual_records.append(record)

df_actuals = pd.DataFrame(actual_records).set_index("Week_Start")
df_actuals.index.freq = "W-MON"

# ==============================================================================
# STEP 2: 5-YEAR EXPONENTIAL SMOOTHING BASELINE
# ==============================================================================
# Fit on the latest 5 years; fitted values are the model's one-week-ahead estimate
baseline = df_actuals.iloc[-LOOKBACK_WEEKS:].copy()
models = fit_driver_models(baseline)
baseline["Fitted_Revenue"] = [
    calculate_revenue(models["sessions"].fittedvalues[w], models["cvr"].fittedvalues[w],
                      models["aov"].fittedvalues[w])["Gross_Revenue"]
    for w in baseline.index
]

# ==============================================================================
# STEP 3: EXPORT
# ==============================================================================
for df, path in [(df_actuals, ACTUALS_FILE), (baseline, "terrastride_5yr_baseline.csv")]:
    out = df.copy()
    out.index = out.index.strftime("%Y-%m-%d")
    out.to_csv(path, index_label="Week_Start")

miss = ((baseline["Fitted_Revenue"] - baseline["Gross_Revenue"]).abs() / baseline["Gross_Revenue"]).mean()
print("Weekly actuals and 5-year baseline saved.")
print(f"Baseline: {baseline.index[0]:%b %d, %Y} to {baseline.index[-1]:%b %d, %Y}, "
      f"average fit error {miss:.1%}")
