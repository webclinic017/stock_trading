import sys
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

    short_mas = [3, 5, 7, 10, 15, 20]
    long_mas = [6, 9, 13, 20, 50]

    ann_rets = []
    max_dds = []
    win_percs = []
    avg_rets = []
    avg_wins = []

    for short_ma in short_mas:
        short_ma_ann_rets = []
        short_ma_max_dds = []
        short_ma_win_percs = []
        short_ma_avg_rets = []
        short_ma_avg_wins = []
        for long_ma in long_mas:

            if long_ma == 20 and short_ma == 20:
                ann_ret_long, max_dd_long, win_perc_long, avg_return_long, avg_win_long = 0, 0, 0, 0, 0
            else:
                ann_ret_long, max_dd_long, win_perc_long, avg_return_long, avg_win_long = get_summary(str(short_ma) + "_" + str(long_ma) + ".csv", money_per_trade, commission)

            short_ma_ann_rets.append(ann_ret_long)
            short_ma_max_dds.append(max_dd_long)
            short_ma_win_percs.append(win_perc_long)
            short_ma_avg_rets.append(avg_return_long)
            short_ma_avg_wins.append(avg_win_long)

        ann_rets.append(short_ma_ann_rets)
        max_dds.append(short_ma_max_dds)
        win_percs.append(short_ma_win_percs)
        avg_rets.append(short_ma_avg_rets)
        avg_wins.append(short_ma_avg_wins)

    ann_rets = pd.DataFrame(ann_rets)
    max_dds = pd.DataFrame(max_dds)
    win_percs = pd.DataFrame(win_percs)
    avg_rets = pd.DataFrame(avg_rets)
    avg_wins = pd.DataFrame(avg_wins)

    ann_rets.columns = long_mas
    ann_rets["Short MAs"] = short_mas
    ann_rets = ann_rets.set_index("Short MAs")
    ann_rets.to_csv("returns.csv")

    max_dds.columns = long_mas
    max_dds["Short MAs"] = short_mas
    max_dds = max_dds.set_index("Short MAs")
    max_dds.to_csv("Max DDs.csv")
    
    win_percs.columns = long_mas
    win_percs["Short MAs"] = short_mas
    win_percs = win_percs.set_index("Short MAs")
    win_percs.to_csv("Win Percs.csv")
    
    avg_rets.columns = long_mas
    avg_rets["Short MAs"] = short_mas
    avg_rets = avg_rets.set_index("Short MAs")
    avg_rets.to_csv("Avg Returns.csv")
    
    avg_wins.columns = long_mas
    avg_wins["Short MAs"] = short_mas
    avg_wins = avg_wins.set_index("Short MAs")
    avg_wins.to_csv("Avg Wins.csv")
    