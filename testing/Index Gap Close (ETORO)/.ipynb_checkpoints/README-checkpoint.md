## Index Gap Close (ETORO)

Each index closes (some of the) gap between open and previous close. Inspired by Chapter 6 of Mastering the Trade by John Carter.

Variations:
- variation1: enter on day open; exit as gap is closed; sl is `max_sl`% of gap; tp is `max_tp`% of gap; don't trade if gap is smaller than `no_trade_min` or larger than `no_trade_max`. Exit trade at `exit_time` time periods (minutes) before EOD.   
        - symbol = symbol to be traded
        - max_sl = % of gap at which stop loss is to be placed
        - max_tp = % of gap at which take profit is to be placed
        - exit_time = timestep at which to close trade if still in the market
        - no_trade_min = gap size (in % via last close) has to be greater than this for a trade to be entered 
        - no_trade_max = gap size (in % via last close) has to be smaller than this for a trade to be entered
- **variation1b: go long the gap, whichever direction it is in**
- variation1c: go long the gap if $SMA_{t-1}$ > $SMA_{t-2}$, else go short, `ma_length`is the MA period
- variation1d: go long the gap if $SMA_{t-1}$ > $SMA_{t-2}$ and lower open, go short the gap if $SMA_{t-1}$ > $SMA_{t-2}$ and higher open, `ma_length`is the MA period
- variation1e: go long the gap, whichever direction it is in, if $SMA_{t-1}$ > $SMA_{t-2}$

- variation2: enter on day open; exit as gap is closed; if gap is less than `tp_limit`, tp is whole gap, sl is `max_sl`% of gap, otherwise tp and sl are equidistant from open as `tp_perc` of gap
        - symbol = symbol to be traded
        - exit_time = timestep at which to close trade if still in the market
        - no_trade_min = gap size (in % via last close) has to be greater than this for a trade to be entered 
        - tp_limit = limit at which to switch regimes (% vs previous close)
        - tp_perc = % of gap at which take profit is to be placed
        - sl_perc = % of gap at which stop loss is to be placed
- variation2b: go long the gap, whichever direction it is in
- variation2c: go long the gap if $SMA_{t-1}$ > $SMA_{t-2}$, else go short, `ma_length`is the MA period
- variation2d: go long the gap if $SMA_{t-1}$ > $SMA_{t-2}$ and lower open, go short the gap if $SMA_{t-1}$ > $SMA_{t-2}$ and higher open, `ma_length`is the MA period
- variation2e: go long the gap, whichever direction it is in, if $SMA_{t-1}$ > $SMA_{t-2}$
   
Folders:
- Each variation will have some sensitivity tests done for each of their parameters. Each set of tests have their own folder
- checks: running each variation for 01/01/2022 to 11/05/2022 to verify signals
   
