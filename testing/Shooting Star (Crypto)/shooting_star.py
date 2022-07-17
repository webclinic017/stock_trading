from alpaca_trade_api.rest import REST, TimeFrame, TimeFrameUnit
import pandas as pd
import numpy as np
from datetime import datetime as dt
from datetime import timedelta as td
import sys
sys.path.insert(0, "/Users/danielgalea/Documents/git/stock_trading") 
from common_funcs import load_credentials

def get_prices(api, symbol, start_date, end_date, period):

    prices = api.get_crypto_bars(symbol, TimeFrame.Minute, start_date, end_date).df
    prices = prices.tz_convert('US/Eastern')
    prices = prices[prices["exchange"] == "CBSE"]
    
    if period > 1:
    
        opens = prices["open"].resample(str(period) + "min").first()
        closes = prices["close"].resample(str(period) + "min").last()
        highs = prices["high"].resample(str(period) + "min").max()
        lows = prices["low"].resample(str(period) + "min").min()
        vols = prices["volume"].resample(str(period) + "min").sum()

        period_prices = pd.DataFrame([opens, highs, lows, closes, vols]).T
    else:
        period_prices = prices
        
    return period_prices

def get_quotes(api, symbol, init_date, offset=0):
    
	if isinstance(init_date, np.datetime64):
		init_date = pd.to_datetime(init_date).tz_localize("UTC").tz_convert(tz='America/New_York')

	if offset > 0:
		init_date -= td(minutes=1)
		
	init_date_str = init_date.isoformat()
	end_date_str = (init_date + td(minutes=1)).isoformat()
    
	quotes = api.get_crypto_quotes(symbol, init_date_str, end_date_str, limit=1000000).df
    
	while len(quotes) == 0:
		init_date += td(minutes=1)
		init_date_str = init_date.isoformat()
		end_date_str = (init_date + td(minutes=1)).isoformat()
		quotes = api.get_crypto_quotes(symbol, init_date_str, end_date_str, limit=1000000).df

	quotes = process_quotes(quotes)
    
	return init_date, quotes

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
 
def simulation(prices, shadow_length):
    
	open_trades = []
	close_trades = []
    
	last_close_trade = None
	
	for row in range(len(prices)-1):
        
		index = prices.index.values[row]
		values = prices.iloc[row]
		open_price = values.open
		close_price = values.close
		high_price = values.high
		low_price = values.low

		if last_close_trade != None and pd.to_datetime(index).tz_localize("UTC").tz_convert(tz='America/New_York') <= last_close_trade:
			continue

		if prices.index.year.values[row] == 2018 and prices.index.month.values[row] == 2 and (prices.index.day.values[row] in [3, 4, 5] or (prices.index.day.values[row] == 2 and prices.index.hour.values[row] >= 17)):
			continue

		if prices.index.hour.values[row] == 0 and prices.index.minute.values[row] == 0:
			print(index)
		
		body_length = abs(open_price - close_price)
		if open_price <= close_price:
			upper_wick_length = abs(high_price - close_price)
			lower_wick_length = abs(open_price - low_price)
		elif open_price > close_price:
			upper_wick_length = abs(high_price - open_price)
			lower_wick_length = abs(close_price - low_price)

		if close_price > open_price and close_price == high_price and lower_wick_length * shadow_length > body_length:
			if len(open_trades) == len(close_trades):
				date, quotes = get_quotes(api, symbol, index, offset=0)
				open_trades.append([date, quotes.median_ask_price[0]])
				
		if close_price < open_price and close_price == low_price and upper_wick_length * shadow_length > body_length:
			if len(open_trades) - 1 == len(close_trades):
				date, quotes = get_quotes(api, symbol, index, offset=0)
				close_trades.append([date, quotes.median_bid_price[0]])
				last_close_trade = date
		
	if len(open_trades) - 1 == len(close_trades):
		open_trades = open_trades[:-1]
		
	return open_trades, close_trades
        
def log_trades(open_trades, close_trades, symbol):
    
    logs = []
    for i in range(len(open_trades)):
        logs.append([str(open_trades[i][0]), str(close_trades[i][0]), symbol, "LONG", open_trades[i][1], close_trades[i][1]])
        
    history = pd.DataFrame(logs)
    history.columns = ["Entry Time", "Exit Time", "Symbol", "Direction", "Entry", "Exit"]
    
    history["Entry Time"] = pd.Index(pd.to_datetime(history["Entry Time"]))
    history["Exit Time"] = pd.Index(pd.to_datetime(history["Exit Time"]))
    
    history.to_csv(sys.argv[0].replace(".py", ".csv"))

if __name__ == "__main__":

	symbol = "BTCUSD"
	start_date = "2017-07-01"
	end_date = "2018-07-01"
	period = 15
	shadow_length = 1

	key_id, secret_key = load_credentials(opt="paper")
	api = REST(key_id, secret_key, base_url='https://paper-api.alpaca.markets')
	
	print("Getting prices...")
	prices = get_prices(api, symbol, start_date, end_date, period)
	print("Prices pbtained.")

	open_trades, close_trades = simulation(prices, shadow_length)

	log_trades(open_trades, close_trades, symbol)
