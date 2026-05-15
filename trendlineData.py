# ============================================================
# Imports
# ============================================================
import math
import numpy as np


# ============================================================
# Return Trendline
# ============================================================
def generate_trendline_data(df, trend_data, type):
    """
    Converts trendln output into mplfinance-compatible line data.
    
    Parameters
    ----------
    df : DataFrame
        OHLC dataframe
    
    trend_data : list
        mintrend or maxtrend from trendln
    
    Returns
    -------
    list
        List of mplfinance addplot objects
    """

    trendlines = []

    for points, result in trend_data:

        if len(points) < 2:
            continue

        slope = result[0]
        intercept = result[1]

        # trendln returns SSR (Sum of Squared Residuals),
        # which measures how far points are from the trendline.
        #
        # We convert it into a rough standard deviation estimate
        # so we can create a support/resistance "zone"
        # instead of a single thin line.
        sd = math.sqrt(result[2] / len(points)

        # We create two arrays:
        #
        # upper -> top boundary of support/resistance zone
        # lower -> bottom boundary of support/resistance zone
        #
        # np.nan means "empty value".
        # This helps matplotlib avoid drawing unwanted lines.
        upper = np.full(len(df), np.nan)
        lower = np.full(len(df), np.nan)

        start = min(points)
        end = len(df) - 1

        # A trendline is considered ACTIVE only while price respects it.
        # 
        # Example:
        # - A support zone should stay below price.
        # - A resistance zone should stay above price.
        #
        # If price strongly breaks through the zone,
        # we mark the trendline as invalid.
        is_active = True

        for i in range(start, end + 1):

            val = slope * i + intercept

            # If price breaks too far beyond the zone,
            # the trendline is no longer valid.
            #
            # Example:
            # - If price falls below support strongly,
            #   support has failed.
            #
            # - If price rises above resistance strongly,
            #   resistance has failed.
            if df['low'].iloc[i] + 3 * sd < val and type == 'support':
                is_active = False
                break
            elif df['high'].iloc[i] - 3 * sd > val and type == 'resistance':
                is_active = False
                break

            upper[i] = val + sd * 3
            lower[i] = val - sd * 3

        trendlines.append((points, upper, lower, is_active))

    return trendlines
