# TerraStride Co.: 13-Week Rolling Revenue Forecast

A 13-week rolling revenue forecast built in Python for a fictional direct-to-consumer sneaker brand. It builds on an existing 5-year exponential smoothing baseline. Every week, the forecast adds the newest closed week, refits the model on the latest five years of history, and re-forecasts the next 13 weeks.

> **Note:** TerraStride Co. and all data are fictional. Actuals are simulated, and all assumptions are illustrative.

**Portfolio write-up:** [Notion page](https://app.notion.com/p/melissamenendez/TerraStride-Co-13-Week-Rolling-Revenue-Forecast-3e6f1fbe1c7f80068743f3547447bf5c?source=copy_link)

---

## Project Structure

| Part | What it is | Script |
|---|---|---|
| **1. 5-year baseline** (already in place) | Five years of weekly sales history and the exponential smoothing model fit to it | `build_baseline.py` |
| **2. 13-week rolling forecast** (this project) | A forecast that rolls forward one week at a time, refit on the latest 5 years each week | `rolling_forecast.py` |
| **3. Bad Harvest scenario** | The current forecast stress-tested against a crop failure that limits supply | `bad_harvest_scenario.py` |

## Part 1: The 5-Year Baseline

TerraStride's weekly history covers Aug 2021–Oct 2026. The baseline is an exponential smoothing model fit on the latest five years (260 weeks, Nov 2021–Oct 2026). Its fitted revenue tracks actual revenue within **4.1%** on average.

**Driver chain:** Website Sessions → Conversion Rate → Orders → Average Order Value → Revenue

Each driver has its own smoothing model, so the forecast can show *why* revenue moves:

| Driver | Smoothing model | What it captures |
|---|---|---|
| Website sessions | Holt-Winters: multiplicative trend and 52-week seasonality | Compounding growth and holiday traffic spikes |
| Conversion rate | Holt-Winters: multiplicative 52-week seasonality, no trend | The holiday conversion dip |
| Average order value | Simple exponential smoothing | A stable level with week-to-week noise |

## Part 2: The 13-Week Rolling Forecast

- **Rolling cadence:** each Monday, the newest closed week is added, the models are refit on the latest 260 weeks, and the next 13 weeks are re-forecast.
- **Versions:** 13 weekly versions are kept. Versions 1–12 are past weekly runs (actuals through Aug 3–Oct 19, 2026), kept to measure accuracy against what actually happened. Version 13 is the **current forecast**, built on actuals through the week of Oct 26, 2026.
- **Accuracy tracking:** every forecast week that has since closed carries its actual revenue and variance.

## Part 3: Bad Harvest Scenario

TerraStride's plant-based leather depends on an agricultural harvest. This scenario applies a crop failure to the current 13-week forecast (Nov 2, 2026–Jan 31, 2027):

| Shock | Setting |
|---|---|
| Ananatex fiber cost | +25% ($14 → $17.50 per pair) |
| Production cap | 600 pairs per week |

Demand comes from the forecast and is unchanged; the shock only limits how much of it can be filled and what each pair costs. The shock is defined in a settings dictionary (`CROP_SHOCK_SETTINGS`), so other scenarios can be tested without changing the calculation code.

| Cost assumption | Value |
|---|---|
| Unit cost | $52 per pair (Cactex leather $28, Ananatex fiber $14, packaging $10) |
| Paid traffic | 60% of sessions at $0.45 per click |
| Repeat orders | 30% of orders, excluded from customer acquisition cost (CAC) |

## Key Results

- **Current forecast (Nov 2, 2026–Jan 31, 2027):** $1.06M revenue, 380K sessions and 8.9K orders over the next 13 weeks. November sessions run about 1.7× October's, a holiday lift the model learned from history.
- **Forecast accuracy:** past versions missed actual revenue by 6.6% on average across 78 closed forecast weeks. All of those weeks fall between August and October, so accuracy over the holiday peak is not yet tested.
- **Bad Harvest impact:** $138,154 in lost revenue and 1,154 lost orders, 13% of forecast revenue. 99% of the loss falls in November–December, when holiday demand runs above the 600-pair cap; January demand mostly fits under it. Gross margin falls from 56.56% to 53.64%, and CAC rises 15% ($16.54 → $19.02) because ad spend keeps buying traffic that can't be served.

---

## Repository Contents

| File | Description |
|---|---|
| `smoothing_model.py` | Shared model settings, exponential smoothing models and revenue driver chain |
| `build_baseline.py` | Part 1: produces the weekly sales history and fits the 5-year baseline |
| `rolling_forecast.py` | Part 2: produces the 13-week rolling forecast |
| `terrastride_weekly_actuals.csv` | Weekly actuals: sessions, conversion rate, orders, order value and revenue (Aug 2021–Oct 2026) |
| `terrastride_5yr_baseline.csv` | The latest 5 years of actuals with the baseline model's fitted revenue |
| `terrastride_13_week_forecast.csv` | 13 rolling versions × 13 weeks, with actuals and variance for closed weeks |
| `bad_harvest_scenario.py` | Part 3: applies the crop-failure shock to the current forecast |
| `terrastride_bad_harvest_scenario.csv` | Normal and Bad Harvest results for each forecast week: fulfilment, lost revenue, costs, margin and CAC |
| `terrastride_forecast_dashboard.pbix` | Power BI dashboard: 5-Year Baseline, 13-Week Forecast, Forecast Accuracy and Bad Harvest pages |
| `pyproject.toml` | Project metadata and Python dependencies |

## Dashboard

`terrastride_forecast_dashboard.pbix` presents the baseline, the current forecast, its accuracy and the Bad Harvest scenario across four pages.

| Page | What it shows |
|---|---|
| **5-Year Baseline** | Weekly actual revenue against the baseline's fitted revenue, with the average fit error |
| **13-Week Forecast** | The current version's revenue, orders and sessions, with weekly revenue and drivers |
| **Forecast Accuracy** | Each past version's forecast against actual revenue, and how the average miss changes with weeks ahead |
| **Bad Harvest** | Lost revenue and orders, gross margin and CAC by scenario, and weekly revenue for the normal forecast against the Bad Harvest scenario |

## Dependencies

| Library | Used for |
|---|---|
| `pandas` | Building the weekly tables and exporting CSVs |
| `numpy` | Generating the seeded random variation in the simulated actuals |
| `statsmodels` | Exponential smoothing (Holt-Winters) |

## How to Run

1. Install Python 3.13 and the dependencies listed in `pyproject.toml` (or run `pip install pandas numpy statsmodels`).
2. Build the history and baseline, the rolling forecast, then the scenario:
   ```
   python build_baseline.py
   python rolling_forecast.py
   python bad_harvest_scenario.py
   ```
   This creates the four CSV files in the project folder. All runs are reproducible.
3. Open `terrastride_forecast_dashboard.pbix` in Power BI Desktop. It includes the data, so no refresh is needed to view it.

## About the Data

The weekly actuals are simulated with a fixed random seed:
- **Traffic:** 50,000 sessions/month in Jan 2025, growing 3% monthly, with holiday lifts of +60% in November and +40% in December.
- **Sales:** 2.5% conversion, 10% lower during the holidays, and a $120 average order value.
- **Variation:** random swings in traffic (−8% to +4%), conversion (±5%) and order value (±3%).

The forecast never sees these assumptions. It learns growth and seasonality from the history alone.

**Tools:** Python (pandas, NumPy, statsmodels) · Power BI · Positron · Git/GitHub
