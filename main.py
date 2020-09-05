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
from multiprocessing import Process


def EURTRADE():
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

    quantity = 7500
    long_regulation_trade = [quantity, quantity + 500, quantity + 1000, quantity + 2000, quantity + 4000]
    long_regulation_number = 0
    short_regulation_trade = [quantity, quantity + 500, quantity + 1000, quantity + 2000, quantity + 4000]
    short_regulation_number = 0
    while True:
        params = {
            "count": 7,
            "granularity": "M2"
            }

        instrum = instruments.InstrumentsCandles(instrument="EUR_USD", params=params)
        json_response = api.request(instrum)
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
                        #Pricing info- bid and ask
                        query = {"instruments": "EUR_USD"}
                        pricingrequest = pricing.PricingInfo(accountID=ACCOUNT_ID, params=query)
                        recievedrequest = api.request(pricingrequest)
                        bidprice = pricingrequest.response['prices'][0]['bids'][0]['price']
                        askprice = pricingrequest.response['prices'][0]['asks'][0]['price']

                        shorttp = round(float(bidprice) * 1.0058, 6)
                        shortsl = round(float(askprice) * 0.9988, 6)
                        longtp = round(float(bidprice) * 0.9942, 6)
                        longsl = round(float(askprice) * 1.0012, 6)

                        #Account info- open positions
                        account_details = positions.OpenPositions(accountID=ACCOUNT_ID)
                        api.request(account_details)

                        #Market order creation- short position
                        shortmktOrder = MarketOrderRequest(
                            instrument="EUR_USD",
                            units= - (short_regulation_trade[short_regulation_number]),
                            takeProfitOnFill=TakeProfitDetails(price=shorttp).data,
                            stopLossOnFill=StopLossDetails(price=shortsl).data)
                        shortordercreation = orders.OrderCreate(ACCOUNT_ID, data=shortmktOrder.data)

                        #Market order creation- long position
                        longmktOrder = MarketOrderRequest(
                            instrument="EUR_USD",
                            units= (long_regulation_trade[long_regulation_number]),
                            takeProfitOnFill=TakeProfitDetails(price=longtp).data,
                            stopLossOnFill=StopLossDetails(price=longsl).data)
                        longordercreation = orders.OrderCreate(ACCOUNT_ID, data=longmktOrder.data)

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
                        print("------------------------------------------------------------------------------------------------------------------------")
                        if float(bidprice) / float(askprice) >= 0.99984:
                            if short_regulation_number == 6:
                                pass
                            else:
                                if rsii[-1] >= 80 and rsii[-2] >= 80 and rsii[-3] >= 80:

                                    list_shortsl.append(shortsl)
                                    try:
                                        # create the OrderCreate request
                                        rv = api.request(shortordercreation)
                                    except oandapyV20.exceptions.V20Error as err:
                                        print(shortordercreation.status_code, err)
                                    else:
                                        print('EUR_USD: Short order for {} units created at {}'.format(short_regulation_trade[short_regulation_number], askprice))
                                        short_regulation_number += 1

                            if long_regulation_number == 6:
                                pass
                            else:
                                if rsii[-1] <= 20 and rsii[-2] <= 20 and rsii[-3] <= 20:

                                    list_longsl.append(longsl)
                                    try:
                                        # create the OrderCreate request
                                        rv = api.request(longordercreation)
                                    except oandapyV20.exceptions.V20Error as err:
                                        print(longordercreation.status_code, err)
                                    else:
                                        print('EUR_USD: Long for {} units created at {}'.format(long_regulation_trade[long_regulation_number], bidprice))
                                        long_regulation_number += 1
                            
                        else:
                            print("Bid/ask too wide for entry.")
                        
                            if mfi[-1] <= 5:
                                for i in range(len(account_details.response['positions'])):
                                    try:
                                        if account_details.response['positions'][i]['instrument'] == 'EUR_USD':
                                            if float(account_details.response['positions'][i]['short']['units']) < 0:
                                                units_available = int(account_details.response['positions'][i]['short']['units'])

                                                mktOrder = MarketOrderRequest(
                                                    instrument="EUR_USD",
                                                    units = -(units_available),
                                                    )
                                                r = orders.OrderCreate(ACCOUNT_ID, data=longmktOrder.data)
                                                try:
                                                    # create the OrderCreate request
                                                    rv = api.request(r)
                                                except oandapyV20.exceptions.V20Error as err:
                                                    print(r.status_code, err)
                                                else:
                                                    print('EUR_USD: Cover short for {} units created at {}'.format(units_available, askprice))
                                                    short_regulation_number = 0
                                    except IndexError:
                                        pass
                                    except KeyError:
                                        pass

                            if mfi[-1] >= 95:
                                for i in range(len(account_details.response['positions'])):
                                    try:
                                        if account_details.response['positions'][i]['instrument'] == 'EUR_USD':
                                            if float(account_details.response['positions'][i]['long']['units']) > 0:
                                                units_available = int(account_details.response['positions'][i]['long']['units'])

                                                mktOrder = MarketOrderRequest(
                                                    instrument="EUR_USD",
                                                    units= -(units_available),
                                                    )
                                                r = orders.OrderCreate(ACCOUNT_ID, data=mktOrder.data)
                                                try:
                                                    # create the OrderCreate request
                                                    rv = api.request(r)
                                                except oandapyV20.exceptions.V20Error as err:
                                                    print(r.status_code, err)
                                                else:
                                                    print('EUR_USD: Selling off {} long units created at {}'.format(units_available, bidprice))
                                                    long_regulation_number = 0
                                    except IndexError:
                                        pass
                                    except KeyError:
                                        pass
                            
            else:
                candleopen.append(openprice)
                candleclose.append(closeprice)
                candlelow.append(lowprice)
                candlehigh.append(highprice)
                candlevolume.append(volume)




def CAD():
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

    quantity = 7500
    long_regulation_trade = [quantity, quantity + 500, quantity + 1000, quantity + 2000, quantity + 4000]
    long_regulation_number = 0
    short_regulation_trade = [quantity, quantity + 500, quantity + 1000, quantity + 2000, quantity + 4000]
    short_regulation_number = 0
    while True:
        params = {
            "count": 7,
            "granularity": "M2"
            }
        
        instrum = instruments.InstrumentsCandles(instrument="USD_CAD", params=params)
        json_response = api.request(instrum)
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
                        #Pricing info- bid and ask
                        query = {"instruments": "USD_CAD"}
                        pricingrequest = pricing.PricingInfo(accountID=ACCOUNT_ID, params=query)
                        recievedrequest = api.request(pricingrequest)
                        bidprice = pricingrequest.response['prices'][0]['bids'][0]['price']
                        askprice = pricingrequest.response['prices'][0]['asks'][0]['price']

                        shorttp = round(float(bidprice) * 1.0058, 6)
                        shortsl = round(float(askprice) * 0.9988, 6)
                        longtp = round(float(bidprice) * 0.9942, 6)
                        longsl = round(float(askprice) * 1.0012, 6)

                        #Account info- open positions
                        account_details = positions.OpenPositions(accountID=ACCOUNT_ID)
                        api.request(account_details)

                        #Market order creation- short position
                        shortmktOrder = MarketOrderRequest(
                            instrument="USD_CAD",
                            units= - (short_regulation_trade[short_regulation_number]),
                            takeProfitOnFill=TakeProfitDetails(price=shorttp).data,
                            stopLossOnFill=StopLossDetails(price=shortsl).data)
                        shortordercreation = orders.OrderCreate(ACCOUNT_ID, data=shortmktOrder.data)

                        #Market order creation- long position
                        longmktOrder = MarketOrderRequest(
                            instrument="USD_CAD",
                            units= (long_regulation_trade[long_regulation_number]),
                            takeProfitOnFill=TakeProfitDetails(price=longtp).data,
                            stopLossOnFill=StopLossDetails(price=longsl).data)
                        longordercreation = orders.OrderCreate(ACCOUNT_ID, data=longmktOrder.data)

                        numclose = np.array(close_prices)
                        numopen = np.array(open_prices)
                        numlow = np.array(low_prices)
                        numhigh = np.array(high_prices)
                        numvolume = np.array(volume_numbers)

                        rsii = talib.RSI(numclose, 7)
                        mfi = talib.MFI(numhigh, numlow, numclose, numvolume, 7)
                        atr = talib.ATR(numhigh, numlow, numclose, 7)

                        print("USD_CAD: The current MFI is {}.".format(mfi[-1]))
                        print("USD_CAD: The current RSI is {}.".format(rsii[-1]))
                        print("USD_CAD: The current ATR is {}.".format(atr[-1]))
                        print("------------------------------------------------------------------------------------------------------------------------")
                        if float(bidprice) / float(askprice) >= 0.99985:
                            if short_regulation_number == 6:
                                pass
                            else:
                                if rsii[-1] >= 75 and rsii[-2] >= 75 and rsii[-3] >= 75 and atr[-1] <= 0.00035:

                                    list_shortsl.append(shortsl)
                                    try:
                                        # create the OrderCreate request
                                        rv = api.request(shortordercreation)
                                    except oandapyV20.exceptions.V20Error as err:
                                        print(shortordercreation.status_code, err)
                                    else:
                                        print('USD_CAD: Short order for {} units created at {}'.format(short_regulation_trade[short_regulation_number], askprice))
                                        short_regulation_number += 1

                            if long_regulation_number == 6:
                                pass
                            else:
                                if rsii[-1] <= 25 and rsii[-2] <= 25 and rsii[-3] <= 25 and atr[-1] <= 0.00035:

                                    list_longsl.append(longsl)
                                    try:
                                        # create the OrderCreate request
                                        rv = api.request(longordercreation)
                                    except oandapyV20.exceptions.V20Error as err:
                                        print(longordercreation.status_code, err)
                                    else:
                                        print('USD_CAD: Long for {} units created at {}'.format(long_regulation_trade[long_regulation_number], bidprice))
                                        long_regulation_number += 1
                            
                        else:
                            print("Bid/ask too wide for entry.")
                        
                            if mfi[-1] <= 10:
                                for i in range(len(account_details.response['positions'])):
                                    try:
                                        if account_details.response['positions'][i]['instrument'] == 'USD_CAD':
                                            if float(account_details.response['positions'][i]['short']['units']) < 0:
                                                units_available = int(account_details.response['positions'][i]['short']['units'])

                                                mktOrder = MarketOrderRequest(
                                                    instrument="USD_CAD",
                                                    units = -(units_available),
                                                    )
                                                r = orders.OrderCreate(ACCOUNT_ID, data=longmktOrder.data)
                                                try:
                                                    # create the OrderCreate request
                                                    rv = api.request(r)
                                                except oandapyV20.exceptions.V20Error as err:
                                                    print(r.status_code, err)
                                                else:
                                                    print('USD_CAD: Cover short for {} units created at {}'.format(units_available, askprice))
                                                    short_regulation_number = 0
                                    except IndexError:
                                        pass
                                    except KeyError:
                                        pass

                            if mfi[-1] >= 90:
                                for i in range(len(account_details.response['positions'])):
                                    try:
                                        if account_details.response['positions'][i]['instrument'] == 'USD_CAD':
                                            if float(account_details.response['positions'][i]['long']['units']) > 0:
                                                units_available = int(account_details.response['positions'][i]['long']['units'])

                                                mktOrder = MarketOrderRequest(
                                                    instrument="USD_CAD",
                                                    units= -(units_available),
                                                    )
                                                r = orders.OrderCreate(ACCOUNT_ID, data=mktOrder.data)
                                                try:
                                                    # create the OrderCreate request
                                                    rv = api.request(r)
                                                except oandapyV20.exceptions.V20Error as err:
                                                    print(r.status_code, err)
                                                else:
                                                    print('USD_CAD: Selling off {} long units created at {}'.format(units_available, bidprice))
                                                    long_regulation_number = 0
                                    except IndexError:
                                        pass
                                    except KeyError:
                                        pass
                            
            else:
                candleopen.append(openprice)
                candleclose.append(closeprice)
                candlelow.append(lowprice)
                candlehigh.append(highprice)
                candlevolume.append(volume)

if __name__=='__main__':
    p1 = Process(target = EURTRADE)
    p2 = Process(target = CAD)
    p1.start()
    p2.start()
    p1.join()
    p2.join()