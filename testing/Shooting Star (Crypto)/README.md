## Shooting Star (Crypto)

Enter on a hammer pattern (green candle - long bottom shadow; little to no upper shadow) and exit on a shooting star (red candle - long upper shadow; little to no lower shadow)

Variations:
   - shooting_star: Strict rules as above - no upper/lower shadow for entry/exit
   - variation1: Strict rules as above but shorter lower shadow than upper shadow for entry
   - variation2: Shorter upper shadow than lower shadow for exit
   - variation3: variation1 + variation2: Shorter lower shadow than upper shadow for entry and shorter upper shadow than lower shadow for exit
   - variation4: variation3 + Entry candle does not have to be green and exit candle does not have to be red
   - variation5: Entry candle has to be green and exit candle does not have to be red
   - variation6: Entry candle does not have to be green and exit candle has to be red  
   - variation7: variation1 + MA8 > MA13 for entry
   - **variation8: variation1 + MA8 < MA13 for exit**
   - variation9: variation1 + MA8 > MA13 for entry and MA8 < MA13 for exit
   - variation10: Daily 20MA of day-1 must be higher than that of day-2
   - variation11: Median Bid-Ask spread of previous timestep has to be < \$100
   - variation12: variation10 + variation11
   
Results:
   - shooting_star: 963.81
   - variation1: -2707.53
   - variation2: -415.07
   - variation3: -7184.58
   - variation4: -16644.19
   - variation5: -10765.41
   - variation6: -9451.15
   - variation7: 1078.14
   - variation8: 1153.66
   - variation9: 981.28
   - variation10: 967.1
   - variation11: 963.81
   - variation12: -1002.45
    
Files:
   - .py - backtesting scripts
   - .csv - backtest outputs
   - .png - backtest stats
    
Folders:
   - diff_market_diff_time_testing - Testing shooting_star on different markets at different bar lengths. market_check.ods summarises results.
   - shadow_length_effect - Test different values of shadow_length to see effect. Reslts in results.csv. TLDR: Longer shadow = less trades, higher win% and avg return, lower overall profit.