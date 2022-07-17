from alpaca_trade_api.rest import REST, TimeFrame, TimeFrameUnit
import datetime as dt
from datetime import timedelta as td
import numpy as np
import matplotlib.pyplot as plt

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
    with open("/Users/danielgalea/Documents/git/stock_trading/credentials.txt") as file:
        
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
    
    bar_data = bar_data[start_date + " " + str(session_open.hour).zfill(2) + ":" + str(session_open.minute).zfill(2) + ":00": end_date + " " + str(session_close.hour).zfill(2) + ":" + str(session_close.minute).zfill(2) + ":00"]
    return bar_data
    
def process_date(api, symbol, prev_date, curr_date, etoro_sl, max_sl, max_tp, exit_time):
    
    data = get_data(api, symbol, prev_date)
    prev_close = data["close"][-1]

    data = get_data(api, symbol, curr_date)
    day_open = data["open"][0]
    #print(prev_close, day_open)
    if day_open > prev_close:
        etoro_sl = day_open + day_open * etoro_sl/100
        gap_sl = day_open + abs(day_open - prev_close) * max_sl/100
        sl = np.min([gap_sl, etoro_sl])
        tp = day_open - abs(day_open - prev_close) * max_tp/100
    elif day_open < prev_close:
        etoro_sl = day_open - day_open * etoro_sl/100
        gap_sl = day_open - abs(day_open - prev_close) * max_sl/100
        sl = np.max([gap_sl, etoro_sl])
        tp = day_open + abs(day_open - prev_close) * max_tp/100
    else:
        return 0, 0
    
    for data_i in range(len(data) - exit_time):
        
        period_open = data.iloc[data_i]["open"]
        period_high = data.iloc[data_i]["high"]
        period_low = data.iloc[data_i]["low"]
        period_close = data.iloc[data_i]["close"]
        
        if day_open > prev_close:
            if period_high > sl:
                return day_open - prev_close, -abs(day_open - sl)/day_open * 100
            if period_low < tp:
                return day_open - prev_close, abs(day_open - tp)/day_open * 100
            
        elif day_open < prev_close:
            if period_high > tp:
                return day_open - prev_close, abs(day_open - tp)/day_open * 100
            if period_low < sl:
                return day_open - prev_close, -abs(day_open - sl)/day_open * 100
            
    return day_open - prev_close, (day_open - data.iloc[-exit_time-1]["close"])/day_open * 100
        
if __name__ == "__main__":
    
    key_id, secret_key = load_credentials(opt="paper")
    api = REST(key_id, secret_key, base_url='https://paper-api.alpaca.markets')
    
    symbols = ["SPY", "DIA", "QQQ"]
    start_date = "2016-07-01"
    end_date = "2016-12-31"
    
    etoro_sl = 100
    max_sl = 100
    max_tp = 100
    exit_time = 0
    
    calendar = api.get_calendar(start=start_date, end=end_date)
    
    trades = []
    diffs = []
    
    for symbol in symbols:
        crossed = 0
        
        perc_diff_close = []
        perc_diff_trade = []
        for date_i in range(1, len(calendar)):
            
            data = get_data(api, symbol, calendar[date_i-1])
            prev_close = data["close"][-1]

            data = get_data(api, symbol, calendar[date_i])
            day_open = data["open"][0]
            day_high = data["high"].max()
            day_low = data["low"].min()

            print(symbol, str(calendar[date_i].date).split(" ")[0])
            
            perc_diff_close.append((day_open - prev_close)/prev_close*100)
            
            flag = False
            if day_open > prev_close and day_low <= prev_close:
                crossed += 1
                flag = True
            if day_open < prev_close and day_high >= prev_close:
                crossed += 1
                flag = True
            
            if flag == True:
                perc_diff_trade.append(abs(day_open - prev_close)/day_open * 100)
            else:
                perc_diff_trade.append(-abs(day_open - prev_close)/day_open * 100)
            
        trades.append(perc_diff_trade)
        diffs.append(perc_diff_close)
        
        account = [1]
        for trade in perc_diff_trade:
            account.append(account[-1] * (100 + trade)/100)
        #print(account)
        
    fig, axs = plt.subplots(4, 3, figsize=(10, 10))
    
    axs = axs.flatten()
    
    axs[0].plot(diffs[0], trades[0], "o")
    axs[1].plot(diffs[1], trades[1], "o")
    axs[2].plot(diffs[2], trades[2], "o")
    
    axs[0].set_title(symbols[0])
    axs[1].set_title(symbols[1])
    axs[2].set_title(symbols[2])
    
    axs[0].set_xlabel("Diff vs prev close")
    axs[1].set_xlabel("Diff vs prev close")
    axs[2].set_xlabel("Diff vs prev close")
    
    axs[0].set_ylabel("Trade")
    axs[1].set_ylabel("Trade")
    axs[2].set_ylabel("Trade")
    
    axs[3].hist(trades[0], bins=50)
    axs[4].hist(trades[1], bins=50)
    axs[5].hist(trades[2], bins=50)
    
    axs[3].set_xlabel("Returns")
    axs[4].set_xlabel("Returns")
    axs[5].set_xlabel("Returns")
    
    axs[3].set_ylabel("Occurences")
    axs[4].set_ylabel("Occurences")
    axs[5].set_ylabel("Occurences")
    
    diffs = []
    trades = []
    for symbol in symbols:
        
        symbol_diffs = []
        symbol_trades = []
        
        for date_i in range(1, len(calendar)):
            
            diff, trade = process_date(api, symbol, calendar[date_i-1], calendar[date_i], etoro_sl, max_sl, max_tp, exit_time)
            
            print(symbol, str(calendar[date_i].date).split(" ")[0])
            #print(diff, trade)
            
            symbol_diffs.append(diff)
            symbol_trades.append(trade)
        
        diffs.append(symbol_diffs)
        trades.append(symbol_trades)
        
    axs[6].plot(diffs[0], trades[0], "o")
    axs[7].plot(diffs[1], trades[1], "o")
    axs[8].plot(diffs[2], trades[2], "o")
    
    axs[6].set_title(symbols[0])
    axs[7].set_title(symbols[1])
    axs[8].set_title(symbols[2])
    
    axs[6].set_xlabel("Diff")
    axs[7].set_xlabel("Diff")
    axs[8].set_xlabel("Diff")
    
    axs[6].set_ylabel("Trade")
    axs[7].set_ylabel("Trade")
    axs[8].set_ylabel("Trade")
    
    axs[9].hist(trades[0], bins=50)
    axs[10].hist(trades[1], bins=50)
    axs[11].hist(trades[2], bins=50)
    
    axs[9].set_xlabel("Returns")
    axs[10].set_xlabel("Returns")
    axs[11].set_xlabel("Returns")
    
    axs[9].set_ylabel("Occurences")
    axs[10].set_ylabel("Occurences")
    axs[11].set_ylabel("Occurences")
            
    plt.tight_layout()
    plt.savefig("testing.png")