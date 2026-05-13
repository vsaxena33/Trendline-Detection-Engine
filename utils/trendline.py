"""
================================================================================
REAL-TIME SUPPORT & RESISTANCE DETECTION ENGINE
================================================================================

This program creates a real-time candlestick chart using live market data
from the FYERS WebSocket API and automatically detects support and
resistance trendline zones using the `trendln` library.

The system continuously receives live tick-by-tick market data and:

1. Builds real-time OHLCV candles
   (Open, High, Low, Close, Volume).

2. Detects important market structure using:
   - Swing highs
   - Swing lows
   - Trendlines
   - Support zones
   - Resistance zones

3. Dynamically updates trendline zones as new candles form.

4. Identifies whether support/resistance structures are:
   - Active
   - Valid
   - Broken

5. Displays a live candlestick chart with real-time
   support and resistance regions.

The project demonstrates important concepts used in:
- Quantitative Trading
- Technical Analysis
- Real-Time Data Engineering
- WebSocket Streaming
- Algorithmic Trading Systems
- Market Structure Analysis

Libraries Used:
- FYERS API
- pandas
- mplfinance
- matplotlib
- trendln
- numpy

Author: Vaibhav Saxena
================================================================================
"""


# ============================================================
# Imports
# ============================================================
from fyers_apiv3.FyersWebsocket import data_ws
from fyers_apiv3 import fyersModel
from credentials import client_id
import datetime as dt
import pandas as pd
import pytz
import matplotlib.pyplot as plt
import mplfinance as mpf
from matplotlib.animation import FuncAnimation
import trendln
import math
import numpy as np


# ============================================================
# Configuration
# ============================================================
symbol = 'NSE:RELIANCE-EQ'
timeZone = 'Asia/Kolkata'
max_candles = 100
plot_window = 100
resolution = "1"


# ============================================================
# Update Logic for Live Data
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
        sd = math.sqrt(result[2])

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
            if df['low'].iloc[i] + 2*sd < val and type == 'support':
                is_active = False
                break
            elif df['high'].iloc[i] - 2*sd > val and type == 'resistance':
                is_active = False
                break

            upper[i] = val + sd * 3
            lower[i] = val - sd * 3

        trendlines.append((points, upper, lower, is_active))

    return trendlines


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
    timestamp = pd.Timestamp.now(tz=timeZone).floor('1min')

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
        data = data.tail(max_candles).copy()

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


# ============================================================
# Plotting the Candlestick Chart
# ============================================================
def plot_chart(candlestick):
    """
    This function handles the 'UI' (User Interface). 
    It creates the window and draws the candles.
    """
    # Create a figure with two parts: Ax (Price chart) and Ax_vol (Volume bars at bottom)
    fig, (ax, ax_vol) = plt.subplots(2, 1, figsize=(10, 6),sharex=True, gridspec_kw={'height_ratios': [3, 1]})

    def animate(i):
        ax.clear()
        ax_vol.clear()

        data_to_plot = candlestick.data.tail(plot_window).copy()

        ohlcv_cols = ['open', 'high', 'low', 'close', 'volume']
        trendline_cols = [c for c in data_to_plot.columns if c not in ohlcv_cols]
        plot_data = data_to_plot[ohlcv_cols]

        # Plot candlesticks first (no addplot needed)
        mpf.plot(
            plot_data,
            type='candle',
            style='charles',
            ax=ax,
            volume=ax_vol,
            ylabel='Price',
        )

        # mplfinance uses integer x positions internally (0, 1, 2, ...)
        # but only plots non-NaN candles, so we need to map our data indices
        # to the actual rendered x positions
        n = len(plot_data)
        x = np.arange(n)

        # Draw shaded bands AFTER mpf.plot so they sit on top
        for col in trendline_cols:
            if not col.endswith(' upper'):
                continue
            base = col.replace(' upper', '')
            lower_col = base + ' lower'
            if lower_col not in data_to_plot.columns:
                continue

            upper_vals = data_to_plot[col].values
            lower_vals = data_to_plot[lower_col].values

            # We only shade areas where both upper and lower
            # boundaries actually exist.
            #
            # NaN values mean the trendline is inactive
            # or outside the valid region.
            valid = ~np.isnan(upper_vals) & ~np.isnan(lower_vals)
            if not valid.any():
                continue

            color = 'green' if col.startswith('support') else 'red'

            ax.fill_between(
                x,
                lower_vals,
                upper_vals,
                where=valid,
                alpha=0.15,
                color=color,
                zorder=2,       # Draw above candles
            )

        ax.set_title(f'{symbol} Real-Time Candlestick Chart')
    
    # Start the animation loop
    ani = FuncAnimation(
        fig,
        animate,
        interval=1000,
        cache_frame_data=False
    )

    plt.show()


# ============================================================
# Historical Data Fetching
# ============================================================
def fetch_historical_data(fyers: fyersModel.FyersModel) -> pd.DataFrame:
    """
    Before starting the live chart, we need to know what happened earlier 
    in the day so the chart doesn't start from a blank screen.
    """
    
    now = dt.datetime.now(pytz.timezone(timeZone))

    start_of_day = now.replace(hour=0, minute=0, second=0, microsecond=0)

    previous_time = start_of_day.timestamp()
    current_time = now.timestamp()

    nifty_data = {
        "symbol": symbol,
        "resolution": resolution,
        "date_format": "0",
        "range_from": int(previous_time),
        "range_to": int(current_time),
        "cont_flag": "1"
    }

    # Ask Fyers for the data and convert it into an Excel-like table (DataFrame)
    response = fyers.history(data=nifty_data)
    historical_data = response['candles']
    df = pd.DataFrame(historical_data, columns=['date', 'open', 'high', 'low', 'close', 'volume'])
    
    # Fix the time format so humans and computers can read it easily
    df['date'] = pd.to_datetime(df['date'], unit='s')
    df['date'] = df['date'].dt.tz_localize('UTC').dt.tz_convert(pytz.timezone(timeZone))
    df.set_index('date', inplace=True)
    return df


# ============================================================
# Candlestick Class to Manage State and WebSocket Callbacks
# ============================================================
class Candlestick:
    """
    This class acts like a real-time market data manager.

    Responsibilities:
    - Receives live market ticks from the websocket.
    - Updates candles continuously.
    - Stores latest market state in memory.
    - Maintains live support/resistance structures.

    Think of this class as the "brain"
    controlling the live chart.
    """
    # ============================================================
    # Initialization
    # ============================================================
    def __init__(self, data):
        """
        Initializes the Candlestick class.
        """
        self.data = data
        self.last_total_volume = None


    # ============================================================
    # WebSocket Callback to Handle Incoming Messages
    # ============================================================
    def onmessage(self, message):
        """
        Callback function to handle incoming messages from the FyersDataSocket WebSocket.

        Parameters:
            message (dict): The received message from the WebSocket.

        """
        self.data, self.last_total_volume = update_live_data(data=self.data, message=message, last_total_volume=self.last_total_volume)
        print(self.data.tail())


    # ============================================================
    # Websocket Callback to Handle Errors Events
    # ============================================================
    def onerror(self, message):
        """
        Callback function to handle WebSocket errors.

        Parameters:
            message (dict): The error message received from the WebSocket.


        """
        print("Error:", message)


    # ============================================================
    # Websocket Callback to Handle Connection Close Events
    # ============================================================
    def onclose(self, message):
        """
        Callback function to handle WebSocket connection close events.
        """
        print("Connection closed:", message)


    # ============================================================
    # Websocket Callback to Handle Subscription Upon Connection
    # ============================================================
    def onopen(self):
        """
        Callback function to subscribe to data type and symbols upon WebSocket connection.

        """
        # Specify the data type and symbols you want to subscribe to
        data_type = "SymbolUpdate"

        # Subscribe to the specified symbols and data type
        symbols = [symbol]
        fyersSocket.subscribe(symbols=symbols, data_type=data_type)

        # Keep the socket running to receive real-time data
        fyersSocket.keep_running()


# ============================================================
# STARTING THE PROGRAM
# ============================================================
if __name__ == "__main__":
    '''
    ============================================================
    HOW THE SYSTEM WORKS
    ============================================================
    
    WebSocket Tick
           ↓
    Update Current Candle
           ↓
    Candle Closes
           ↓
    Detect Support & Resistance
           ↓
    Validate Active Trendlines
           ↓
    Draw Real-Time Zones
    
    ============================================================
    '''
    
    # 1. Read your secret keys (Like a password for the stock market)
    try:
        with open('access_token.txt', 'r') as file:
            access_token = file.read()
    except FileNotFoundError:
        print("Error: access_token.txt not found! Please login first.")
        exit()

    # 2. Fetch data from earlier today
    print("Fetching morning data...")
    fyers_connection = fyersModel.FyersModel(client_id=client_id, token=access_token, is_async=False, log_path='')
    historical_df = fetch_historical_data(fyers=fyers_connection)

    # 3. Initialize our data manager
    candlestick = Candlestick(historical_df)

    # 4. Create a FyersDataSocket instance with the provided parameters
    fyersSocket = data_ws.FyersDataSocket(
        access_token=access_token,          # Access token in the format "appid:accesstoken"
        log_path="",                        # Path to save logs. Leave empty to auto-create logs in the current directory.
        litemode=False,                     # Lite mode disabled. Set to True if you want a lite response.
        write_to_file=False,                # Save response in a log file instead of printing it.
        reconnect=True,                     # Enable auto-reconnection to WebSocket on disconnection.
        on_connect=candlestick.onopen,      # Callback function to subscribe to data upon connection.
        on_close=candlestick.onclose,       # Callback function to handle WebSocket connection close events.
        on_error=candlestick.onerror,       # Callback function to handle WebSocket errors.
        on_message=candlestick.onmessage    # Callback function to handle incoming messages from the WebSocket.
    )

    # 5. Establish a connection to the Fyers WebSocket
    print("Connecting to live stream...")
    fyersSocket.connect()

    # 6. Plot the chart
    try:
        plot_chart(candlestick)
    finally:
        fyersSocket.close_connection()
