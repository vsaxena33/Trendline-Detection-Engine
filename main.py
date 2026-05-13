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
import configuration as config
from newCandlestick import update_live_data
from plot import plot_chart
from historicalData import fetch_historical_data


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
        symbols = [config.symbol]
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