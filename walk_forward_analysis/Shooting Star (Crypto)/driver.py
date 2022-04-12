import pandas as pd
import os, sys
import multiprocessing as mp

if __name__ == "__main__":
    
    symbols = ['BTCUSD', 'BCHUSD', 'ETHUSD', 'LTCUSD']
    #symbols = ['AAVEUSD', 'BATUSD', 'LINKUSD', 'DAIUSD', 'DOGEUSD', 'GRTUSD', 'MKRUSD', 'MATICUSD', 'PAXGUSD', 'SHIBUSD', 'SOLUSD', 'SUSHIUSD', 'USDTUSD', 'TRXUSD', 'UNIUSD', 'WBTCUSD', 'YFIUSD']
    
    periods = [1, 2, 3, 4, 5, 10, 15, 20, 30, 45, 60, 120, 240, 360]
    diff_scaling = [1, 2, 3, 4, 5, 10, 25, 50, 100, 250, 500, 1000]
    
    diff_stats = pd.read_csv("diff_stats.csv")
    diff_stats = diff_stats.set_index("Unnamed: 0")
    
    #for symbol in symbols:
    #    os.makedirs(symbol)
    
    inputs = []
    
    for symbol in symbols:
        median = diff_stats["50th"][symbol]
        for period in periods:
            for diff_scale in diff_scaling:
                inputs.append("python simulation.py " + symbol + " " + str(period) + " " + str(median) + " " + str(diff_scale))
     
    os.system(inputs[int(sys.argv[1])])
    
    #pool = mp.Pool(20)
    #pool.map(os.system, inputs, chunksize=1)
    #pool.close()