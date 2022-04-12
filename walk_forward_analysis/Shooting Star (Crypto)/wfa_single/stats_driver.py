import os
import multiprocessing as mp

files = [f for f in os.listdir(".") if os.path.isfile(os.path.join(".", f))]
files = [f for f in files if ".csv" in f]
    
inputs = []
for file in files:
    inputs.append("python /home/users/dgalea/stock_trading/testing/stats.py \"/home/users/dgalea/stock_trading/walk_forward_analysis/Shooting Star (Crypto)/wfa_single/" + file + "\"")

pool = mp.Pool(20)
pool.map(os.system, inputs)
pool.close()