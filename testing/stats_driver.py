import os, sys
import multiprocessing as mp

if __name__ == "__main__":

    path = sys.argv[1]

    files = [f for f in os.listdir(path) if os.path.isfile(os.path.join(path, f))]
    files = [f for f in files if ".csv" in f]

    inputs = []
    for file in files:
        inputs.append("python stats.py \""+ path + "" + file + "\"")

    pool = mp.Pool(len(files))
    pool.map(os.system, inputs)
    pool.close()