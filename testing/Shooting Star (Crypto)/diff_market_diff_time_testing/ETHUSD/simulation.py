from unittest import result
from alpaca_trade_api.rest import REST, TimeFrame, TimeFrameUnit
import pandas as pd
import numpy as np
from datetime import datetime as dt
from datetime import timedelta as td
import sys
sys.path.insert(0, "/Users/danielgalea/Documents/git/stock_trading") 
from common_funcs import load_credentials, process_quotes, log_trades
import multiprocessing as mp

def get_prices(api, symbol, start_date, end_date, period):

    prices = api.get_crypto_bars(symbol, TimeFrame.Minute, start_date, end_date).df
    prices = prices.tz_convert('US/Eastern')
    prices = prices[prices["exchange"] == "CBSE"]
    
    if period > 1:
    
        opens = prices["open"].resample(str(period) + "min").first()
        closes = prices["close"].resample(str(period) + "min").last()
        highs = prices["high"].resample(str(period) + "min").max()
        lows = prices["low"].resample(str(period) + "min").min()
        vols = prices["volume"].resample(str(period) + "min").sum()

        period_prices = pd.DataFrame([opens, highs, lows, closes, vols]).T
    else:
        period_prices = prices
        
    return period_prices

def get_quotes(api, symbol, init_date, offset=0):
    
    if isinstance(init_date, np.datetime64):
        init_date = pd.to_datetime(init_date).tz_localize("UTC").tz_convert(tz='America/New_York')

    if offset > 0:
        init_date -= td(minutes=1)
        
    init_date_str = init_date.isoformat()
    end_date_str = (init_date + td(minutes=1)).isoformat()

    quotes = api.get_crypto_quotes(symbol, init_date_str, end_date_str, limit=1000000).df

    while len(quotes) == 0:
        init_date += td(minutes=1)
        init_date_str = init_date.isoformat()
        end_date_str = (init_date + td(minutes=1)).isoformat()
        quotes = api.get_crypto_quotes(symbol, init_date_str, end_date_str, limit=1000000).df

    quotes = process_quotes(quotes)

    return init_date, quotes
 
def simulation(prices, shadow_length):

    open_trades_times = []
    close_trades_times = []

    years = prices.index.year.values
    months = prices.index.month.values
    days = prices.index.day.values
    hours = prices.index.hour.values
    
    for row in range(len(prices)-1):
        
        index = prices.index.values[row]
        values = prices.iloc[row]
        open_price = values.open
        close_price = values.close
        high_price = values.high
        low_price = values.low

        if years[row] == 2018 and months[row] == 2 and (days[row] in [3, 4, 5] or (days[row] == 2 and hours[row] >= 17)):
            continue

        body_length = abs(open_price - close_price)
        if open_price <= close_price:
            upper_wick_length = abs(high_price - close_price)
            lower_wick_length = abs(open_price - low_price)
        elif open_price > close_price:
            upper_wick_length = abs(high_price - open_price)
            lower_wick_length = abs(close_price - low_price)

        if close_price > open_price and lower_wick_length > upper_wick_length and lower_wick_length * shadow_length > body_length:
            if len(open_trades_times) == len(close_trades_times):
                open_trades_times.append(index)
                
        if close_price < open_price and upper_wick_length > lower_wick_length and upper_wick_length * shadow_length > body_length:
            if len(open_trades_times) - 1 == len(close_trades_times):
                close_trades_times.append(index)
        
    inter_open_trades = []
    inter_close_trades = []

    inputs = []
    for open_time in open_trades_times:
        inputs.append([api, symbol, open_time])

    pool = mp.Pool(mp.cpu_count() * 2)
    results = pool.starmap(get_quotes, inputs, chunksize=1)

    for res in results:
        date, quotes = res
        inter_open_trades.append([date, quotes.median_ask_price[0]])
        
    inputs = []
    for close_time in close_trades_times:
        inputs.append([api, symbol, close_time])

    results = pool.starmap(get_quotes, inputs, chunksize=1)

    for res in results:
        date, quotes = res
        inter_close_trades.append([date, quotes.median_bid_price[0]])

    if len(inter_open_trades) - 1 == len(inter_close_trades):
        inter_open_trades = inter_open_trades[:-1]

    pool.close()

    open_trades = []
    close_trades = []

    open_counter = 1
    close_counter = 0

    open_trades.append(inter_open_trades[0])
    while open_counter < len(inter_open_trades):
        if inter_close_trades[close_counter][0] >= inter_open_trades[open_counter][0]:
            pass
        else:
            close_trades.append(inter_close_trades[close_counter])
            open_trades.append(inter_open_trades[open_counter])
        open_counter += 1
        close_counter += 1
    close_trades.append(inter_close_trades[close_counter])
    
    return open_trades, close_trades
        
if __name__ == "__main__":

    symbol = sys.argv[1]
    start_date = "2017-07-01"
    end_date = "2018-07-01"
    period = int(sys.argv[2])
    shadow_length = 1

    key_id, secret_key = load_credentials(opt="paper")
    api = REST(key_id, secret_key, base_url='https://paper-api.alpaca.markets')
    
    print("Getting prices...")
    prices = get_prices(api, symbol, start_date, end_date, period)
    print("Prices pbtained.")

    open_trades, close_trades = simulation(prices, shadow_length)
    
    log_trades(open_trades, close_trades, symbol, sys.argv[2])
