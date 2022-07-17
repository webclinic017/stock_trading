## Shooting Star (Crypto)

Enter on a hammer pattern (green candle - long bottom shadow; little to no upper shadow) and exit on a shooting star (red candle - long upper shadow; little to no lower shadow)

Variations:
   - shooting_star: Strict rules as above - no upper/lower shadow for entry/exit
   - variation1: Strict rules as above but shorter lower shadow than upper shadow for entry
   - variation2: Shorter upper shadow than lower shadow for exit
   - **variation3: variation1 + variation2: Shorter lower shadow than upper shadow for entry and shorter upper shadow than lower shadow for exit**
   - variation4: variation3 + Entry candle does not have to be green and exit candle does not have to be red
   - variation5: Entry candle has to be green and exit candle does not have to be red
   - variation6: Entry candle does not have to be green and exit candle has to be red  
   - variation7: variation1 + MA8 > MA13 for entry
   - variation8: variation1 + MA8 < MA13 for exit
   - variation9: variation1 + MA8 > MA13 for entry and MA8 < MA13 for exit
   - variation10: Daily 20MA of day-1 must be higher than that of day-2
   - variation11: Median Bid-Ask spread of previous timestep has to be < \$100
   - variation12: variation10 + variation11
   
Results:
   - shooting_star: 3209.69
   - variation1: 2405.35
   - variation2: 2506.29
   - variation3: 4522.15
   - variation4: 40.42
   - variation5: 2776.23
   - variation6: 2773.66
   - variation7: 2624.63
   - variation8: 
   - variation9: 2361.02
   - variation10: 2397.81
   - variation11: 3209.69
   - variation12: 2397.81
    
Files:
   - .py - backtesting scripts
   - .csv - backtest outputs
   - .png - backtest stats
    
Folders:
   - diff_market_diff_time_testing - Testing shooting_star on different markets at different bar lengths. market_check.ods summarises results.
   - shadow_length_effect - Test different values of shadow_length to see effect. Reslts in results.csv. TLDR: Longer shadow = less trades, higher win% and avg return, lower overall profit.