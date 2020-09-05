import requests
import json
import numpy as np
import pandas as pd
import time
import datetime
import talib
import oandapyV20
from oandapyV20.contrib.requests import MarketOrderRequest
from oandapyV20.contrib.requests import TakeProfitDetails, StopLossDetails
import oandapyV20.endpoints.orders as orders
import oandapyV20.endpoints.positions as positions
import oandapyV20.endpoints.pricing as pricing
from oandapyV20 import API
import oandapyV20.endpoints.instruments as instruments

ACCESS_TOKEN = "YOUR OANDA API TOKEN"
ACCOUNT_ID = "YOUR ACCOUNT ID"

api = oandapyV20.API(access_token=ACCESS_TOKEN)

close_prices = []
open_prices = []
low_prices = []
high_prices = []
volume_numbers = []
list_of_time = []
candleopen = []
candleclose = []
candlehigh = []
candlelow = []
candlevolume = []

list_shortsl = []
list_longsl = []

long_wait_10 = []
short_wait_10 = []
quantity = 100
long_regulation_trade = [quantity, quantity + 25, quantity + 100]
long_regulation_number = 0
short_regulation_trade = [quantity, quantity + 25, quantity + 100]
short_regulation_number = 0

totalprofit = 0
totalloss = 0
#Candlestick data
params = {
    "count": 2000,
    "granularity": "M2"
    }
instrum = instruments.InstrumentsCandles(instrument="GBP_USD", params=params)
json_response = api.request(instrum)
longed = 0
shorted = 0

shortbasis = 0
longbasis = 0
shortexit = 0
longexit = 0


for candlenum in range(len(json_response["candles"])):

    openprice = float(json_response["candles"][candlenum]['mid']['o'])
    closeprice = float(json_response["candles"][candlenum]['mid']['c'])
    highprice = float(json_response["candles"][candlenum]['mid']['h'])
    lowprice = float(json_response["candles"][candlenum]['mid']['l'])
    volume = float(json_response["candles"][candlenum]['volume'])

    timestamped = (json_response["candles"][candlenum]['time'])

    if timestamped not in list_of_time:
        list_of_time.append(timestamped)

        if len(candleopen) >= 1:
            close_prices.append(candleclose[-1])
            open_prices.append(candleopen[-1])
            low_prices.append(candlelow[-1])
            high_prices.append(candlehigh[-1])
            volume_numbers.append(candlevolume[-1])
            #reset candles
            candleopen = []
            candleclose = []
            candlehigh = []
            candlelow = []
            candlevolume = []

            
            if len(close_prices) > 7:

                bidprice = closeprice * 0.999935
                askprice = closeprice * 1.000065


                numclose = np.array(close_prices)
                numopen = np.array(open_prices)
                numlow = np.array(low_prices)
                numhigh = np.array(high_prices)
                numvolume = np.array(volume_numbers)

                rsii = talib.RSI(numclose, 7)
                mfi = talib.MFI(numhigh, numlow, numclose, numvolume, 7)
                atr = talib.ATR(numhigh, numlow, numclose, 7)
                print("EUR_USD: The current MFI is {}.".format(mfi[-1]))
                print("EUR_USD: The current RSI is {}.".format(rsii[-1]))
                print("EUR_USD: The current ATR is {}.".format(atr[-1]))
                print("Timestamp: {}".format(timestamped))



                if shorted <= 2600:
                    if rsii[-1] >= 80 and rsii[-2] >= 80 and rsii[-3] >= 80 and atr[-1] <= 0.00045:

                        print('Short order for {} units created at {}'.format(1300, bidprice))
                        print("Time is {}".format(list_of_time[-1]))
                        print("---------")
                        shorted += 1300
                        shortbasis += bidprice * 1300

                if longed <= 2600:
                    if rsii[-1] <= 20 and rsii[-2] <= 20 and rsii[-3] <= 20 and atr[-1] <= 0.00045:

                        print('Long for {} units created at {}'.format(1300, askprice))
                        print("Time is {}".format(list_of_time[-1]))
                        print("---------")
                        longed += 1300
                        longbasis += askprice * 1300
            
                
                if shorted > 0:
                    if mfi[-1] <= 10:

                        
                        print('Cover short for {} units created at {}'.format(shorted, askprice))
                        print("Time is {}".format(list_of_time[-1]))
                        print("---------")
                        shortexit += askprice * shorted
                        shorted = 0

                if longed > 0:
                    if mfi[-1] >= 90:
                        print('Selling off {} long units created at {}'.format(longed, bidprice))
                        print("Time is {}".format(list_of_time[-1]))
                        print("---------")
                        longexit += bidprice * longed
                        longed = 0
        else:
            candleopen.append(openprice)
            candleclose.append(closeprice)
            candlelow.append(lowprice)
            candlehigh.append(highprice)
            candlevolume.append(volume)
shortexit += askprice * shorted
longexit += bidprice * longed
print('***************')
print("The short basis is {}".format(shortbasis))
print("The short exit is {}".format(shortexit))
print("Short profit is {}".format(float(shortbasis - shortexit)))
print("----------------------------")
print("The long basis is {}".format(longbasis))
print("The long exit is {}".format(longexit))
print("Long profit is {}".format(float(longexit - longbasis)))
print("---")
print("Total profit is {}".format((float(longexit - longbasis) + float(shortbasis - shortexit))))