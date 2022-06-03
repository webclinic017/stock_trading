from alpaca_trade_api.rest import REST, TimeFrame, TimeFrameUnit
import datetime as dt
from datetime import timedelta as td
import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
import multiprocessing as mp
import sys, os
os.environ["APCA_RETRY_MAX"] = "100"
os.environ["APCA_RETRY_WAIT"] = "1"


def load_credentials(opt="paper"):
    '''
    Load Alpaca API keys for account.
    Args:
        str: opt - Select between paper and live account
    Returns:
        str: key_id - Alpaca API key id
        str: secret_key - Alpaca API secret_key
    '''
    
    #Open credentials file
    with open("/home/users/dgalea/stock_trading/credentials.txt") as file:
        
        #Read lines
        lines = file.readlines()
        
        #Get keys
        if opt == "paper":
            key_id = lines[0].split("=")[1].strip()
            secret_key = lines[1].split("=")[1].strip()
        elif opt == "live":
            key_id = lines[2].split("=")[1].strip()
            secret_key = lines[3].split("=")[1].strip()
        else:
            return None, None
        
    #Return keys
    return key_id, secret_key

def get_data(api, symbol, date):
    
    date_str = str(date.date).split(" ")[0]
    session_open = date.open
    session_close = (dt.datetime.combine(dt.date(1,1,1), date.close) - td(minutes=1)).time()# date.session_close - td(minutes=1)
    
    bar_data = api.get_bars(symbol, TimeFrame.Minute, date_str, date_str, adjustment="all").df
    bar_data = bar_data.tz_convert('US/Eastern')
    
    bar_data = bar_data[date_str + " " + str(session_open.hour).zfill(2) + ":" + str(session_open.minute).zfill(2) + ":00": date_str + " " + str(session_close.hour).zfill(2) + ":" + str(session_close.minute).zfill(2) + ":00"]
    return bar_data
    
def process_date(api, symbol, prev_date, curr_date, etoro_sl, max_sl, max_tp, exit_timesteps, no_trade_min, no_trade_max):
    
    data = get_data(api, symbol, prev_date)
    prev_close = data["close"][-1]

    data = get_data(api, symbol, curr_date)
    day_open = data["open"][0]
    
    gap = abs(day_open - prev_close) / prev_close * 100
    if gap < no_trade_min or gap > no_trade_max:
        return pd.DataFrame()
    
    etoro_sl = day_open - day_open * etoro_sl/100
    gap_sl = day_open - abs(day_open - prev_close) * max_sl/100
    sl = np.max([gap_sl, etoro_sl])
    tp = day_open + abs(day_open - prev_close) * max_tp/100
    
    entry_time, entry_price = get_quotes_entry(api, symbol, data.index.values[0], 0, exit_timesteps)
    direction = "LONG"
    
    exit_price_present = False
    for data_i in range(len(data) - exit_timesteps):
        
        period_open = data.iloc[data_i]["open"]
        period_high = data.iloc[data_i]["high"]
        period_low = data.iloc[data_i]["low"]
        period_close = data.iloc[data_i]["close"]
        period_timestamp = data.index.values[data_i]
        
        if period_high > tp:
            exit_time, exit_price = get_quotes_exit(api, symbol, period_timestamp, 1, exit_timesteps)
            exit_price_present = True
            break
        if period_low < sl:
            exit_time, exit_price = get_quotes_exit(api, symbol, period_timestamp, 0, exit_timesteps)
            exit_price_present = True
            break
    
    if exit_price_present == False:
        exit_time, exit_price = get_quotes_exit(api, symbol, pd.to_datetime(data.index.values[-1]).tz_localize("UTC").tz_convert(tz='America/New_York')-td(minutes=exit_timesteps), 1, exit_timesteps)
        
    if entry_price is None or exit_price is None:
        return pd.DataFrame()
    
    trade_data = pd.DataFrame([entry_time, exit_time, symbol, direction, entry_price, exit_price]).T
    trade_data.columns = ["Entry Time", "Exit Time", "Symbol", "Direction", "Entry", "Exit"]

    return trade_data

def get_quotes_exit(api, symbol, init_date, buy_sell, exit_time):
    
    if isinstance(init_date, np.datetime64):
        init_date = pd.to_datetime(init_date).tz_localize("UTC").tz_convert(tz='America/New_York')
    end_time = init_date - td(minutes=exit_time) 
    
    init_date_str = init_date.isoformat()
    end_date_str = (init_date + td(minutes=1)).isoformat()
    
    quotes = api.get_quotes(symbol, init_date_str, end_date_str, limit=1000000).df
    
    while len(quotes) == 0:
        init_date += td(minutes=1)
        init_date_str = init_date.isoformat()
        end_date_str = (init_date + td(minutes=1)).isoformat()
        quotes = api.get_quotes(symbol, init_date_str, end_date_str, limit=1000000).df
    
        if init_date > end_time:
            return None, None
    
    quotes = process_quotes(quotes)
    quotes = quotes.dropna()
    
    if buy_sell == 0:
        price = quotes["median_ask_price"].values[0]
    elif buy_sell == 1:
        price = quotes["median_bid_price"].values[0]
    
    return init_date, price

def get_quotes_entry(api, symbol, init_date, buy_sell, exit_time):
    
    init_date = pd.to_datetime(init_date).tz_localize("UTC").tz_convert(tz='America/New_York')
    end_time = init_date - td(minutes=exit_time) 
    
    init_date_str = init_date.isoformat()
    end_date_str = (init_date + td(minutes=1)).isoformat()
    
    quotes = api.get_quotes(symbol, init_date_str, end_date_str, limit=1000000).df
    
    while len(quotes) == 0:
        init_date += td(minutes=1)
        init_date_str = init_date.isoformat()
        end_date_str = (init_date + td(minutes=1)).isoformat()
        quotes = api.get_quotes(symbol, init_date_str, end_date_str, limit=1000000).df
        
        if init_date > end_time:
            return None, None
        
    quotes = process_quotes(quotes)
    quotes = quotes.dropna()
    
    if buy_sell == 0:
        price = quotes["median_ask_price"].values[0]
    elif buy_sell == 1:
        price = quotes["median_bid_price"].values[0]
    
    return init_date, price

def process_quotes(data):
    '''
    Process quotes to get min/max/mean/median bid/ask prices per minute.
    Args:
        dataframe: data - Quote data from Alpaca API
    Returns:
        dataframe: data - Treated data
    '''
    
    data = data[["ask_price", "bid_price"]]
        
    bid_max = data["bid_price"].resample("10s").max()
    bid_min = data["bid_price"].resample("10s").min()
    bid_mean = data["bid_price"].resample("10s").mean()
    bid_median = data["bid_price"].resample("10s").median()
    ask_max = data["ask_price"].resample("10s").max()
    ask_min = data["ask_price"].resample("10s").min()
    ask_mean = data["ask_price"].resample("10s").mean()
    ask_median = data["ask_price"].resample("10s").median()
        
    data = pd.DataFrame([bid_max, bid_min, bid_mean, bid_median, ask_max, ask_min, ask_mean, ask_median]).T
    data.columns = ["max_bid_price", "min_bid_price", "mean_bid_price", "median_bid_price", "max_ask_price", "min_ask_price", "mean_ask_price", "median_ask_price"]
    
    return data


if __name__ == "__main__":
    
    key_id, secret_key = load_credentials(opt="paper")
    api = REST(key_id, secret_key, base_url='https://paper-api.alpaca.markets')
    
    start_date = "2016-07-01"
    end_date = "2020-12-31"
    etoro_sl = 2.5
    
    symbol = sys.argv[1]
    max_sl = int(sys.argv[2])
    max_tp = int(sys.argv[3])
    exit_time = int(sys.argv[4])
    no_trade_min = float(sys.argv[5])
    no_trade_max = float(sys.argv[6])
    
    calendar = api.get_calendar(start=start_date, end=end_date)
    
    all_trade_data = []
    
    for date_i in range(1, len(calendar)):
        
        prev_date = calendar[date_i-1]
        curr_date = calendar[date_i]
        
        print(symbol, str(curr_date.date).split(" ")[0])
        
        trade_data = process_date(api, symbol, prev_date, curr_date, etoro_sl, max_sl, max_tp, exit_time, no_trade_min, no_trade_max)
        all_trade_data.append(trade_data)
            
    all_trade_data = pd.concat(all_trade_data)
    all_trade_data.to_csv(symbol + "_" + str(max_sl) + "_" + str(max_tp) + "_" + str(exit_time) + "_" + str(no_trade_min) + "_" + str(no_trade_max) + ".csv")
    
    