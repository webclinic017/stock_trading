import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from datetime import datetime as dt
import yfinance as yf
import os, sys
import seaborn as sns

sys.path.insert(0, "/Users/danielgalea/Documents/git/stock_trading") 
from common_funcs import get_backtest, get_daily_returns, get_underwater_data, get_monte_carlo, accum_return, annual_return, max_dd, annual_sharpe_ratio, win_perc, avg_return, avg_win, avg_loss, largest_loss, largest_win, consecutive_losses, consecutive_wins

if __name__ == "__main__":
    
    money_per_trade = 1000
    stop_trading = -1000
    commission = 6
    
    path = sys.argv[1]
    df = pd.read_csv(path)
    
    backtest = get_backtest(df, money_per_trade, commission)
    
    daily_backtest_both = get_daily_returns(backtest, "Both")
    daily_backtest_long = get_daily_returns(backtest, "LONG")
    daily_backtest_short = get_daily_returns(backtest, "SHORT")
    
    #comp_returns = daily_compounded_returns(daily_backtest_both)
    
    fig, axs = plt.subplots(4, 3, figsize=(12, 12))
    
    backtest.plot(y="Accum Returns", ax=axs[0][0], label="Returns")
    axs[0][0].set_title("Accumulated Returns")
    axs[0][0].set_xlabel("Trade Count")
    
    underwater, underwater_perc = get_underwater_data(backtest)
    axs[0][1].plot(underwater, label="Amount")
    axs[0][1].set_title("Underwater Plot")
    axs[0][1].set_xlabel("Trade Count")
    axs[0][1].set_ylabel("Amount", color="b")
    
    secondy = axs[0][1].twinx()
    secondy.plot(underwater_perc, color="r")
    secondy.set_ylabel("Percentage", color="r")
    
    df_month = pd.DataFrame({"Dates": daily_backtest_both["Dates"], "Return": daily_backtest_both["Daily Returns"]})
    df_month = df_month.set_index("Dates")
    df_month = df_month.resample("M").sum()
    
    dates_dt = df_month.index.to_pydatetime()
    months = []
    years = []
    for date in dates_dt:
        months.append(date.month)
        years.append(date.year)
    df_month["Month"] = months
    df_month["Year"] = years
        
    month_vs_year = df_month.pivot_table(index="Month",columns="Year", aggfunc="sum").fillna(0)
    sns.heatmap(month_vs_year, ax=axs[0][2], annot=True, fmt='g')
    axs[0][2].set_xlabel("Year")
    axs[0][2].set_title("Monthly Returns")
    
    df_month = pd.DataFrame({"Dates": daily_backtest_both["Dates"], "Return": daily_backtest_both["Daily Returns"]})
    df_month = df_month.set_index("Dates")
    
    dates_dt = df_month.index.to_pydatetime()
    days = []
    years = []
    for date in dates_dt:
        days.append(date.weekday())
        years.append(date.year)
    df_month["Day"] = days
    df_month["Year"] = years
    day_vs_year = df_month.pivot_table(index="Day",columns="Year", aggfunc = "sum").fillna(0)
    sns.heatmap(day_vs_year, ax=axs[2][2], annot=True, fmt='g')
    axs[2][2].set_xlabel("Year")
    axs[2][2].set_title("Daily Returns")
    
    daily_backtest_both.plot(x="Dates", y="Daily Returns", ax=axs[1][0])
    axs[1][0].set_title("Daily Returns")
    
    daily_backtest_both["Accum Returns"] = daily_backtest_both.sort_values("Dates")["Daily Returns"].cumsum() / 1000 * 100
    daily_backtest_both.plot(x="Dates", y="Accum Returns", ax=axs[1][1])
    #comp_returns.plot(x="Dates", y="Accum Returns", ax=axs[1][1], label="Comp Returns")
    axs[1][1].set_title("Daily Accum Returns")
    
    start_date_str = str(daily_backtest_both.sort_values("Dates")["Dates"].values[0]).split("T")[0]
    end_date_str = str(daily_backtest_both.sort_values("Dates")["Dates"].values[-1]).split("T")[0]
    
    spy = yf.download("^GSPC", start=start_date_str, end=end_date_str)
    spy["Close"] = (spy["Close"] - spy["Close"].values[0]) / spy["Close"].values[0] * 100
    spy.plot(y="Close", label = "SPY", ax=axs[1][1])
    
    dji = yf.download("^DJI", start=start_date_str, end=end_date_str)
    dji["Close"] = (dji["Close"] - dji["Close"].values[0]) / dji["Close"].values[0] * 100
    dji.plot(y="Close", label = "DJI", ax=axs[1][1])
    
    ixic = yf.download("^IXIC", start=start_date_str, end=end_date_str)
    ixic["Close"] = (ixic["Close"] - ixic["Close"].values[0]) / ixic["Close"].values[0] * 100
    ixic.plot(y="Close", label = "^IXIC", ax=axs[1][1])
    axs[1][1].set_ylabel("% Return")
    
    bins = np.array(list(range(100))) - 50
    perc = backtest["Return"].values / backtest["Entry"].values * 100
    axs[1][2].hist(perc, bins=bins)
    axs[1][2].set_xlabel("% Returns")
    axs[1][2].set_ylabel("Count")
    axs[1][2].set_title("Return Distribution")
    
    poss, mean, plus_std, plus_2std, minus_std, minus_2std = get_monte_carlo(backtest, 1000, stop_trading)
    init_portfolio = [4000, 5000, 6000, 7000, 8000, 9000, 10000, 11000, 12000, 13000, 14000, 15000, 16000, 17000, 18000, 19000, 20000]
    ror = []
    for init in init_portfolio:
        count = 0
        for p in poss:
            if init + p[-1] < stop_trading:
                count += 1
        ror.append(count/len(poss) * 100.)
    axs[2][0].plot(init_portfolio, ror, "o-")
    axs[2][0].set_xlabel("Inital Portfolio")
    axs[2][0].set_ylabel("Risk of Ruin / %")
    axs[2][0].set_title("Risk of Ruin")
    
    for p in poss[:100]:
        
        axs[2][1].plot(p, color="y")
    axs[2][1].plot(mean, label="Mean", color="k")
    axs[2][1].plot(plus_std, label="+Std Dev", color="b")
    axs[2][1].plot(minus_std, label="-Std Dev", color="b")
    axs[2][1].plot(plus_2std, label="+2Std Dev", color="r")
    axs[2][1].plot(minus_2std, label="-2Std Dev", color="r")
    axs[2][1].legend()
    rows = []
    data = []
    
    accum_return_total = accum_return(backtest, "Both")
    accum_return_long = accum_return(backtest, "LONG")
    accum_return_short = accum_return(backtest, "SHORT")
    data.append(["Accum. Return", accum_return_total, accum_return_long, accum_return_short])

    ann_ret_total = annual_return(daily_backtest_both)
    ann_ret_long = annual_return(daily_backtest_long)
    ann_ret_short = annual_return(daily_backtest_short)
    data.append(["Annual Return", ann_ret_total, ann_ret_long, ann_ret_short])

    max_dd_total = max_dd(backtest, "Both")
    max_dd_long = max_dd(backtest, "LONG")
    max_dd_short = max_dd(backtest, "SHORT")
    data.append(["Max DD", max_dd_total, max_dd_long, max_dd_short])
    
    sharpe_total = annual_sharpe_ratio(daily_backtest_both)
    sharpe_long = annual_sharpe_ratio(daily_backtest_long)
    sharpe_short = annual_sharpe_ratio(daily_backtest_short)
    data.append(["Annual Sharpe Ratio", sharpe_total, sharpe_long, sharpe_short])

    win_perc_total = win_perc(backtest, "Both")
    win_perc_long = win_perc(backtest, "LONG")
    win_perc_short = win_perc(backtest, "SHORT")
    data.append(["Win %", win_perc_total, win_perc_long, win_perc_short])

    avg_return_total = avg_return(backtest, "Both")
    avg_return_long = avg_return(backtest, "LONG")
    avg_return_short = avg_return(backtest, "SHORT")
    data.append(["Avg Return", avg_return_total, avg_return_long, avg_return_short])
    
    avg_win_total = avg_win(backtest, "Both")
    avg_win_long = avg_win(backtest, "LONG")
    avg_win_short = avg_win(backtest, "SHORT")
    data.append(["Avg Win", avg_win_total, avg_win_long, avg_win_short])
    
    avg_loss_total = avg_loss(backtest, "Both")
    avg_loss_long = avg_loss(backtest, "LONG")
    avg_loss_short = avg_loss(backtest, "SHORT")
    data.append(["Avg Loss", avg_loss_total, avg_loss_long, avg_loss_short])

    largest_win_total = largest_win(backtest, "Both")
    largest_win_long = largest_win(backtest, "LONG")
    largest_win_short = largest_win(backtest, "SHORT")
    data.append(["Largest Win", largest_win_total, largest_win_long, largest_win_short])

    largest_loss_total = largest_loss(backtest, "Both")
    largest_loss_long = largest_loss(backtest, "LONG")
    largest_loss_short = largest_loss(backtest, "SHORT")
    data.append(["Largest Loss", largest_loss_total, largest_loss_long, largest_loss_short])

    cons_wins_total = consecutive_wins(backtest, "Both")
    cons_wins_long = consecutive_wins(backtest, "LONG")
    cons_wins_short = consecutive_wins(backtest, "SHORT")
    data.append(["Max Consecutive Wins", cons_wins_total, cons_wins_long, cons_wins_short])

    cons_losses_total = consecutive_losses(backtest, "Both")
    cons_losses_long = consecutive_losses(backtest, "LONG")
    cons_losses_short = consecutive_losses(backtest, "SHORT")
    data.append(["Max Consecutive Losses", cons_losses_total, cons_losses_long, cons_losses_short])
    
    tharp_total = (avg_win_total * win_perc_total + avg_loss_total * (100 - win_perc_total)) / -(avg_loss_total + 1e-6)
    tharp_long = (avg_win_long * win_perc_long + avg_loss_long * (100 - win_perc_long)) / -(avg_loss_long + 1e-6)
    tharp_short = (avg_win_short * win_perc_short + avg_loss_short * (100 - win_perc_short)) / -(avg_loss_short + 1e-6)
    data.append(["Tharp Expectancy", tharp_total, tharp_long, tharp_short])
    
    results = pd.DataFrame(data)
    results.columns = ["Index", "Total", "Long", "Short"]
    results.set_index("Index")
    results["Total"] = results["Total"].astype(float).round(2)
    results["Long"] = results["Long"].astype(float).round(2)
    results["Short"] = results["Short"].astype(float).round(2)
    
    print(results)
    
    gs = axs[3, 0].get_gridspec()
    # remove the underlying axes
    for ax in axs[3, :]:
        ax.remove()
    axbig = fig.add_subplot(gs[3, :])
    
    tab = axbig.table(cellText=results.values, colWidths = [0.25]*len(results.columns), rowLabels=results.index, colLabels=results.columns, cellLoc = 'center', rowLoc = 'center', loc='center')
    tab.auto_set_font_size(False)
    tab.set_fontsize(8)
    axbig.axis("off")
    
    plt.tight_layout()
    plt.savefig(path.replace("csv", "png"))
    
