cd diff_symbols
python simulation.py QQQ 1 0.1 2 0.5 100 150 7 &
python simulation.py SPY 1 0.1 2 0.5 100 150 7 &
python simulation.py DIA 1 0.1 2 0.5 100 150 7 &
wait
cd ../diff_exit_time
python simulation.py QQQ 1 0.1 2 0.5 100 150 7 &
python simulation.py QQQ 2 0.1 2 0.5 100 150 7 &
python simulation.py QQQ 3 0.1 2 0.5 100 150 7 &
python simulation.py QQQ 4 0.1 2 0.5 100 150 7 &
python simulation.py QQQ 5 0.1 2 0.5 100 150 7 &
python simulation.py QQQ 10 0.1 2 0.5 100 150 7 &
python simulation.py QQQ 15 0.1 2 0.5 100 150 7 &
wait
python simulation.py QQQ 20 0.1 2 0.5 100 150 7 &
python simulation.py QQQ 30 0.1 2 0.5 100 150 7 &
python simulation.py QQQ 45 0.1 2 0.5 100 150 7 &
python simulation.py QQQ 60 0.1 2 0.5 100 150 7 &
python simulation.py QQQ 90 0.1 2 0.5 100 150 7 &
python simulation.py QQQ 120 0.1 2 0.5 100 150 7 &
python simulation.py QQQ 240 0.1 2 0.5 100 150 7 &
python simulation.py QQQ 360 0.1 2 0.5 100 150 7 &
wait
cd ../diff_no_trade_max
python simulation.py QQQ 1 0.1 0.25 0.5 100 150 7 &
python simulation.py QQQ 1 0.1 0.5 0.5 100 150 7 &
python simulation.py QQQ 1 0.1 0.75 0.5 100 150 7 &
python simulation.py QQQ 1 0.1 1 0.5 100 150 7 &
python simulation.py QQQ 1 0.1 1.25 0.5 100 150 7 &
python simulation.py QQQ 1 0.1 1.5 0.5 100 150 7 &
wait
python simulation.py QQQ 1 0.1 1.75 0.5 100 150 7 &
python simulation.py QQQ 1 0.1 2 0.5 100 150 7 &
python simulation.py QQQ 1 0.1 2.25 0.5 100 150 7 &
python simulation.py QQQ 1 0.1 2.5 0.5 100 150 7 &
python simulation.py QQQ 1 0.1 3 0.5 100 150 7 &
python simulation.py QQQ 1 0.1 4 0.5 100 150 7 &
python simulation.py QQQ 1 0.1 5 0.5 100 150 7 &
wait
cd ../diff_no_trade_min
python simulation.py QQQ 1 0.01 2 0.5 100 150 7 &
python simulation.py QQQ 1 0.05 2 0.5 100 150 7 &
python simulation.py QQQ 1 0.1 2 0.5 100 150 7 &
python simulation.py QQQ 1 0.15 2 0.5 100 150 7 &
python simulation.py QQQ 1 0.2 2 0.5 100 150 7 &
python simulation.py QQQ 1 0.25 2 0.5 100 150 7 &
wait
python simulation.py QQQ 1 0.3 2 0.5 100 150 7 &
python simulation.py QQQ 1 0.35 2 0.5 100 150 7 &
python simulation.py QQQ 1 0.4 2 0.5 100 150 7 &
python simulation.py QQQ 1 0.5 2 0.5 100 150 7 &
python simulation.py QQQ 1 0.75 2 0.5 100 150 7 &
wait
cd ../diff_sl_perc
python simulation.py QQQ 1 0.1 2 0.5 100 10 7 &
python simulation.py QQQ 1 0.1 2 0.5 100 25 7 &
python simulation.py QQQ 1 0.1 2 0.5 100 50 7 &
python simulation.py QQQ 1 0.1 2 0.5 100 75 7 &
python simulation.py QQQ 1 0.1 2 0.5 100 125 7 &
python simulation.py QQQ 1 0.1 2 0.5 100 150 7 &
python simulation.py QQQ 1 0.1 2 0.5 100 200 7 &
python simulation.py QQQ 1 0.1 2 0.5 100 250 7 &
wait
cd ../diff_tp_perc
python simulation.py QQQ 1 0.1 2 0.5 10 150 7 &
python simulation.py QQQ 1 0.1 2 0.5 25 150 7 &
python simulation.py QQQ 1 0.1 2 0.5 50 150 7 &
python simulation.py QQQ 1 0.1 2 0.5 75 150 7 &
python simulation.py QQQ 1 0.1 2 0.5 100 150 7 &
wait
python simulation.py QQQ 1 0.1 2 0.5 150 150 7 &
python simulation.py QQQ 1 0.1 2 0.5 175 150 7 &
python simulation.py QQQ 1 0.1 2 0.5 200 150 7 &
python simulation.py QQQ 1 0.1 2 0.5 250 150 7 &
python simulation.py QQQ 1 0.1 2 0.5 300 150 7 &
wait
cd ../diff_tp_limit
python simulation.py QQQ 1 0.1 2 0.1 100 150 7 &
python simulation.py QQQ 1 0.1 2 0.2 100 150 7 &
python simulation.py QQQ 1 0.1 2 0.3 100 150 7 &
python simulation.py QQQ 1 0.1 2 0.4 100 150 7 &
python simulation.py QQQ 1 0.1 2 0.5 100 150 7 &
python simulation.py QQQ 1 0.1 2 0.75 100 150 7 &
python simulation.py QQQ 1 0.1 2 1 100 150 7 &
python simulation.py QQQ 1 0.1 2 1.5 100 150 7 &
python simulation.py QQQ 1 0.1 2 2 100 150 7 &
wait
cd ../diff_ma_length
python simulation.py QQQ 1 0.1 2 0.5 100 150 2 &
python simulation.py QQQ 1 0.1 2 0.5 100 150 5 &
python simulation.py QQQ 1 0.1 2 0.5 100 150 7 &
python simulation.py QQQ 1 0.1 2 0.5 100 150 10 &
python simulation.py QQQ 1 0.1 2 0.5 100 150 15 &
python simulation.py QQQ 1 0.1 2 0.5 100 150 20 &
python simulation.py QQQ 1 0.1 2 0.5 100 150 50 &