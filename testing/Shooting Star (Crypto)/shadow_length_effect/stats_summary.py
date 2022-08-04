import os, sys
import multiprocessing as mp
import pandas as pd
sys.path.insert(0, "/Users/danielgalea/Documents/git/stock_trading") 
from common_funcs import *

def get_summary(file, money_per_trade, commission):

    df = pd.read_csv(file)
    
    backtest = get_backtest(df, money_per_trade, commission)
    daily_backtest_long = get_daily_returns(backtest, "LONG")
    ann_ret_long = annual_return(daily_backtest_long)
    max_dd_long = max_dd(backtest, "LONG")
    win_perc_long = win_perc(backtest, "LONG")
    avg_return_long = avg_return(backtest, "LONG")
    avg_win_long = avg_win(backtest, "LONG")
    return ann_ret_long, max_dd_long, win_perc_long, avg_return_long, avg_win_long
    
if __name__ == "__main__":

    money_per_trade = 1000
    stop_trading = -1000
    commission = 6
    
    files = [f for f in os.listdir(".") if os.path.isfile(os.path.join(".", f))]
    files = [f for f in files if ".csv" in f]
    
    data = []
    for file in files:
        if "results" in file:
            continue
        
        ann_ret_long, max_dd_long, win_perc_long, avg_return_long, avg_win_long = get_summary(file, money_per_trade, commission)
        
        data.append([float(file.replace(".csv", "")), ann_ret_long, max_dd_long, win_perc_long, avg_return_long, avg_win_long])

    data = pd.DataFrame(data)
    data.columns = ["Shadow Length", "Annual Return", "Max DD", "Win %", "Avg Return", "Avg Win"]
    data = data.set_index("Shadow Length")
    data = data.sort_index()
    data.to_csv("summary.csv")