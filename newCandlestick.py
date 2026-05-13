# ============================================================
# Imports
# ============================================================
import pandas as pd
import configuration as config
from supportResistance import support_resistance
from trendlineData import generate_trendline_data


# ============================================================
# Update Logic for Live Data
# ============================================================
def update_live_data(data, message, last_total_volume):
    """
    Update the OHLCV dataframe using incoming websocket tick data.

    The websocket provides cumulative traded volume for the session.
    This function converts cumulative volume into incremental candle volume.

    Parameters
    ----------
    data : pandas.DataFrame
        Existing OHLCV dataframe indexed by timestamp.

    message : dict
        Incoming websocket tick message from Fyers.

    last_total_volume : int or None
        Previous cumulative traded volume received from websocket.

    Returns
    -------
    tuple
        Updated dataframe and latest cumulative traded volume.
    """

    # If the message is empty or broken, don't do anything
    if "symbol" not in message:
        return data, last_total_volume
    
    ltp = message.get('ltp')                            # LTP = Last Traded Price (The current market price)

    if ltp is None:
        return data, last_total_volume
    
    # Cumulative volume is the total shares traded since 9:15 AM. 
    # We want to find out how many were traded just in the last tick.
    total_vol = message.get('vol_traded_today')
    
    # Create a timestamp rounded to the current minute (e.g., 10:05:42 becomes 10:05:00)
    timestamp = pd.Timestamp.now(tz=config.timeZone).floor('1min')

    if total_vol is None:
        total_vol = last_total_volume if last_total_volume is not None else 0

    # The websocket gives TOTAL traded volume for the entire day.
    #
    # But each candle should only contain volume traded
    # during that specific minute.
    #
    # So:
    #
    # Incremental Volume = Current Total Volume - Previous Total Volume
    if last_total_volume is None:
        incremental_vol = 0
    else:
        incremental_vol = total_vol - last_total_volume

    if incremental_vol < 0:
        incremental_vol = 0

    # If the latest candle already belongs to the current minute,
    # we UPDATE the existing candle.
    #
    # Otherwise:
    # we CREATE a completely new candle.
    if len(data) > 0 and data.index[-1] == timestamp:
        # If we are still in the same minute, we update the existing candle
        data.iloc[-1, 3] = ltp                          # Close price continuously tracks latest traded price
        data.iloc[-1, 1] = max(data.iloc[-1, 1], ltp)   # Update High if price went higher
        data.iloc[-1, 2] = min(data.iloc[-1, 2], ltp)   # Update Low if price went lower
        data.iloc[-1, 4] += incremental_vol             # Add the new volume to the minute's total
    else:
        new_candle = pd.DataFrame(
            [{'open': ltp, 'high': ltp, 'low': ltp, 'close': ltp, 'volume': incremental_vol}],
            index=[timestamp]
        )

        # IMPORTANT:
        #
        # We calculate support/resistance ONLY when a candle closes.
        #
        # Why?
        #
        # During candle formation, price keeps moving rapidly.
        # This can create fake highs/lows and unstable trendlines.
        #
        # Closed candles provide more reliable market structure.
        # ✅ Step 1: Trim first, so index positions are stable
        data = data.tail(config.max_candles).copy()

        # ✅ Step 2: Drop stale trendline columns before recomputing
        trendline_cols = [c for c in data.columns if c.startswith('support:') or c.startswith('resistance:')]
        data = data.drop(columns=trendline_cols)

        # ✅ Step 3: Compute S/R on clean, trimmed, completed candles
        minwindows, maxwindows = support_resistance(df=data)
        print(minwindows)

        # ✅ Step 4: NOW append new candle (so trendline arrays are sized correctly)
        data = pd.concat([data, new_candle])

        support = generate_trendline_data(df=data, trend_data=minwindows, type='support')
        resistance = generate_trendline_data(df=data, trend_data=maxwindows, type='resistance')

        for points, upper, lower, is_active in support:
            if is_active:
                data[f'support: {points} upper'] = upper
                data[f'support: {points} lower'] = lower

        for points, upper, lower, is_active in resistance:
            if is_active:
                data[f'resistance: {points} upper'] = upper
                data[f'resistance: {points} lower'] = lower

    return data, total_vol