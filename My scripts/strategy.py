############################################################################
#
#   This strategy is running @aws
#
#
############################################################################

import pandas as pd
import numpy as np
from time import sleep
import datetime
import talib
import indicators
import Zerodha_login as kite_app
import sys
import time

kite = kite_app.kite

print('Available Margin', kite.margins()['equity']['net'])

# Just to confirm kite has been connected or not
print('ITC current price', kite.ltp(['NSE:ITC']))


watchlist = ['BANKNIFTY2211337500CE', 'BANKNIFTY2211337500PE']

quantity_check = {'B': 25,
                 'N': 50
                 }

def get_data(delta, name, exchange, interval, continuous, oi):
    to_date = datetime.datetime.now().date()
    from_date = to_date - datetime.timedelta(days = delta)
#     print(to_date, from_date)
    token = kite.ltp([exchange + name])[exchange + name]['instrument_token']
#     print(token)
    data = kite.historical_data(instrument_token=token, from_date=from_date, to_date=to_date, interval=interval, 
                               continuous=continuous, oi=oi)
    df_data = pd.DataFrame(data)
    return df_data

def exit_trades(buy_stocks):
    for name in buy_stocks:
        qnty = quantity_check[name[0]]
        try: 
            kite.place_order(variety = kite.VARIETY_REGULAR, exchange = kite.EXCHANGE_NFO, tradingsymbol = name, 
                             transaction_type = kite.TRANSACTION_TYPE_SELL, quantity = 1 * qnty, product = kite.PRODUCT_MIS, 
                             order_type = kite.ORDER_TYPE_MARKET, price=None, validity=None, disclosed_quantity=None, 
                             trigger_price=None, squareoff=None, stoploss=None, trailing_stoploss=None, tag=None)
            buy_stocks.remove(name)
        except Exception as e:
            print('Error while exiting: ', e)
    return len(buy_stocks)



buy_stocks = []  

now = datetime.datetime.now()
now = now + datetime.timedelta(hours = 5, minutes = 30)
now = now.strftime("%H:%M:%S")

while ( (now > "09:25:10") and (now < "15:20:00") ):
    now = datetime.datetime.now()
    now = now + datetime.timedelta(hours = 5, minutes = 30)
    now = now.strftime("%H:%M:%S")

    if now >= "15:18:00":
        print('Exiting all MIS positions')
        len_ = exit_trades(buy_stocks)
        if len_ == 0:
            watchlist = []
            # we are good to stop for today. 
            print('Trade finished for today. ')
            sys.exit('###########  Exiting now  ###########')
        
    for name in watchlist[:]:
        try:
#             print('Name: ', name)
            # get 1 minute and 5 minute data
            qnty = quantity_check[name[0]]
            df_min = get_data(delta=4, name = name, exchange='NFO:', interval='minute', continuous=False, oi= False)
            df = get_data(delta=4, name=name, exchange='NFO:', interval='5minute', continuous=False, oi= False)
            df_ten = get_data(delta=4, name=name, exchange='NFO:', interval='10minute', continuous=False, oi= False)
            
            # Logic - 8,20 EMA, RSI and ADX
#             print(df.head())
            indicators.SuperTrend(df = df, period=7, multiplier=3, ohlc=['open', 'high', 'low', 'close'])
            df['ema_small'] = talib.EMA(df['close'], timeperiod=8)
            df['ema_large'] = talib.EMA(df['close'], timeperiod=20)
            df['rsi'] = talib.RSI(df['close'], timeperiod=14)
            df['adx'] = talib.ADX(df['high'], df['low'], df['close'])
            df_min['rsi'] = talib.RSI(df_min['close'], timeperiod=14)
            df_ten['rsi'] = talib.RSI(df_ten['close'], timeperiod=14)
            
            last_minute_candle = df_min.iloc[-2]
            current_minute_candle = df_min.iloc[-1]
            last_candle = df.iloc[-2]
            current_candle = df.iloc[-1]
            last_ten_candle = df_ten.iloc[-2]
            current_ten_candle = df_ten.iloc[-1]
#             print('RSI: ', round(last_candle['rsi'], 2))
#             print('Last candle: ', last_candle)
#             print('Cuurnt candle: ', current_candle)
            
            ema_condition = ''
            # check ema cross-over status
            if (last_candle['ema_small'] > last_candle['ema_large']):
                ema_condition = 'golden_crossover'
            if (last_candle['ema_small'] < last_candle['ema_large']):
                ema_condition = 'death_crossover'
            
            rsi_buy_condition = False
            rsi_sell_condition = False
            if current_candle['rsi'] >= last_candle['rsi']:
                rsi_buy_condition = True
#                 if (current_candle['rsi'] > 55.0) :
#                     print('RSI buy condition satisfied', round(current_candle['rsi'], 2), name)
            if current_candle['rsi'] <= last_candle['rsi']:
                rsi_sell_condition = True
                    
            strong_bullish = True
            strong_bearish = True
#             x_name = 'NFO:'+name
#             ltp = kite.ltp([x_name])[x_name]['last_price']
#             if ltp >= last_candle['close']:
#                 strong_bullish = True
#             if ltp <= last_candle['close']:
#                 strong_bearish = True
                
            strong_adx = True
#             if current_candle['adx'] >= last_candle['adx']:
#                 strong_adx = True

            # Buy script - 1
            if( (now < "15:15:00") and (ema_condition == 'golden_crossover') and (last_candle['rsi'] > 60) and (last_candle['STX_7_3'] == 'up') and (last_candle['adx'] >= 15) and (current_candle['rsi'] > 60) and (last_minute_candle['rsi'] > 60.5) and (current_minute_candle['rsi'] > 60.5) ):
                if( (name not in buy_stocks) and (last_ten_candle['rsi'] > 55) and (current_ten_candle['rsi'] > 60) and (rsi_buy_condition) ):
                    try:
                        # Place fresh-buy order
                        order_id = kite.place_order(variety = kite.VARIETY_REGULAR, exchange = kite.EXCHANGE_NFO, tradingsymbol = name, 
                                                    transaction_type = kite.TRANSACTION_TYPE_BUY, quantity = 1 * qnty, product = kite.PRODUCT_MIS, 
                                                    order_type = kite.ORDER_TYPE_MARKET, price=None, validity=None, disclosed_quantity=None, 
                                                    trigger_price=None, squareoff=None, stoploss=None, trailing_stoploss=None, tag=None)
                        time.sleep(1)
                        id_history = kite.order_history(order_id)[-1]['status']
                        if id_history == 'COMPLETE':
                            buy_stocks.append(name)
                            print('##### Buy: #####', name)
                            print('Time: ', now)
                            print('5 min last candle RSI: ', round(last_candle['rsi'], 2))
                            print('ADX: ', round(last_candle['adx'], 2))
                            print('10 min last candle RSI: ', round(last_ten_candle['rsi'], 2))
                            print('10 min current candle RSI: ', round(current_ten_candle['rsi'], 2))
                            #if strong_bullish:
                                #print('Strong bullish')
                            if rsi_buy_condition:
                                print('RSI buy condition')
                            #if strong_adx:
                                #print('Strong adx with value', round(current_candle['adx'], 2))
                    
                    except Exception as e:
                        print('Buy order placement failed for ', name)
                        print('Error: ', e)
#                         continue
            ### End of Buy script - 1 ###

                        
            # Sell script - For Buy order - 1.1
#             print('Current bought stocks: ', buy_stocks)
            for name in buy_stocks:
                # Load data again for this stock
                qnty = quantity_check[name[0]]
                df_min2 = get_data(delta=4, name = name, exchange='NFO:', interval='minute', continuous=False, oi= False)
                df2 = get_data(delta=4, name=name, exchange='NFO:', interval='5minute', continuous=False, oi= False)
                
                df2['rsi'] = talib.RSI(df2['close'], timeperiod=14)
                indicators.SuperTrend(df = df2, period=7, multiplier=3, ohlc=['open', 'high', 'low', 'close'])
                df_min2['rsi'] = talib.RSI(df_min2['close'], timeperiod=14)
                df_min2['rsi_7'] = talib.RSI(df_min2['close'], timeperiod=7)  # extra security added
                
                current_minute_candle2 = df_min2.iloc[-1]
                last_minute_candle2 = df_min2.iloc[-2]
                last_candle2 = df2.iloc[-2]
                #current_candle2 = df2.iloc[-1]
                
                rsi_exit = False
                if ( (current_minute_candle2['rsi'] < 55) or (last_minute_candle2['rsi'] < 55) ):
                    rsi_exit = True
                    print('RSI going down for ', name, round(current_minute_candle2['rsi'], 2))
                rsi_7_exit = False
                if last_minute_candle2['rsi_7'] < 40:
                    rsi_7_exit = True
                    print('RSI 7 going below 40 for ', name, round(last_minute_candle2['rsi_7'], 2))

                # Check RSI
                if ( (now >= "15:18:00") or (rsi_exit) or (last_candle2['rsi'] <= 59) or (last_candle2['STX_7_3'] == 'down') ):
                    try:
                        # Place sell order
                        sell_order_id = kite.place_order(variety = kite.VARIETY_REGULAR, exchange = kite.EXCHANGE_NFO, tradingsymbol = name, 
                                                        transaction_type = kite.TRANSACTION_TYPE_SELL, quantity = 1*qnty, product = kite.PRODUCT_MIS, 
                                                        order_type = kite.ORDER_TYPE_MARKET, price=None, validity=None, disclosed_quantity=None, 
                                                        trigger_price=None, squareoff=None, stoploss=None, trailing_stoploss=None, tag=None)
                        buy_stocks.remove(name)
                        print('### Trade squareoff - sell: ###', name)
                        print('Time: ', now)
                        print('RSI of last 5 min candle: ', round(last_candle2['rsi'], 2))
                        if last_candle2['rsi'] <= 59:
                            print('RSI Weaker, last 5 min rsi value : ', round(last_candle2['rsi'], 2))
                        if last_candle2['STX_7_3'] == 'down':
                            print('ST down')
                        if rsi_exit:
                            print('Minute candle RSI weaker, value: ', round(current_minute_candle2['rsi'], 2))
                            print('Last minute candle RSI weaker, value: ', round(last_minute_candle2['rsi'], 2))
                        if (now >= "15:18:00"):
                            print('Enough for today')
                        
                    except Exception as e:
                        print('Sell order placement failed for ', name)
                        print('Error: ', e)
            
            ### End of sell script - 1.1 ###
            
                
        except Exception as e:
            print('Problem in current stock: ', name, now)
            print('Error: ', e)
            continue
            

