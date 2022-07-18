import os,time,json
try:
    import ccxt
except:
    os.system("pip install ccxt")
try:
    import ta
except:
    os.system("pip install ta")
try:
    import pandas as pd
except:
    os.system("pip install pandas")
try:
    import chime
except:
    os.system("pip install chime")
import numpy as np
from ta.trend import PSARIndicator
from ta.volatility import AverageTrueRange
import warnings
warnings.simplefilter(action='ignore', category=FutureWarning)

with open('config.json') as f:
    veri = json.load(f)

# API CONNECT
exchange = ccxt.binance({
"apiKey": veri["apiKey"],
"secret": veri["secretKey"],
'options': {
'defaultType': 'spot'
},
'enableRateLimit': True
})

symbol = "BTC/USDT"
balance = exchange.fetch_balance()
startingMoney = float(balance["total"]["USDT"])

longPosition = False
shortPosition = False
complatedTradeAmount = 0
win = 0
loss = 0
winRate = 0
tpPrice = 0
entryPrices = []
entryAmounts = []
exitPrices = []

while True:
    try:
        baslangic = time.time()
        balance = exchange.fetch_balance()

        totalMoney = float(balance["total"]["USDT"])
        with open('config.json') as f:
            veri = json.load(f)

        percentageOfTradeMoney = float(veri["percentageOfTradeMoney"])
        step = float(veri["step"])
        maxStep = float(veri["maxStep"])
        tpCarpan = float(veri["tpCarpan"])
        sounds = veri["sounds"].upper()
        takeProfit = veri["takeProfit"].upper()

        if sounds == "TRUE":
            sounds = True
        else:
            sounds = False

        if takeProfit == "TRUE":
            takeProfit = True
        else:
            takeProfit = False

        ###################################################################################################
        orderBook = exchange.fetch_order_book(symbol)
        # LOAD BARS
        bars = exchange.fetch_ohlcv(symbol, timeframe="1m", since = None, limit = 100)
        df = pd.DataFrame(bars, columns=["timestamp", "open", "high", "low", "close", "volume"])

        shortToplam = 0
        longToplam = 0
        if longPosition:
            currentPrice = orderBook["asks"][0][0]
        if longPosition == False:
            currentPrice = orderBook["bids"][0][0]

        ###################################################################################################
        pSar = PSARIndicator(df["high"], df["low"], df["close"], step, maxStep)
        df["psar"] = pSar.psar()
        df["pSar_Up"] = pSar.psar_up()
        df["pSar_Down"] = pSar.psar_down()

        df['pSar_Up'] = df["pSar_Up"].replace(np.nan, 0)
        df['pSar_Down'] = df["pSar_Down"].replace(np.nan, 0)

        if takeProfit:
            atr = AverageTrueRange(df["high"], df["low"], df["close"])
            df["atr"] = atr.average_true_range()
        ###################################################################################################

        # LONG ENTER
        def longEnter(alinacak_miktar):
            order = exchange.create_market_buy_order(symbol, alinacak_miktar)
            entryPrices.append(float(order["price"]))
            entryAmounts.append(float(order["amount"]))
            if sounds:
                chime.success()


        # LONG EXIT
        def longExit():
            order = exchange.create_market_sell_order(symbol, float(balance["total"]["BTC"]))
            exitPrices.append(float(order["price"]))
            if sounds:
                chime.success()
            if float(order["fee"]["cost"])>0:
                exit()

        # LONG ENTER
        if longPosition == False and df['pSar_Up'][len(df.index) - 1] > 0 and df['pSar_Down'][len(df.index) - 2] > 0:
            qty = ((totalMoney / 100) *  percentageOfTradeMoney) / currentPrice
            longEnter(qty)
            entryPrice = float(entryPrices[len(entryPrices)-1])
            amount = float(entryAmounts[len(entryAmounts)-1])
            longPosition = True
            print("LONG ENTER")

        # LONG EXIT
        if longPosition and df['pSar_Down'][len(df.index) - 1] > 0 and df['pSar_Up'][len(df.index) - 2] > 0:
            longExit()
            print("LONG EXIT")
            longPosition = False
            exitPrice = float(exitPrices[len(exitPrices)-1])
            if exitPrice > entryPrice:
                win = win + 1
            else: loss = loss + 1
            complatedTradeAmount = complatedTradeAmount + 1
            winRate = (win / complatedTradeAmount) * 100

        # TAKE PROFIT
        if takeProfit:
            if longPosition:
                tpPrice = entryPrice + (df["atr"][len(df.index) - 2] * tpCarpan)
                if currentPrice >= tpPrice:
                    longExit()
                    print("LONG EXIT (TAKE PROFIT)")
                    longPosition = False
                    exitPrice = float(exitPrices[len(exitPrices)-1])
                    if exitPrice > entryPrice:
                        win = win + 1
                    else: loss = loss + 1
                    complatedTradeAmount = complatedTradeAmount + 1
                    winRate = (win / complatedTradeAmount) * 100

        os.system("cls")
        print("Total USDT:", round(totalMoney, 4))
        print("Total BTC:", float(balance["total"]["BTC"]))
        if longPosition:
            roe = round(((currentPrice - entryPrice) / entryPrice) * 100, 4)
            print("Long Pozisyonda. Roe: %"+str(roe))
        else:
            print("Total Profit:", round(float(balance["total"]["USDT"]) - startingMoney, 4), "USDT || %" + str(round(( (float(balance["total"]["USDT"]) - startingMoney) /  startingMoney) * 100, 4)))
        print("Trade Amount:",complatedTradeAmount, "|| Win:", win, "|| Loss:", loss, "|| WinRate: %"+str(round(winRate, 2)))
        son = time.time()
        print("Delay:", round(son-baslangic, 2), "seconds")

    except ccxt.BaseError as Error:
        print ("[ERROR] ", Error )
        continue
