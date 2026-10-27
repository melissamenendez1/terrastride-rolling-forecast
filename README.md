# TerraStride Co.: Driver-Based Rolling Forecast

A 12-month rolling forecast built in Python, with a Power BI dashboard, for a fictional direct-to-consumer sneaker brand. Revenue and operating costs are calculated from traffic, sales and cost drivers rather than projected from past trends. A second scenario stress-tests the business against a supply shock: a crop failure that cuts production of its plant-based leather.

> **Note:** TerraStride Co., its suppliers (Cactex, Ananatex) and all data are fictional. Actual results are simulated, and all assumptions are illustrative.

**Portfolio write-up:** [Notion page](https://app.notion.com/p/melissamenendez/TerraStride-Co-Dynamic-Driver-Based-Rolling-Forecast-Model-3e6f1fbe1c7f80068743f3547447bf5c?source=copy_link)

---

## How the Model Works

**Driver chain:** Website Sessions → Conversion Rate → Orders → Average Order Value → Revenue → COGS → Gross Profit → Operating Income

| Group | Driver | Assumption |
|---|---|---|
| Traffic | Starting traffic | 50,000 sessions/month, growing 3% monthly |
| Traffic | Holiday seasonality | November +60%, December +40% (assumed) |
| Traffic | Traffic mix | 40% organic, 60% paid |
| Sales | Conversion rate | 2.5%, dipping to 2.25% in Nov–Dec (assumed) |
| Sales | Average order value | $120 |
| Cost | Unit COGS | $52 (Cactex $28, Ananatex $14, packaging $10) |
| Cost | Cost per click | $0.45 per paid session |
| Cost | Fixed overhead | $15,000/month, rising 1% monthly |

- **Rolling forecast:** 24 monthly versions (Jan 2025–Dec 2026). Each version locks closed months as actuals and re-anchors traffic, conversion and order value to the **average of the last three closed months** before projecting forward.
- **Simulated actuals:** the plan with seeded random variation in traffic (−8% to +4%), conversion (±5%) and order value (±3%), so results are reproducible.
- **Single engine:** one function calculates every month for both actuals and forecasts, so the math is written once.

## Scenarios

| Scenario | Description |
|---|---|
| **Normal** | No disruption |
| **Bad Harvest** | January–June 2026: Ananatex fiber costs +25%, production capped at 1,100 pairs/month |

The shock is defined in a settings dictionary (`CROP_SHOCK_SETTINGS`), so other scenarios can be tested without changing the calculation code. The Bad Harvest scenario is a stress test: forecasts assume the shock is known in advance, isolating its full cost.

## Key Results

- **Forecast outlook (Jan 2026 version):** $3.11M revenue, 1.10M sessions, 26.3K orders and $1.24M operating income over the next 12 months.
- **Anchoring design:** averaging the last three months cut the average forecast miss from 5.5% (single-month anchor) to 4.2%.
- **Bad Harvest impact:** $554,005 in lost revenue and 4,587 lost orders; gross margin fell from 56.46% to 54.05%, and CAC rose 66% ($15.81 → $26.25).

---

## Repository Contents

| File | Description |
|---|---|
| `generate_model.py` | Builds the forecast and both scenarios, and exports the CSVs |
| `terrastride_forecast_normal.csv` | Normal scenario output (24 versions) |
| `terrastride_forecast_bad_harvest.csv` | Bad Harvest scenario output (24 versions) |
| `terrastride_forecast_dashboard.pbix` | Power BI dashboard (Normal Forecast and Bad Harvest pages) |
| `pyproject.toml` | Project metadata and Python dependencies |

## Dependencies

All Python dependencies are used by `generate_model.py`:

| Library | Used for |
|---|---|
| `pandas` | Building the forecast tables and exporting CSVs |
| `numpy` | Generating the seeded random variation for simulated actuals |

The dashboard requires **Power BI Desktop** (Windows). It is not a Python dependency.

## How to Run

1. Install Python 3.13 and the dependencies listed in `pyproject.toml` (or run `pip install pandas numpy`).
2. Run the script:
   ```
   python generate_model.py
   ```
   This creates the two CSV files in the project folder.
3. Open `terrastride_forecast_dashboard.pbix` in Power BI Desktop.
4. If Power BI cannot find the CSVs, update their location under **Transform data → Data source settings**, then click **Refresh**.

## Next Phase

Cash flow modeling: adding inventory purchases and supplier payment timing to estimate the emergency funding needed during the Bad Harvest.

**Tools:** Python (pandas, NumPy) · Positron · Power BI · Git/GitHub