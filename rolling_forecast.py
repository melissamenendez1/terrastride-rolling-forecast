"""
Part 2: 13-week rolling revenue forecast. Each week the forecast rolls forward:
the newest closed week is added, the exponential smoothing models are refit on
the latest 5 years of actuals, and the next 13 weeks are re-forecast.

Run build_baseline.py first; it produces the weekly actuals this script reads.
"""
import pandas as pd

from smoothing_model import (
    ACTUALS_FILE,
    FORECAST_HORIZON_WEEKS,
    LOOKBACK_WEEKS,
    ROLLING_VERSIONS,
    calculate_revenue,
    fit_driver_models,
)

df_actuals = pd.read_csv(ACTUALS_FILE, parse_dates=["Week_Start"], index_col="Week_Start")
df_actuals.index.freq = "W-MON"

# ==============================================================================
# 13-WEEK ROLLING FORECAST
# ==============================================================================
# Version 1 closes 12 weeks before the latest close; the last version is the current forecast
forecast_records = []

for version in range(1, ROLLING_VERSIONS + 1):
    cutoff_position = len(df_actuals) - ROLLING_VERSIONS + version
    history = df_actuals.iloc[cutoff_position - LOOKBACK_WEEKS:cutoff_position]
    cutoff_week = history.index[-1]

    models = fit_driver_models(history)
    driver_forecast = pd.DataFrame({
        "sessions": models["sessions"].forecast(FORECAST_HORIZON_WEEKS),
        "cvr": models["cvr"].forecast(FORECAST_HORIZON_WEEKS),
        "aov": models["aov"].forecast(FORECAST_HORIZON_WEEKS)
    })

    for weeks_ahead, (week_start, drivers) in enumerate(driver_forecast.iterrows(), start=1):
        record = {
            "Version_Number": version,
            "Forecast_Version": f"v{version}_{cutoff_week.strftime('%Y-%m-%d')}_Close",
            "Actuals_Through": cutoff_week.strftime("%Y-%m-%d"),
            "Week_Start": week_start.strftime("%Y-%m-%d"),
            "Weeks_Ahead": weeks_ahead
        }
        record.update(calculate_revenue(drivers["sessions"], drivers["cvr"], drivers["aov"]))

        # Attach the actual once that week has closed, for forecast accuracy
        has_actual = week_start in df_actuals.index
        record["Actual_Revenue"] = df_actuals.at[week_start, "Gross_Revenue"] if has_actual else None
        record["Revenue_Variance"] = (round(record["Actual_Revenue"] - record["Gross_Revenue"], 2)
                                      if has_actual else None)
        forecast_records.append(record)

# ==============================================================================
# EXPORT
# ==============================================================================
df_forecast = pd.DataFrame(forecast_records)
df_forecast.to_csv("terrastride_13_week_forecast.csv", index=False)

closed = df_forecast.dropna(subset=["Actual_Revenue"])
miss = (closed["Revenue_Variance"].abs() / closed["Actual_Revenue"]).mean()
current = df_forecast[df_forecast["Version_Number"] == ROLLING_VERSIONS]

print("13-week rolling forecast saved.")
print(f"Average revenue miss on closed weeks: {miss:.1%}")
print(f"Current forecast ({current['Forecast_Version'].iloc[0]}): "
      f"${current['Gross_Revenue'].sum():,.0f} revenue, "
      f"{current['Week_Start'].iloc[0]} to {current['Week_Start'].iloc[-1]}")
