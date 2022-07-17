import pandas as pd
import numpy as np
import random, sys

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

def log_trades(open_trades, close_trades, symbol, name=None):
    
    logs = []
    for i in range(len(open_trades)):
        logs.append([str(open_trades[i][0]), str(close_trades[i][0]), symbol, "LONG", open_trades[i][1], close_trades[i][1]])
        
    history = pd.DataFrame(logs)
    history.columns = ["Entry Time", "Exit Time", "Symbol", "Direction", "Entry", "Exit"]
    
    history["Entry Time"] = pd.Index(pd.to_datetime(history["Entry Time"]))
    history["Exit Time"] = pd.Index(pd.to_datetime(history["Exit Time"]))
    
    if name == None:
        history.to_csv(sys.argv[0].replace(".py", ".csv"))
    else:
        history.to_csv(name + ".csv")
        
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

def get_monte_carlo(df, n, stop):
    
    poss = []
    
    returns = list(df["Return"].values)
    for n_i in range(n):
        p = [random.choice(returns) for _ in range(len(returns))]
        cum_sum = np.cumsum(p)
        poss.append(cum_sum)
        
    mean = []
    plus_std = []
    plus_2std = []
    minus_std = []
    minus_2std = []
        
    for i in range(len(returns)):
        vals = []
        for n_i in range(n):
            vals.append(poss[n_i][i])
        
        vals = np.array(vals)
        mean.append(np.mean(vals))
        
        std = np.std(vals)
        plus_std.append(mean[-1] + std)
        plus_2std.append(mean[-1] + 2 * std)
        minus_std.append(mean[-1] - std)
        minus_2std.append(mean[-1] - 2 * std)

    return poss, mean, plus_std, plus_2std, minus_std, minus_2std
        
def get_daily_returns(df, side):
    
    if side == "LONG":
        df = df.loc[df["Direction"] == "LONG"]
    elif side == "SHORT":
        df = df.loc[df["Direction"] == "SHORT"]
    
    timestamps = []
    for timestamp in df["Entry Time"].values:
        timestamp_conv = timestamp#dt.strptime(timestamp, "%Y-%m-%d %H:%M:%S%z")
        timestamps.append(timestamp_conv)
        
    df["Entry Time"] = pd.to_datetime(timestamps, utc=True)
    df = df.set_index("Entry Time")
    df = df.tz_convert('US/Eastern')
    
    df = df["Return"].resample("D").sum()
    df2 = pd.DataFrame({"Dates":df.index, "Daily Returns":df.values})
    
    return df2
    
def annual_return(df):
    
    if len(df) > 0:
        
        num_days_traded = len(df)
        num_days_actual = (df["Dates"].values[-1] - df["Dates"].values[0])
        num_days_actual = num_days_actual.astype('timedelta64[D]')
        num_days_actual = int(num_days_actual / np.timedelta64(1, 'D')) + 1
        
        if num_days_traded == num_days_actual:
            return df["Daily Returns"].cumsum().values[-1] / num_days_traded * 365
        else:
            return df["Daily Returns"].cumsum().values[-1] / num_days_traded * 252
    else:
        return 0
    
def accum_return(df, side):

    if side == "Both":
        return df["Accum Returns"].values[-1]
    elif side == "LONG":
        if len(df.loc[df["Direction"] == "LONG"]) > 0:
            return df.loc[df["Direction"] == "LONG"]["Return"].cumsum().values[-1]
        else:
            return 0
    elif side == "SHORT":
        if len(df.loc[df["Direction"] == "SHORT"]) > 0:
            return df.loc[df["Direction"] == "SHORT"]["Return"].cumsum().values[-1]
        else:
            return 0
        
def win_perc(df, side):
    
    if side == "Both":
        return len(df.loc[df["Return"] > 0]) / len(df) * 100
    elif side == "LONG":
        df2 = df.loc[df["Direction"] == "LONG"]
        if len(df2) > 0:
            return len(df2.loc[df2["Return"] > 0]) / len(df2) * 100
        else:
            return 0
    elif side == "SHORT":
        df2 = df.loc[df["Direction"] == "SHORT"]
        if len(df2) > 0:
            return len(df2.loc[df2["Return"] > 0]) / len(df2) * 100
        else:
            return 0
            
def largest_win(df, side):
    
    if side == "Both":
        if len(df) > 0:
            return df["Return"].max()
        else:
            return 0
    elif side == "LONG":
        if len(df.loc[df["Direction"] == "LONG"]) > 0:
            return df.loc[df["Direction"] == "LONG"]["Return"].max()
        else:
            return 0
    elif side == "SHORT":
        if len(df.loc[df["Direction"] == "SHORT"]) > 0:
            return df.loc[df["Direction"] == "SHORT"]["Return"].max()
        else:
            return 0
        
def largest_loss(df, side):
    
    if side == "Both":
        if len(df) > 0:
            return df["Return"].min()
        else:
            return 0
    elif side == "LONG":
        if len(df.loc[df["Direction"] == "LONG"]) > 0:
            return df.loc[df["Direction"] == "LONG"]["Return"].min()
        else:
            return 0
    elif side == "SHORT":
        if len(df.loc[df["Direction"] == "SHORT"]) > 0:
            return df.loc[df["Direction"] == "SHORT"]["Return"].min()
        else:
            return 0
        
def avg_win(df, side):
    
    if side == "Both":
        if len(df) > 0:
            return df.loc[df["Return"] > 0]["Return"].mean()
        else:
            return 0
    elif side == "LONG":
        df2 = df.loc[df["Direction"] == "LONG"]
        if len(df2) > 0:
            return df2.loc[df2["Return"] > 0]["Return"].mean()
        else:
            return 0
    elif side == "SHORT":
        df2 = df.loc[df["Direction"] == "SHORT"]
        if len(df2) > 0:
            return df2.loc[df2["Return"] > 0]["Return"].mean()
        else:
            return 0
    
def avg_loss(df, side):
    
    if side == "Both":
        if len(df) > 0:
            return df.loc[df["Return"] < 0]["Return"].mean()
        else:
            return 0
    elif side == "LONG":
        df2 = df.loc[df["Direction"] == "LONG"]
        if len(df2) > 0:
            return df2.loc[df2["Return"] < 0]["Return"].mean()
        else:
            return 0
    elif side == "SHORT":
        df2 = df.loc[df["Direction"] == "SHORT"]
        if len(df2) > 0:
            return df2.loc[df2["Return"] < 0]["Return"].mean()
        else:
            return 0
        
def avg_return(df, side):
    
    if side == "Both":
        if len(df) > 0:
            return df["Return"].mean()
        else:
            return 0
    elif side == "LONG":
        df2 = df.loc[df["Direction"] == "LONG"]
        if len(df2) > 0:
            return df2["Return"].mean()
        else:
            return 0
    elif side == "SHORT":
        df2 = df.loc[df["Direction"] == "SHORT"]
        if len(df2) > 0:
            return df2["Return"].mean()
        else:
            return 0
        
def annual_sharpe_ratio(df):
    
    if len(df) > 0:
        daily_returns = df["Daily Returns"].values

        daily_returns = np.array(daily_returns)
        daily_returns = np.cumsum(daily_returns)
        r = np.diff(daily_returns)
        return r.mean() / r.std() * np.sqrt(252)
    else:
        return 0
    
def get_underwater_data(df):
    
    returns = df["Return"].values
    
    underwater = []
    
    for ret_i, ret in enumerate(returns):
        if ret_i == 0:
            if ret > 0:
                underwater.append(0)
            else:
                underwater.append(ret)
        else:
            if underwater[-1] + ret > 0:
                underwater.append(0)
            else:
                underwater.append(underwater[-1] + ret)
    
    underwater_perc = []
    
    for und_i, und in enumerate(underwater):
        
        if und_i == 0:
            underwater_perc.append( und / 1000)
        else:
            underwater_perc.append(  und / (1000 + np.max(np.cumsum(returns[:und_i]))) )
            
    underwater_perc = np.array(underwater_perc) * 100
            
    return underwater, underwater_perc
    
def max_dd(df, side):
    
    if side == "LONG":
        df = df.loc[df["Direction"] == "LONG"]
    elif side == "SHORT":
        df = df.loc[df["Direction"] == "SHORT"]
        
    if len(df) > 0:
        und = get_underwater_data(df)
        return np.min(und)
    else:
        return 0

def consecutive_wins(df, side):
    
    if side == "LONG":
        df = df.loc[df["Direction"] == "LONG"]
    elif side == "SHORT":
        df = df.loc[df["Direction"] == "SHORT"]
        
    returns = df["Return"].values
    
    max_wins = 0
    wins = []
    for ret in returns:
        if ret > 0:
            wins.append(ret)
        else:
            if max_wins < len(wins):
                max_wins = len(wins)
            wins = []
            
    return max_wins

def consecutive_losses(df, side):
    
    if side == "LONG":
        df = df.loc[df["Direction"] == "LONG"]
    elif side == "SHORT":
        df = df.loc[df["Direction"] == "SHORT"]
        
    returns = df["Return"].values
    
    max_losses = 0
    losses = []
    for ret in returns:
        if ret < 0:
            losses.append(ret)
        else:
            if max_losses < len(losses):
                max_losses = len(losses)
            losses = []
            
    return max_losses

def daily_compounded_returns(df):
    
    rets = df["Daily Returns"].values
    comp_rets = [rets[0]]
    factors = [1]
    
    for ret_i, ret in enumerate(rets[1:]):
        if 1 + comp_rets[-1]/4000 > 0:
            factors.append(1 + comp_rets[-1]/4000)
        else:
            factors.append(0)
        comp_rets.append(comp_rets[-1] + ret * factors[-1])
        
    comp_rets = np.array(comp_rets)
    
    ret_df = pd.DataFrame({"Dates": df["Dates"], "Accum Returns": comp_rets})
    
    return ret_df
