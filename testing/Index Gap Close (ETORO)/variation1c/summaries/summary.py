import pandas as pd
import sys, os
import numpy as np

sys.path.insert(0, "/Users/danielgalea/Documents/git/stock_trading") 
from common_funcs import get_backtest, get_daily_returns, win_perc

if __name__ == "__main__":
    
    path = sys.argv[1]
    
    money_per_trade = 1000
    commission = 0
    
    files = [f for f in os.listdir(path) if os.path.isfile(os.path.join(path, f))]
    files = [f for f in files if ".csv" in f]

    summary = []
    
    for file in files:
        
        try:
            key = float(file.replace(".csv", ""))
        except:
            key = file.replace(".csv", "")
        csv = pd.read_csv(path + file)
        
        backtest = get_backtest(csv, money_per_trade, commission)
        
        all_returns = get_daily_returns(backtest, "Both")
        if all_returns.empty:
            all_returns = 0
        else:
            all_returns = all_returns["Daily Returns"].cumsum().values[-1]
        long_returns = get_daily_returns(backtest, "LONG")
        if long_returns.empty:
            long_returns = 0
        else:
            long_returns = long_returns["Daily Returns"].cumsum().values[-1]
        short_returns = get_daily_returns(backtest, "SHORT")
        if short_returns.empty:
            short_returns = 0
        else:
            short_returns = short_returns["Daily Returns"].cumsum().values[-1]
        
        all_win_perc = win_perc(backtest, "Both")
        long_win_perc = win_perc(backtest, "LONG")
        short_win_perc = win_perc(backtest, "SHORT")
        
        summary.append([key, all_returns, long_returns, short_returns, all_win_perc, long_win_perc, short_win_perc])
        
    summary = pd.DataFrame(summary)
    summary.columns = [path[5:-1], "All Returns", "All Returns", "All Returns", "All win %", "Long win %", "Short win %"]
    summary = summary.sort_values(by=[path[5:-1]])
    summary = summary.set_index(path[5:-1])
    summary.to_csv(path[5:-1] + "_summary.csv")