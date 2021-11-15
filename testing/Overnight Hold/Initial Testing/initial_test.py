from alpaca_trade_api.rest import REST, TimeFrame
from datetime import datetime as dt
from datetime import timedelta as td
import pandas_market_calendars as mcal
import multiprocessing as mp
import os, logging, pytz, sys
import pandas as pd

#Change enviornment variables to deal with rate limiter
os.environ["APCA_RETRY_MAX"] = "100"
os.environ["APCA_RETRY_WAIT"] = "2"
#os.environ["APCA_RETRY_CODES"] = "429"

#Change Alpaca logger to critical to avoid printing outrate limit messages
logger = logging.getLogger("alpaca_trade_api")
logger.setLevel(logging.CRITICAL)

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
    with open("../../../credentials.txt") as file:
        
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

def get_symbols_api(api):
    '''
    Get all symbols from Alpaca API.
    Args:
        obj: api - Alpaca API object
    Returns:
        list: symbols - List of symbols from Alpaca API
    '''
    
    #Get all assets
    assets_list = api.list_assets()

    #Get symbol for each asset
    asset_list = {}
    symbols = []
    for asset in assets_list:
        asset_list[asset.symbol] = asset
        symbols.append(asset.symbol)

    #Return symbols
    return symbols

def get_market_dates(begin_date, end_date):
    '''
    Get dates on which market was/is open.
    Args:
        datetime: begin_date - Date at start of period to check
        datetime: end_date - Date at end of period to check
    Returns:
        list: dates - Dates at which market is/was open in period requested
    '''
    
    #Initialise list of dates
    dates = []
    
    #Get NYSE calendar
    nyse = mcal.get_calendar('NYSE')
    
    #Get days on which market is open
    days = nyse.valid_days(start_date=begin_date, end_date=end_date).tolist()
    for day in days:
        dates.append(dt(day.year, day.month, day.day))
            
    #Return days in which market is open
    return dates

def get_prices(api, symbol, date):
    '''
    Get OHLCV data for symbol for a given date.
    Args:
        obj: api - Alpaca API object
        str: symbol - Asset needed
        datetime: date - Date for which to get data
    Returns:
        dataframe: prices - OHLCV data
    '''
    
    #Parse date into string
    date_str = str(date.year)+"-"+str(date.month).zfill(2)+"-"+str(date.day).zfill(2)
    
    #Get OHLCV data
    prices = api.get_bars(symbol, TimeFrame.Minute, date_str, date_str, adjustment='all', limit=100000000).df
    
    if prices.empty:
        return prices
    
    #Rename columns
    prices = prices[["open", "high", "low", "close", "volume"]]
    
    #Return prices
    return prices

def get_daily_change(api, symbol_i, symbol, entry_date, entry_time):
    '''
    Get % change for a symbol for a given date upto a given time.
    Args:
        obj: api - Alpaca API object
        int: symbol_i - Symbol number
        str: symbol - Asset needed
        datetime: entry_date - Date for which to get data
        str: entry_time - Time to enter trade, i.e. time upto which to get % change
    Returns:
        str: symbol - Date for which to get data
        float: change - % change
        int: direction - Long(1) or Short(-1)
        float: open_price
        float: close_price
        long: volume
    '''
    
    try:
        #Logging
        if symbol_i != 0 and symbol_i % 1000 == 0:
            print("Getting symbol", symbol_i, ":", symbol)
            
        #Get OHLCV for symbols
        df = get_prices(api, symbol, entry_date)
        if df.empty:
            return symbol, 0, 1, 0, 0, 0
        df = df.tz_convert('US/Eastern')

        #Create bounds for data
        entry_str = str(entry_date.year) + "-" + str(entry_date.month).zfill(2) + "-" + str(entry_date.day).zfill(2) + " " + "09:30:00"
        exit_str = str(entry_date.year) + "-" + str(entry_date.month).zfill(2) + "-" + str(entry_date.day).zfill(2) + " " + entry_time
        
        #If no data in range, output zeros
        if len(df.loc[entry_str:exit_str]["open"].values) == 0:
            return symbol, 0, 1, 0, 0, 0

        #Get prices, %change and volume
        open_price = df.loc[entry_str:exit_str]["open"].values[0]
        close_price = df.loc[entry_str:exit_str]["open"].values[-1]
        change = (close_price - open_price) / open_price * 100
        volume = df["volume"].cumsum().values[-1]

        #Return values
        if change < 0:
            return [symbol, abs(change), -1, open_price, close_price, volume]
        else:
            return [symbol, change, 1, open_price, close_price, volume]
        
    except Exception as e:
        #print(e)
        return symbol, 0, 1, 0, 0, 0

def get_daily_changes(api, symbols, market_dates, entry_time):
    '''
    Get gainers and losers for each date.
    Args:
        obj: api - Alpaca API object
        list: symbols - List of symbols for which there is data
        list: market_dates - List of dates for which to get gainers/losers list
        str: entry_time - Time upto which to calculate gainers/losers list
    Returns:
        dict: daily_changes - Dict of gainers/losers for each date
    '''
    
    #Open pool of workers
    pool = mp.Pool(2000)
    
    #Initialise dict for final answers
    daily_changes = {}
    
    #For each market date
    for date_i, date in enumerate(market_dates[:-1]):
        
        #Logging
        print("Getting daily changes for date", date_i+1, "of", len(market_dates), ":", str(date.day).zfill(2)+"-"+str(date.month).zfill(2)+"-"+str(date.year))
        
        #Prepare inputs for workers
        inputs = []
        for symbol_i, symbol in enumerate(symbols):
            inputs.append([api, symbol_i, symbol, date, entry_time])
            
        #Get daily change for each symbol for the day
        results = pool.starmap(get_daily_change, inputs, chunksize=1)
        
        #Add changes to list
        changes = []
        for result in results:
            changes.append(result)
           
        #Sort list
        changes = sorted(changes, key=lambda x: (x[1]))
        changes = changes[::-1]
        
        #Add list to dict
        daily_changes[date] = changes
        
    #Close pool of workers
    pool.close()
    
    #Return dict of gainers/losers list
    return daily_changes

def is_dst(date=None, timezone="America/New_York"):
    '''
    Check if date is in daylight saving time for a given timezone.
    Args:
        datetime: date - Date to check
        str: timezone - Timezone to check
    Returns:
        bool: is_dst - True if date is in daylight saving time, False if not
    '''
    
    if date is None:
        date = dt.utcnow()
    timezone = pytz.timezone(timezone)
    timezone_aware_date = timezone.localize(date, is_dst=None)
    return timezone_aware_date.tzinfo._dst.seconds != 0

def process_quotes(data):
    '''
    Process quotes to get min/max/mean/median bid/ask prices per minute.
    Args:
        dataframe: data - Quote data from Alpaca API
    Returns:
        dataframe: data - Treated data
    '''
    
    data = data[["ask_price", "bid_price"]]
        
    data1 = data.resample("T").min()
    data1.columns=["min_ask_price", "min_bid_price"]
        
    data2 = data.resample("T").max()
    data2.columns=["max_ask_price", "max_bid_price"]
        
    data3 = data.resample("T").mean()
    data3.columns=["mean_ask_price", "mean_bid_price"]
        
    data4 = data.resample("T").median()
    data4.columns=["median_ask_price", "median_bid_price"]
        
    data = data1.join([data2, data3, data4])
    
    return data

def get_initial_quotes(api, symbol, date, entry_time, limit=100000000000):
    '''
    Get quotes from given time until EOD for a given date.
    Args:
        obj: api - Alpaca API object
        str: symbol - Asset's symbol
        datetime: date - Date for which to get quotes
        str: entry_time - Time from which to get quotes
        long: limit - Number of rows returned by Alpaca
    Returns:
        dataframe: data - Quotes
    '''
    
    #Get right time extension
    if is_dst(date):
        time_ext = "-04:00"
    else:
        time_ext = "-05:00"
     
    #Parse time boundaries
    entry_date_str = str(date.year) + "-" + str(date.month).zfill(2) + "-" + str(date.day).zfill(2) + "T" + str(date.hour).zfill(2) + ":" + str(date.minute).zfill(2) + ":00" + time_ext
    exit_date_str = str(date.year) + "-" + str(date.month).zfill(2) + "-" + str(date.day).zfill(2) + "T15:59:00" + time_ext

    #Get quotes
    try:
        data = api.get_quotes(symbol, entry_date_str, exit_date_str, limit=limit).df
        data = data.tz_convert('US/Eastern')
    except:
        return pd.DataFrame()
    
    #Return empty dataframe if empty
    if data.empty == True:
        return pd.DataFrame()
    
    #Process quotes
    data = process_quotes(data)
    
    #Return quotes
    return data

def get_quotes(api, symbol, entry_date, exit_date, entry_time, exit_time, direction):
    '''
    Get entry/exit quotes and their time.
    Args:
        obj: api - Alpaca API object
        str: symbol - Asset's symbol
        datetime: entry_date - Date for which to get entry quotes
        datetime: exit_date - Date for which to get exit quotes
        str: entry_time - Time to enter trade
        str: exit_time - Time to exit trade
        int: direction - Direction of trade
    Returns:
        timestamp: entry_ts - Timestamp for trade entry
        timestamp: exit_ts - Timestamp for trade exit
        float: entry_price - Trade entry price
        float: exit_price - Trade exit price
    '''
    
    #Treat times to get values
    entry_hour, entry_minute = map(int, entry_time.split(":"))
    exit_hour, exit_minute = map(int, exit_time.split(":"))
    
    #Increment entry time
    if entry_minute == 59:
        entry_hour += 1
        entry_minute = 0
    else:
        entry_minute += 1
    
    #Create datetime object for entry/exit time/date
    entry_date = dt(entry_date.year, entry_date.month, entry_date.day, entry_hour, entry_minute)
    exit_date = dt(exit_date.year, exit_date.month, exit_date.day, exit_hour, exit_minute)
    
    #Get quotes
    entry_quotes = get_initial_quotes(api, symbol, entry_date, entry_time)
    exit_quotes = get_initial_quotes(api, symbol, exit_date, exit_time, limit=10000)
    
    #If either of quotes is empty, return none
    if entry_quotes.empty or exit_quotes.empty:
        return None
    
    #Return prices
    if direction == 1:
        return entry_quotes.index.values[0], exit_quotes.index.values[0], entry_quotes["median_ask_price"].values[0], exit_quotes["median_bid_price"].values[0]
    else:
        return entry_quotes.index.values[0], exit_quotes.index.values[0], entry_quotes["median_bid_price"].values[0], exit_quotes["median_ask_price"].values[0]
        
def simulation(api, market_dates, daily_changes, entry_time, exit_time):
    '''
    Perform backtest simulation.
    Args:
        obj: api - Alpaca API object
        list: market_dates - List of dates for which to get gainers/losers list
        daily_changes - Dict of gainers/losers for each date
        str: entry_time - Time to enter trade
        str: exit_time - Time to exit trade
    '''
        
    #List of trades taken
    history = []
    
    #Loop through each day market is open
    for date_i, date in enumerate(market_dates[:-1]):
        
        #Get list of gainers/losers
        changes = daily_changes[date]
        
        #Counter to place 4 trades per day
        counter = 0
        
        #For each symbol in losers/gainers
        for change in changes:
            
            #Get change
            symbol, change, direction, open_price, close_price, volume = change
            
            #Get trade quotes
            quotes = get_quotes(api, symbol, date, market_dates[date_i+1], entry_time, exit_time, direction)
            if quotes == None:
                continue
            
            entry_time_sig, exit_time_sig, entry_price, exit_price = quotes
            counter += 1
            
            #Logging
            print(symbol, entry_price, exit_price)
            
            if direction == 1:
                direction_str = "LONG"
            else:
                direction_str = "SHORT"
                
            #Logging
            history.append([entry_time_sig, exit_time_sig, symbol, direction_str, entry_price, exit_price])
            
            #If 4 trades made, move on to next day
            if counter == 4:
                break
            
    #Save history to file
    history = pd.DataFrame(history)
    history.columns = ["Entry Time", "Exit Time", "Symbol", "Direction", "Entry", "Exit"]
    
    history["Entry Time"] = pd.Index(history["Entry Time"]).tz_localize("UTC").tz_convert('US/Eastern')
    history["Exit Time"] = pd.Index(history["Exit Time"]).tz_localize("UTC").tz_convert('US/Eastern')
    
    history.to_csv(sys.argv[0].replace(".py", ".csv"))
            
if __name__ == "__main__":
    
    #Date at which backtest to start
    begin_date = dt(2016, 7, 1)
    
    #Date at which backtest to end
    end_date = dt(2017, 7, 1)
    
    #Time to get into trade
    entry_time = "15:50"
    
    #Time to get out of trade
    exit_time = "09:30"
    
    #Load API keys
    key_id, secret_key = load_credentials("paper")
    
    #Create API connection
    api = REST(key_id, secret_key, base_url='https://paper-api.alpaca.markets')
    
    #Get all symbols given by Alpaca
    symbols = get_symbols_api(api)
    
    #Get all market dates in backtest period
    market_dates = get_market_dates(begin_date, end_date)
    
    #Get lists of daily losers/gainers
    daily_changes = get_daily_changes(api, symbols, market_dates, entry_time)
        
    #Perform backtest
    simulation(api, market_dates, daily_changes, entry_time, exit_time)