from alpaca_trade_api.rest import REST
import datetime as dt
from datetime import timedelta as td
import numpy as np
import sys
sys.path.insert(0, "/Users/danielgalea/Documents/git/stock_trading") 
from common_funcs import load_credentials, get_prices, get_quotes, log_trades
import multiprocessing as mp

def get_data(api, symbol, date):
    
    date_str = str(date.date).split(" ")[0]
    session_open = date.open
    session_close = (dt.datetime.combine(dt.date(1,1,1), date.close) - td(minutes=1)).time()# date.session_close - td(minutes=1)
    
    bar_data = get_prices(api, symbol, date_str, date_str, [1])[1]
    
    bar_data = bar_data[date_str + " " + str(session_open.hour).zfill(2) + ":" + str(session_open.minute).zfill(2) + ":00": date_str + " " + str(session_close.hour).zfill(2) + ":" + str(session_close.minute).zfill(2) + ":00"]
    return bar_data
    
def process_date(api, symbol, prev_date, curr_date, etoro_sl, exit_timesteps, no_trade_min, no_trade_max, tp_limit, tp_perc, sl_perc):
    
    data = get_data(api, symbol, prev_date)
    prev_close = data["close"][-1]
    
    data = get_data(api, symbol, curr_date)
    day_open = data["open"][0]
    
    gap = abs(day_open - prev_close) / prev_close * 100
    if gap < no_trade_min or gap > no_trade_max:
        return []
    
    if day_open > prev_close:
        etoro_sl = day_open + day_open * etoro_sl/100
        if gap <= tp_limit:
            tp = day_open - abs(day_open - prev_close)
            gap_sl = day_open + abs(day_open - prev_close) * sl_perc/100
        else:
            tp = day_open - abs(day_open - prev_close) * tp_perc/100
            gap_sl = day_open + abs(day_open - prev_close) * tp_perc/100
        sl = np.min([gap_sl, etoro_sl])
        entry_type = "bid"
        direction = "SHORT"
    elif day_open < prev_close:
        etoro_sl = day_open - day_open * etoro_sl/100
        if gap <= tp_limit:
            tp = day_open + abs(day_open - prev_close)
            gap_sl = day_open - abs(day_open - prev_close) * sl_perc/100
        else:
            tp = day_open + abs(day_open - prev_close) * tp_perc/100
            gap_sl = day_open - abs(day_open - prev_close) * tp_perc/100
        sl = np.max([gap_sl, etoro_sl])
        direction = "LONG"
        entry_type = "ask"
    else:
        return []
    
    period_timestamps = data.index.values
    entry_time = period_timestamps[0]
        
    exit_time = None   
    for data_i in range(len(data) - exit_timesteps):
        
        period_high = data.iloc[data_i]["high"]
        period_low = data.iloc[data_i]["low"]
        
        if day_open > prev_close:
            if period_high > sl:
                exit_time = period_timestamps[data_i+1]
                exit_type = "bid"
                break
            if period_low < tp:
                exit_time = period_timestamps[data_i+1]
                exit_type = "ask"
                break
            
        elif day_open < prev_close:
            if period_high > tp:
                exit_time = period_timestamps[data_i+1]
                exit_type = "bid"
                break
            if period_low < sl:
                exit_time = period_timestamps[data_i+1]
                exit_type = "ask"
                break
    
    if exit_time is None:
        if day_open > prev_close:
            exit_time = period_timestamps[-exit_timesteps-1]
            exit_type = "ask"
        elif day_open < prev_close:
            exit_time = period_timestamps[-exit_timesteps-1]
            exit_type = "bid"
                
    if entry_time is None or exit_time is None:
        return []
    
    return entry_time, entry_type, exit_time, exit_type, direction, symbol

def simulation(api, calendar, symbol, etoro_sl, close_trade, no_trade_min, no_trade_max, tp_limit, tp_perc, sl_perc, pool):

    entry_inputs = []
    entry_types = []
    exit_inputs = []
    exit_types = []
    directions = []
    
    for date_i in range(1, len(calendar)):
        
        prev_date = calendar[date_i-1]
        curr_date = calendar[date_i]
        
        result = process_date(api, symbol, prev_date, curr_date, etoro_sl, close_trade, no_trade_min, no_trade_max, tp_limit, tp_perc, sl_perc)
        
        if len(result) > 0:
            entry_time, entry_type, exit_time, exit_type, direction, symbol = result
            entry_inputs.append([api, symbol, entry_time, 0])
            entry_types.append(entry_type)
            exit_inputs.append([api, symbol, exit_time, 32])
            exit_types.append(exit_type)
            directions.append(direction)
        else:
            continue

    entry_results = pool.starmap(get_quotes, entry_inputs, chunksize=1)
    exit_results = pool.starmap(get_quotes, exit_inputs, chunksize=1)
    
    open_trades = []
    close_trades = []

    for i in range(len(entry_results)):
        entry_time, quotes = entry_results[i]
        if entry_types[i] == "bid":
            entry_price = quotes.median_bid_price[0]
        else:
            entry_price = quotes.median_ask_price[0] 
        open_trades.append([entry_time, symbol, entry_price, directions[i]])

    for i in range(len(exit_results)):
        exit_time, quotes = exit_results[i]
        if exit_types[i] == "bid":
            exit_price = quotes.median_bid_price[0]
        else:
            exit_price = quotes.median_ask_price[0] 
        close_trades.append([exit_time, symbol, exit_price])

    return open_trades, close_trades
    
if __name__ == "__main__":
    
    key_id, secret_key = load_credentials(opt="paper")
    api = REST(key_id, secret_key, base_url='https://paper-api.alpaca.markets')
    
    start_date = "2016-07-01"
    end_date = "2017-07-01"
    etoro_sl = 2.5
    
    symbol = "QQQ"
    close_trade = 1
    no_trade_min = 0.1
    no_trade_max = 2
    tp_limit = 0.5
    tp_perc = 100
    sl_perc = 150

    calendar = api.get_calendar(start=start_date, end=end_date)
    
    pool = mp.Pool(50)
    open_trades, close_trades = simulation(api, calendar, symbol, etoro_sl, close_trade, no_trade_min, no_trade_max, tp_limit, tp_perc, sl_perc, pool)
    pool.close()

    log_trades(open_trades, close_trades, name=sys.argv[0].replace(".py", ""), save=True)
    
    