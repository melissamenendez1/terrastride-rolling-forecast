"""Exponential smoothing model shared by the 5-year baseline and the 13-week rolling forecast."""
import warnings

from statsmodels.tsa.holtwinters import ExponentialSmoothing
from statsmodels.tools.sm_exceptions import ConvergenceWarning

# Noisy weekly series occasionally trip the optimizer's convergence warning;
# the fitted parameters are still usable, so keep the console output clean
warnings.simplefilter("ignore", ConvergenceWarning)

# ==============================================================================
# MODEL SETTINGS
# ==============================================================================
LOOKBACK_WEEKS = 260         # 5 years of weekly history behind every fit
SEASONAL_PERIODS = 52        # Weekly data, yearly seasonality
FORECAST_HORIZON_WEEKS = 13  # Each rolling forecast looks 13 weeks ahead
ROLLING_VERSIONS = 13        # One rolling version per week for the last 13 closed weeks

ACTUALS_FILE = "terrastride_weekly_actuals.csv"


def calculate_revenue(sessions, cvr, aov):
    """Driver chain: Sessions → Conversion Rate → Orders → Average Order Value → Revenue."""
    sessions = int(sessions)
    orders = int(sessions * cvr)
    return {
        "Total_Sessions": sessions,
        "Conversion_Rate": round(cvr, 5),
        "Orders": orders,
        "Average_Order_Value": round(aov, 2),
        "Gross_Revenue": round(orders * aov, 2)
    }


def fit_driver_models(history):
    """
    Fits one exponential smoothing model per driver on a block of weekly actuals.

    Sessions:         Holt-Winters, multiplicative trend and seasonality
                      (compounding growth, holiday spikes that scale with the business).
    Conversion rate:  Holt-Winters, multiplicative seasonality, no trend (holiday dip).
    Order value:      simple exponential smoothing (no trend or seasonality).
    """
    return {
        "sessions": ExponentialSmoothing(
            history["Total_Sessions"].astype(float), trend="mul", seasonal="mul",
            seasonal_periods=SEASONAL_PERIODS, initialization_method="estimated"
        ).fit(),
        "cvr": ExponentialSmoothing(
            history["Conversion_Rate"], trend=None, seasonal="mul",
            seasonal_periods=SEASONAL_PERIODS, initialization_method="estimated"
        ).fit(),
        "aov": ExponentialSmoothing(
            history["Average_Order_Value"], trend=None, seasonal=None,
            initialization_method="estimated"
        ).fit()
    }
