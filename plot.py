# ============================================================
# Imports
# ============================================================
import matplotlib.pyplot as plt
import mplfinance as mpf
from matplotlib.animation import FuncAnimation
import numpy as np
import configuration as config

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

        data_to_plot = candlestick.data.tail(config.plot_window).copy()

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

        ax.set_title(f'{config.symbol} Real-Time Candlestick Chart')
    
    # Start the animation loop
    ani = FuncAnimation(
        fig,
        animate,
        interval=1000,
        cache_frame_data=False
    )

    plt.show()