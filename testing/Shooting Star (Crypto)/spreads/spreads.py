import pandas as pd
from datetime import datetime as dt
import matplotlib.pyplot as plt
import pytz
import numpy as np

def get_data(symbol, start_date, end_date, period):
    
    prices = pd.read_csv("/gws/nopw/j04/hiresgw/dg/crypto_minute_data/" + symbol + "_prices.csv")
    quotes = pd.read_csv("/gws/nopw/j04/hiresgw/dg/crypto_minute_quotes/" + symbol + "_quotes.csv")
    
    prices = prices[prices["exchange"] == "CBSE"]
    
    prices["timestamp"] = pd.to_datetime(prices["timestamp"], utc=True)
    prices = prices.set_index("timestamp")
    prices = prices.tz_convert('US/Eastern')
    prices = prices.sort_index()
    
    quotes["timestamp"] = pd.to_datetime(quotes["timestamp"], utc=True)
    quotes = quotes.set_index("timestamp")
    quotes = quotes.tz_convert('US/Eastern')
    quotes = quotes.sort_index()
    
    if period > 1:
        
        opens = prices["open"].resample(str(period) + "min").first()
        closes = prices["close"].resample(str(period) + "min").last()
        highs = prices["high"].resample(str(period) + "min").max()
        lows = prices["low"].resample(str(period) + "min").min()
        vols = prices["volume"].resample(str(period) + "min").sum()
        
        prices = pd.DataFrame([opens, highs, lows, closes, vols]).T
    
    #prices = prices.loc[start_date:end_date]
    #quotes = quotes.loc[start_date:end_date]
    
    return prices, quotes
    

if __name__ == "__main__":
    
    start_date = "2017-07-05 23:15:00-04:00"
    end_date = "2022-03-01 00:00:00-04:00"
    period = 1
    shadow_length = 1
    
    symbols = ['AAVEUSD', 'BATUSD', 'BTCUSD', 'BCHUSD', 'LINKUSD', 'DAIUSD', 'DOGEUSD', 'ETHUSD', 'GRTUSD', 'LTCUSD', 'MKRUSD', 'MATICUSD', 'PAXGUSD', 'SHIBUSD', 'SOLUSD', 'SUSHIUSD', 'USDTUSD', 'TRXUSD', 'UNIUSD', 'WBTCUSD', 'YFIUSD']
    
    for symbol in symbols:
        print(symbol)
        prices, quotes = get_data(symbol, start_date, end_date, period)
        
        quotes = quotes.dropna()
        quotes["diff"] = quotes["median_ask_price"] - quotes["median_bid_price"]
        quant_50 = quotes["diff"].quantile([0.5]).values[0]
        quant_90 = quotes["diff"].quantile([0.9]).values[0]
        quant_95 = quotes["diff"].quantile([0.95]).values[0]
        quant_99 = quotes["diff"].quantile([0.99]).values[0]
        
        plt.figure(figsize=(10, 6))
        
        plt.subplot(121)
        plt.plot(quotes.index.values, quotes["diff"].values, color="r")
        plt.plot(quotes.index.values, quotes["diff"].rolling(20).mean().values, color="b")
        
        plt.subplot(122)
        plt.hist(quotes["diff"].values, bins=100)
        plt.axvline(quant_50, label="50% = " + str(quant_50), color="g")
        plt.axvline(quant_90, label="90% = " + str(quant_90), color="b")
        plt.axvline(quant_95, label="95% = " + str(quant_95), color="k")
        plt.axvline(quant_99, label="99% = " + str(quant_99), color="r")
        plt.legend()
        
        plt.tight_layout()
        plt.savefig(symbol + ".png")