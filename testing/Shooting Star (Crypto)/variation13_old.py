import pandas as pd
import numpy as np
from datetime import datetime as dt
from datetime import timedelta as td
import sys
from alpaca_trade_api.rest import REST, TimeFrame, TimeFrameUnit
    
def get_data(symbol, start_date, end_date, period):
    
    prices = pd.read_csv("/home/users/dgalea/stock_trading/data/crypto_minute_data/" + symbol + "_prices.csv")
    quotes = pd.read_csv("/home/users/dgalea/stock_trading/data/crypto_minute_quotes/" + symbol + "_quotes.csv")
    
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

def simulate_one_type(prices, quotes, shadow_length, diff_limit, init_data, end_date):
    
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

    if len(open_trades) - 1 == len(close_trades):
        open_trades = open_trades[:-1]
        
    
def simulation(prices, quotes, secondary_prices, secondary_quotes, shadow_length, diff_limit):
    
    quotes["diff"] = quotes["median_ask_price"] - quotes["median_bid_price"]
    
    all_data = prices.join(quotes).dropna()
    secondary_all_data = secondary_prices.join(secondary_quotes).dropna()
    
    daily_data["ma"] = daily_data["close"].rolling(20).mean()
    
    open_trades = []
    close_trades = []
    
    type_flag = False
    for row in range(1, len(all_data)-1):
        
        prev_diff = all_data.iloc[row-1]["diff"]
        
        if prev_diff < diff_limit:
            
            short_data = all_data[row:]
            short_data = short_data.loc[:all_data.index.values[row]]
            
        else:
            
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
    diff_limit = 100
    secondary_period = 360
    
    prices, quotes = get_data(symbol, start_date, end_date, period)
    secondary_prices, secondary_quotes = get_data(symbol, start_date, end_date, secondary_period)
    
    open_trades, close_trades = simulation(prices, quotes, secondary_prices, secondary_quotes, shadow_length, diff_limit)
    
    log_trades(open_trades, close_trades, symbol)
    