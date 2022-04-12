import os, sys
import multiprocessing as mp

path = sys.argv[1]

files = [f for f in os.listdir(path) if os.path.isfile(os.path.join(path, f))]
files = [f for f in files if ".csv" in f]
    
inputs = []
for file in files:
    inputs.append("python /home/users/dgalea/stock_trading/testing/stats.py \""+ path + "" + file + "\"")

pool = mp.Pool(20)
pool.map(os.system, inputs)
pool.close()