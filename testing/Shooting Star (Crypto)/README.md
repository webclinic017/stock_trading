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
   - variation8: variation1 + MA8 < MA13 for exit
   - variation9: variation1 + MA8 > MA13 for entry and MA8 < MA13 for exit
   - variation10: Daily 20MA of day-1 must be higher than that of day-2
   - **variation11: Median Bid-Ask spread of previous timestep has to be < \$100**
   - variation12: variation10 + variation11
   - variation13: variation11 + shooting_star
    
Results:
   - shooting_star: 2172.04
   - variation1: 918.74
   - variation2: 1794.69
   - variation3: 1121.63
   - variation4: 1037.01
   - variation5: 690.96
   - variation6: 1321.31
   - variation7: 2068.09
   - variation8: 1538.51
   - variation9: 1618.49
   - variation10: 1371.63
   - variation11: 2239.53
   - variation12: 1652.30
   - variation13: 2239.53
    
Files:
   - .py - backtesting scripts
   - .csv - backtest outputs
   - .png - backtest stats
    
Folders:
   - diff_market_diff_time_testing - Testing shooting_star on different markets at different bar lengths. market_check.ods summarises results.
   - shadow_length_effect - Test different values of shadow_length to see effect. Reslts in results.csv. TLDR: Longer shadow = less trades, higher win% and avg return, lower overall profit.