from alpaca_trade_api.rest import REST, TimeFrame, TimeFrameUnit
import sys
sys.path.insert(0, "/Users/danielgalea/Documents/git/stock_trading") 
from common_funcs import load_credentials, get_crypto_prices, get_crypto_quotes, log_trades
import multiprocessing as mp
import pandas as pd
from datetime import timedelta as td

def simulation(api, symbol, prices, shadow_length, daily_data, pool):
    
	daily_data["ma"] = daily_data["close"].rolling(20).mean()
    
	open_trades_times = []
	close_trades_times = []

	years = prices.index.year.values
	months = prices.index.month.values
	days = prices.index.day.values
	hours = prices.index.hour.values
	indexes = prices.index.values

	for row in range(len(prices)-1):
        
		values = prices.iloc[row]
		open_price = values.open
		close_price = values.close
		high_price = values.high
		low_price = values.low

		if years[row] == 2018 and months[row] == 2 and (days[row] in [2, 3, 4, 5] or (days[row] == 2 and hours[row] >= 17)):
			continue

		body_length = abs(open_price - close_price)
		if open_price <= close_price:
			upper_wick_length = abs(high_price - close_price)
			lower_wick_length = abs(open_price - low_price)
		elif open_price > close_price:
			upper_wick_length = abs(high_price - open_price)
			lower_wick_length = abs(close_price - low_price)

		day_minus_1 = pd.to_datetime(indexes[row]) - td(days=1)
		day_minus_2 = pd.to_datetime(indexes[row]) - td(days=2)
		
		day_minus_1_str = str(day_minus_1.year) + "-" + str(day_minus_1.month).zfill(2) + "-" + str(day_minus_1.day).zfill(2)
		day_minus_2_str = str(day_minus_2.year) + "-" + str(day_minus_2.month).zfill(2) + "-" + str(day_minus_2.day).zfill(2)
		
		if close_price > open_price and close_price == high_price and lower_wick_length > body_length * shadow_length and daily_data[day_minus_2_str]["ma"].values[0] < daily_data[day_minus_1_str]["ma"].values[0]:
			_, quotes = get_crypto_quotes(api, symbol, indexes[row], 0)
			prev_diff = quotes.median_ask_price.values[0] - quotes.median_bid_price.values[0]
			if prev_diff < 100 and len(open_trades_times) == len(close_trades_times):
				open_trades_times.append([indexes[row+1], close_price])

		if close_price < open_price and upper_wick_length > lower_wick_length and upper_wick_length > body_length * shadow_length:
			if len(open_trades_times) - 1 == len(close_trades_times):
				close_trades_times.append([indexes[row+1], close_price])
                
	inter_open_trades = []
	inter_close_trades = []

	inputs = []
	for open_time in open_trades_times:
		inputs.append([api, symbol, open_time[0], 37])

	results = pool.starmap(get_crypto_quotes, inputs, chunksize=1)

	for res_i, res in enumerate(results):
		date, quotes = res
		if not quotes.empty:
			inter_open_trades.append([date, symbol, quotes.median_ask_price[0]])
		else:
			inter_open_trades.append([date, symbol, open_trades_times[res_i][1] * 1.005])
		
	inputs = []
	for close_time in close_trades_times:
		inputs.append([api, symbol, close_time[0], 32])

	results = pool.starmap(get_crypto_quotes, inputs, chunksize=1)

	for res_i, res in enumerate(results):
		date, quotes = res
		if not quotes.empty:
			inter_close_trades.append([date, symbol, quotes.median_bid_price[0]])
		else:
			inter_close_trades.append([date, symbol, open_trades_times[res_i][1] * 0.995])
			
	if len(inter_open_trades) - 1 == len(inter_close_trades):
		inter_open_trades = inter_open_trades[:-1]

	open_trades = []
	close_trades = []

	if len(inter_open_trades) > 1:
		
		open_counter = 1
		close_counter = 0
		
		open_trades.append(inter_open_trades[0])
		while open_counter < len(inter_open_trades):
			if inter_close_trades[close_counter][0] >= inter_open_trades[open_counter][0]:
				pass
			else:
				close_trades.append(inter_close_trades[close_counter])
				open_trades.append(inter_open_trades[open_counter])
			open_counter += 1
			close_counter += 1
		close_trades.append(inter_close_trades[close_counter])
		
	return open_trades, close_trades
        
def get_daily_data(api, symbol, start, end):
    
    data = api.get_crypto_bars(symbol, TimeFrame(1, TimeFrameUnit.Day), start, end).df
    data = data.tz_convert('US/Eastern')
    data = data[data["exchange"] == "CBSE"]
    
    return data

if __name__ == "__main__":

	symbol = "BTCUSD"
	start_date = "2017-07-01"
	end_date = "2018-07-01"
	period = 15
	shadow_length = 1

	key_id, secret_key = load_credentials(opt="paper")
	api = REST(key_id, secret_key, base_url='https://paper-api.alpaca.markets')
	
	print("Getting prices...")
	prices = get_crypto_prices(api, symbol, start_date, end_date, [period])[period]
	daily_data = get_daily_data(api, symbol, "2016-07-01", end_date)
	print("Prices pbtained.")

	pool = mp.Pool(10)
	open_trades, close_trades = simulation(api, symbol, prices, shadow_length, daily_data, pool)
	pool.close()
	
	log_trades(open_trades, close_trades, name=sys.argv[0].replace(".py", ""), save=True)
    