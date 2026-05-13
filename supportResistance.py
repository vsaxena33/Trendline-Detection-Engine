# ============================================================
# Imports
# ============================================================
import trendln

# ============================================================
# Support and Resistance
# ============================================================
def support_resistance(df):
    """
    Detect support and resistance trendlines from market data.

    This function uses the `trendln` library to identify important
    price structures in the market.

    Support lines are created using candle LOW prices.
    Resistance lines are created using candle HIGH prices.

    The library first:
    1. Finds local swing highs and swing lows.
    2. Creates possible trendlines.
    3. Ranks the best trendlines mathematically.

    We only return the latest window because recent market structure
    is more useful for real-time trading than old historical structure.

    Parameters
    ----------
    df : pandas.DataFrame
        OHLCV candlestick dataframe.

    Returns
    -------
    tuple
        Latest support trendlines and resistance trendlines.
    """
    
    (minimaIdxs, pmin, mintrend, minwindows),(maximaIdxs, pmax, maxtrend, maxwindows) = trendln.calc_support_resistance(
        (df['low'].to_numpy(), df['high'].to_numpy()),
        extmethod=trendln.METHOD_NUMDIFF,
        method=trendln.METHOD_NSQUREDLOGN,
        window=50,
        errpct=0.003)

    return minwindows[-1], maxwindows[-1]