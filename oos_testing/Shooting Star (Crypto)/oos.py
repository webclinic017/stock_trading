import pandas as pd
import multiprocessing as mp
from datetime import datetime as dt
from dateutil.relativedelta import relativedelta
import numpy as np

def get_data(symbol, start_date, end_date, period, load_quotes=True):
    
    prices = pd.read_csv("/gws/nopw/j04/hiresgw/dg/crypto_minute_data/" + symbol + "_prices.csv")
    quotes = pd.read_csv("/gws/nopw/j04/hiresgw/dg/crypto_minute_quotes/" + symbol + "_quotes.csv")
    
    prices = prices[prices["exchange"] == "CBSE"]
    
    prices["timestamp"] = pd.to_datetime(prices["timestamp"], utc=True)
    prices = prices.set_index("timestamp")
    prices = prices.tz_convert('US/Eastern')
    prices = prices.sort_index()
    
    if period > 1:
        
        opens = prices["open"].resample(str(period) + "min").first()
        closes = prices["close"].resample(str(period) + "min").last()
        highs = prices["high"].resample(str(period) + "min").max()
        lows = prices["low"].resample(str(period) + "min").min()
        vols = prices["volume"].resample(str(period) + "min").sum()
        
        prices = pd.DataFrame([opens, highs, lows, closes, vols]).T
    
    prices = prices.loc[start_date:end_date]
    
    if load_quotes == False:
        return prices, None
    
    quotes["timestamp"] = pd.to_datetime(quotes["timestamp"], utc=True)
    quotes = quotes.set_index("timestamp")
    quotes = quotes.tz_convert('US/Eastern')
    quotes = quotes.sort_index()
    
    quotes = quotes.loc[start_date:end_date]
    
    return prices, quotes

def load_data(symbol, start_date, end_date, period, load_quotes):
    
    prices, quotes = get_data(symbol, start_date, end_date, period, load_quotes=True)
    
    return prices, quotes, symbol, period
    
def simulation(prices, quotes, shadow_length, median_diff, diff_scaling):
    
    quotes["diff"] = quotes["median_ask_price"] - quotes["median_bid_price"]
    
    all_data = prices.join(quotes).dropna()
    
    open_trades = []
    close_trades = []
    
    for row in range(1, len(all_data)-1):
        
        index = all_data.index.values[row]
        values = all_data.iloc[row]
        open_price = values.open
        close_price = values.close
        high_price = values.high
        low_price = values.low
        prev_diff = all_data.iloc[row-1]["diff"]
        
        body_length = abs(open_price - close_price)
        if open_price <= close_price:
            upper_wick_length = abs(high_price - close_price)
            lower_wick_length = abs(open_price - low_price)
        elif open_price > close_price:
            upper_wick_length = abs(high_price - open_price)
            lower_wick_length = abs(close_price - low_price)

        if close_price > open_price and close_price == high_price and lower_wick_length * shadow_length > body_length and prev_diff < median_diff * diff_scaling:
            if len(open_trades) == len(close_trades):
                open_trades.append([index, all_data.iloc[row+1].median_ask_price])
                
        if close_price < open_price and close_price == low_price and upper_wick_length * shadow_length > body_length:
            if len(open_trades) - 1 == len(close_trades):
                close_trades.append([index, all_data.iloc[row+1].median_bid_price])
        
    if len(open_trades) - 1 == len(close_trades):
        open_trades = open_trades[:-1]
        
    return open_trades, close_trades

def log_trades(open_trades, close_trades, path=None):
    
    logs = []
    for i in range(len(open_trades)):
        logs.append([str(open_trades[i][0]), str(close_trades[i][0]), symbol, "LONG", open_trades[i][1], close_trades[i][1]])
        
    history = pd.DataFrame(logs)
    history.columns = ["Entry Time", "Exit Time", "Symbol", "Direction", "Entry", "Exit"]
    
    history["Entry Time"] = pd.Index(pd.to_datetime(history["Entry Time"]))
    history["Exit Time"] = pd.Index(pd.to_datetime(history["Exit Time"]))

    if path != None:
        history.to_csv(path)
        
    return history
    
def get_backtest(df, money_per_trade, commission):
    
    sizes = []
    returns = []

    for i in range(len(df)):
        
        entry_price = df.loc[i]["Entry"]
        exit_price = df.loc[i]["Exit"]
        direction = df.loc[i]["Direction"]
        
        if entry_price == 0 or exit_price == 0:
            sizes.append(0)
            returns.append(0)
            continue
        
        size = money_per_trade/entry_price
        ret = size * (exit_price - entry_price)
        if direction == "SHORT":
            ret = -ret
            
        sizes.append(size)
        returns.append(ret)
    
    df["Size"] = np.array(sizes)
    df["Return"] = np.array(returns) - commission
    df["Accum Returns"] = df["Return"].cumsum()
    
    return df
    
if __name__ == "__main__":
    
    init_month = 8
    init_year = 2021
    
    end_month = 4
    end_year = 2022
    
    start_date = str(init_year) + "-" + str(init_month).zfill(2) + "-01" 
    end_date = str(end_year) + "-" + str(end_month).zfill(2) + "-01" 
    
    symbols = ["LTCUSD", "BTCUSD", "BCHUSD", "ETHUSD"]
    periods = [1, 2, 3, 4, 5, 10, 15, 20, 30, 45, 60, 120, 240, 360]
    diffs = [1, 2, 3, 4, 5, 10, 25, 50, 100, 250, 500, 1000]
    
    diff_stats = pd.read_csv("diff_stats.csv")
    diff_stats = diff_stats.set_index("Unnamed: 0")
    
    inputs = []
    for period_i, period in enumerate(periods):
        if period_i == 0:
            for symbol in symbols:
                inputs.append([symbol, start_date, end_date, period, True])
        else:
            for symbol in symbols:
                inputs.append([symbol, start_date, end_date, period, False])
    
    print("Loading data...")
    pool = mp.Pool(len(inputs))
    results = pool.starmap(load_data, inputs, chunksize=1)
    pool.close()
    print("Finished loading data.")
    
    prices = {}
    quotes = {}
    
    for res in results:
        price, quote, symbol, period = res
        prices[(symbol, period)] = price
        quotes[symbol] = quote
    
    curr_date = dt(init_year, init_month, 1) + relativedelta(months=1)
    end_date = dt(end_year, end_month, 1) - relativedelta(months=1)
    
    oos_open_trades = []
    oos_close_trades = []
    while curr_date <= end_date:
        
        prev_date = curr_date - relativedelta(months=1)
        next_date = curr_date + relativedelta(months=1)
        
        period_prev_date = str(prev_date.year) + "-" + str(prev_date.month).zfill(2) + "-01"
        period_start_date = str(curr_date.year) + "-" + str(curr_date.month).zfill(2) + "-01"
        period_end_date = str(next_date.year) + "-" + str(next_date.month).zfill(2) + "-01" 
    
        print("Processing " + str(prev_date.month).zfill(2) + "-" + str(prev_date.year))
        
        returns_period = []
        
        for symbol in symbols:
            
            median_diff = diff_stats.loc[symbol]["50th"]
            for period in periods:
                period_prices = prices[(symbol, period)].loc[period_prev_date:period_start_date]
                for diff in diffs:
                    #print("Processing", symbol, period, diff)
                    open_trades, close_trades = simulation(period_prices, quotes[symbol], 1, median_diff, diff)
                    
                    if len(open_trades) > 0:
                        history = log_trades(open_trades, close_trades)
                        accum_returns = get_backtest(history, 1000, 0)["Accum Returns"].values[-1]
                        returns_period.append([symbol, period, diff, accum_returns])
                    else:
                        returns_period.append([symbol, period, diff, 0])
                        
        returns_period = pd.DataFrame(returns_period, columns=["symbol", "period", "diff_scaling", "accum_returns"])
        returns_period = returns_period.sort_values(by=['accum_returns'], ascending=False)

        print("Settings for " + str(prev_date.month).zfill(2) + "-" + str(prev_date.year), returns_period["symbol"].values[0], returns_period["period"].values[0], returns_period["diff_scaling"].values[0], returns_period["accum_returns"].values[0])
        
        best_symbol = returns_period["symbol"].values[0]
        best_period = returns_period["period"].values[0]
        best_diff = returns_period["diff_scaling"].values[0]
        median_diff = diff_stats.loc[best_symbol]["50th"]
        period_prices = prices[(best_symbol, best_period)].loc[period_start_date:period_end_date]
        
        open_trades, close_trades = simulation(period_prices, quotes[best_symbol], 1, median_diff, best_diff)
        
        for trade in range(len(open_trades)):
            oos_open_trades.append(open_trades[trade])
            oos_close_trades.append(close_trades[trade])
            
        curr_date += relativedelta(months=1)
        
    log_trades(oos_open_trades, oos_close_trades, path="oos.csv")