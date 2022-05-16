import pandas as pd
import sys, os
import numpy as np

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

def get_daily_returns(df, side):
    
    df = df.copy()
    
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
    return win_return

if __name__ == "__main__":
    
    path = sys.argv[1]
    position = int(sys.argv[2])
    
    money_per_trade = 1000
    commission = 0
    
    files = [f for f in os.listdir(path) if os.path.isfile(os.path.join(path, f))]
    files = [f for f in files if ".csv" in f]

    summary = []
    
    for file in files:
        
        key = file.replace(".csv", "").split("_")[position]
        csv = pd.read_csv(path + file)
        
        backtest = get_backtest(csv, money_per_trade, commission)
        
        all_returns = get_daily_returns(backtest, "Both")["Daily Returns"].cumsum().values[-1]
        long_returns = get_daily_returns(backtest, "LONG")["Daily Returns"].cumsum().values[-1]
        short_returns = get_daily_returns(backtest, "SHORT")["Daily Returns"].cumsum().values[-1]
        
        all_win_perc = win_perc(backtest, "Both")
        long_win_perc = win_perc(backtest, "LONG")
        short_win_perc = win_perc(backtest, "SHORT")
        
        summary.append([key, all_returns, long_returns, short_returns, all_win_perc, long_win_perc, short_win_perc])
        
    summary = pd.DataFrame(summary)
    summary.columns = [path[5:-1], "All Returns", "All Returns", "All Returns", "All win %", "Long win %", "Short win %"]
    summary = summary.sort_values(by=[path[5:-1]])
    summary = summary.set_index(path[5:-1])
    summary.to_csv(path[5:-1] + "_summary.csv")