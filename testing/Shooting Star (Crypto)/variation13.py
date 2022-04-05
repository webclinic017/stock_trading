import pandas as pd
import numpy as np
from datetime import datetime as dt
import sys

def get_data(symbol, start_date, end_date, period):
    
    prices = pd.read_csv("/gws/nopw/j04/hiresgw/dg/crypto_minute_data/" + symbol + "_prices.csv")#[600000:1000000]
    quotes = pd.read_csv("/gws/nopw/j04/hiresgw/dg/crypto_minute_quotes/" + symbol + "_quotes.csv")#[3000000:4500000]
    
    prices = prices[prices["exchange"] == "CBSE"]
    
    prices["timestamp"] = pd.to_datetime(prices["timestamp"], utc=True)
    prices = prices.set_index("timestamp")
    prices = prices.tz_convert('US/Eastern')
    prices = prices.sort_index()
    
    quotes["timestamp"] = pd.to_datetime(quotes["timestamp"], utc=True)
    quotes = quotes.set_index("timestamp")
    quotes = quotes.tz_convert('US/Eastern')
    quotes = quotes.sort_index()
    
    if period > 1:
        
        opens = prices["open"].resample(str(period) + "min").first()
        closes = prices["close"].resample(str(period) + "min").last()
        highs = prices["high"].resample(str(period) + "min").max()
        lows = prices["low"].resample(str(period) + "min").min()
        vols = prices["volume"].resample(str(period) + "min").sum()
        
        prices = pd.DataFrame([opens, highs, lows, closes, vols]).T
    
    prices = prices.loc[start_date:end_date]
    quotes = quotes.loc[start_date:end_date]
    
    return prices, quotes
    
def simulate_secondary_type(all_data, open_trades, close_trades, init_date):
    
    init_trades = len(open_trades)
    
    all_data = all_data.iloc[init_date:]
    
    for row in range(len(all_data)-1):
    
        index = all_data.index.values[row]
        values = all_data.iloc[row]
        open_price = values.open
        close_price = values.close
        high_price = values.high
        low_price = values.low

        body_length = abs(open_price - close_price)
        if open_price <= close_price:
            upper_wick_length = abs(high_price - close_price)
            lower_wick_length = abs(open_price - low_price)
        elif open_price > close_price:
            upper_wick_length = abs(high_price - open_price)
            lower_wick_length = abs(close_price - low_price)

        if close_price > open_price and close_price == high_price and lower_wick_length * shadow_length > body_length:
            if len(open_trades) == len(close_trades):
                open_trades.append([index, all_data.iloc[row+1].median_ask_price])
                
        if close_price < open_price and close_price == low_price and upper_wick_length * shadow_length > body_length:
            if len(open_trades) - 1 == len(close_trades):
                close_trades.append([index, all_data.iloc[row+1].median_bid_price])
                
        if len(close_trades) == (init_trades + 1):
            break

    return open_trades, close_trades, index
    
def simulation(prices, quotes, secondary_prices, secondary_quotes, shadow_length, diff_limit):
    
    quotes["diff"] = quotes["median_ask_price"] - quotes["median_bid_price"]
    
    all_data = prices.join(quotes).dropna()
    secondary_data = secondary_prices.join(secondary_quotes).dropna()
    
    open_trades = []
    close_trades = []
    
    for row in range(len(all_data)-1):
        
        prev_diff = all_data.iloc[row-1]["diff"]
        
        index = all_data.index.values[row]
        values = all_data.iloc[row]
        open_price = values.open
        close_price = values.close
        high_price = values.high
        low_price = values.low

        body_length = abs(open_price - close_price)
        if open_price <= close_price:
            upper_wick_length = abs(high_price - close_price)
            lower_wick_length = abs(open_price - low_price)
        elif open_price > close_price:
            upper_wick_length = abs(high_price - open_price)
            lower_wick_length = abs(close_price - low_price)

        if close_price < open_price and close_price == low_price and upper_wick_length * shadow_length > body_length:
            if len(open_trades) - 1 == len(close_trades):
                close_trades.append([index, all_data.iloc[row+1].median_bid_price])
                continue

        if prev_diff < diff_limit:

            if close_price > open_price and close_price == high_price and lower_wick_length * shadow_length > body_length:
                if len(open_trades) == len(close_trades):
                    open_trades.append([index, all_data.iloc[row+1].median_ask_price])

        else:
            print(index)
            
            index_str = str(index.year) + "-" + str(index.month).zfill(2) + "-" + str(index.day).zfill(2) + " " + str(index.hour).zfill(2) + ":" + str(index.minute).zfill(2) + ":00"
            
            open_trades, close_trades, end_time = simulate_secondary_type(secondary_data, open_trades, close_trades, init_date)
            
            end_time = str(end_time.year) + "-" + str(end_time.month).zfill(2) + "-" + str(end_time.day).zfill(2) + " " + str(end_time.hour).zfill(2) + ":" + str(end_time.minute).zfill(2) + ":00"
            
            row = list(np.where(all_data.index == end_time)[0])[0]
        
    if len(open_trades) - 1 == len(close_trades):
        open_trades = open_trades[:-1]
        
    return open_trades, close_trades
        
def log_trades(open_trades, close_trades, symbol):
    
    logs = []
    for i in range(len(open_trades)):
        logs.append([str(open_trades[i][0]), str(close_trades[i][0]), symbol, "LONG", open_trades[i][1], close_trades[i][1]])
        
    history = pd.DataFrame(logs)
    history.columns = ["Entry Time", "Exit Time", "Symbol", "Direction", "Entry", "Exit"]
    
    history["Entry Time"] = pd.Index(pd.to_datetime(history["Entry Time"]))
    history["Exit Time"] = pd.Index(pd.to_datetime(history["Exit Time"]))
    
    history.to_csv(sys.argv[0].replace(".py", ".csv"))
    
if __name__ == "__main__":
    
    symbol = "BTCUSD"
    start_date = "2017-07-01"
    end_date = "2018-07-01"
    period = 15
    shadow_length = 1
    secondary_period = 120
    diff_limit = 100
    
    prices, quotes = get_data(symbol, start_date, end_date, period)
    secondary_prices, secondary_quotes = get_data(symbol, start_date, end_date, secondary_period)
    
    open_trades, close_trades = simulation(prices, quotes, secondary_prices, secondary_quotes, shadow_length, diff_limit)
    
    log_trades(open_trades, close_trades, symbol)
    