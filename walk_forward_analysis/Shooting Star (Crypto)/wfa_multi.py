import pandas as pd
import os, sys
from datetime import datetime as dt
from datetime import timedelta as td
import numpy as np
import multiprocessing as mp

def get_backtest(df, money_per_trade, commission):
    
    df = df.copy()
    
    sizes = []
    returns = []

    for i in range(len(df)):
        
        entry_price = df.loc[i, "Entry"]
        exit_price = df.loc[i, "Exit"]
        direction = df.loc[i, "Direction"]
        
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

def process_window(init_date, end_date, next_date, window, windows, wfa_period):
    
    init_date = window_dates[window]
    end_date = window_dates[window+1]
    next_date = window_dates[window+2]

    print("Processing window", window+1, "of", len(window_dates) - 2, ": ", init_date, "-", end_date, "for WFA period = ", wfa_period)

    returns_period = []
    for csv_i, csv in enumerate(csvs):

        csv_period = csv[csv["Entry Time"] >= init_date]
        csv_period = csv[csv["Exit Time"] < end_date]

        if len(csv_period) == 0:
            returns_period.append([params[csv_i][0], params[csv_i][1], 0, csv_i])
        else:
            period_accum_return = get_backtest(csv_period, money_per_trade, commission)["Accum Returns"].values[-1]
            returns_period.append([params[csv_i][0], params[csv_i][1], period_accum_return, csv_i])

    returns_period = pd.DataFrame(returns_period, columns=["period", "diff_scaling", "accum_returns", "csv_num"])
    returns_period = returns_period.sort_values(by=['accum_returns'], ascending=False)

    csv_period = csvs[returns_period["csv_num"].values[0]]
    csv_period = csv_period[csv_period["Entry Time"] >= init_date]
    csv_period = csv_period[csv_period["Exit Time"] < end_date]  
    best_csv = csv_period.copy()

    csv_period = csvs[returns_period["csv_num"].values[0]]
    csv_period = csv_period[csv_period["Entry Time"] >= end_date]
    csv_period = csv_period[csv_period["Exit Time"] < next_date]
    wfa = csv_period.copy()
    
    return best_csv, wfa


if __name__ == "__main__":
    
    wfa_periods = [1, 3, 7, 14, 30, 60, 90]
    money_per_trade = 1000
    commission = 0
    symbols = ["LTCUSD", "BTCUSD", "BCHUSD", "ETHUSD"]
    
    all_files = []
    for symbol in symbols:
        files = [f for f in os.listdir(symbol) if os.path.isfile(os.path.join(symbol, f))]
        files = [f for f in files if ".csv" in f]
        [all_files.append(symbol + "/" + f) for f in files]
    
    csvs = []
    params = []
    earliest_date = None
    latest_date = None
    for file_i, file in enumerate(all_files):
        
        #if file_i % 10 == 0:
        #    print("File", file_i, "of", len(files))
        
        csv = pd.read_csv(file)
        csv = csv.drop(columns=["Unnamed: 0"])
        csv["Entry Time"] = pd.to_datetime(csv["Entry Time"])
        csv["Exit Time"] = pd.to_datetime(csv["Exit Time"])
        
        if earliest_date == None:
            earliest_date = csv["Entry Time"].values[0]
        elif csv["Entry Time"].values[0] < earliest_date:
            earliest_date = csv["Entry Time"].values[0]
            
        if latest_date == None:
            latest_date = csv["Exit Time"].values[-1]
        elif csv["Exit Time"].values[-1] > latest_date:
            latest_date = csv["Exit Time"].values[-1]
        
        csvs.append(csv)#get_backtest(csv, money_per_trade, commission))
        
        period, diff = file.split("/")[1].replace(".csv", "").split("_")
        
        period = int(period)
        diff = int(diff)
        symbol = file.split("/")[0]
        
        params.append([period, diff, symbol])
        
    earliest_date = pd.to_datetime(earliest_date)
    latest_date = pd.to_datetime(latest_date)
    
    wfa_results = []
    
    for wfa_period in wfa_periods:

        date = dt(earliest_date.year, earliest_date.month, earliest_date.day)
        window_dates = []
        while date < latest_date:
            window_dates.append(date)
            date += td(days=wfa_period)

        inputs = []
        for window in range(len(window_dates) - 2):
            inputs.append([window_dates[window], window_dates[window+1], window_dates[window+2], window, len(window_dates) - 2, wfa_period])
        
        pool = mp.Pool(mp.cpu_count())
        results = pool.starmap(process_window, inputs, chunksize=1)
        pool.close()
        
        best_csvs = []
        wfas = []
        for result in results:
            best_csv, wfa = result
            best_csvs.append(best_csv)
            wfas.append(wfa)
            
        best_csvs = pd.concat(best_csvs)
        best_csvs = best_csvs.reset_index(drop=True)
        wfas = pd.concat(wfas)
        wfas = wfas.reset_index(drop=True)

        best_csvs.to_csv("best_multi_"+str(wfa_period)+".csv")
        wfas.to_csv("wfa_multi_"+str(wfa_period)+".csv")

        best_csvs_backtest = get_backtest(best_csvs, money_per_trade, commission)
        wfa_backtest = get_backtest(wfas, money_per_trade, commission)

        wfa_results.append([wfa_period, wfa_backtest["Accum Returns"].values[-1] - best_csvs_backtest["Accum Returns"].values[-1]])

    wfa_results = pd.DataFrame(wfa_results, columns=["wfa_period", "diff"])
    wfa_results = wfa_results.sort_values(by=['diff'], ascending=False)
    
    print(wfa_results)