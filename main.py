import urllib.request
import json
import threading
from pathlib import Path
import curses
import os
import time
import matplotlib.pyplot as plt

certFile = 'Cyberoam_SSL_CA.cert'

class koinexTrader:
    ''' A simple algorithmic trader to trade cryptocurrency on koinex '''

    koinexTickerURL = "https://koinex.in/api/ticker"
    tickerData = {}
    priceHistory = {
        'timestamp': [],
        'BTC': [],
        'ETH': [],
        'XRP': [],
        'LTC': [],
        'BCH': [],
        'MIOTA': [],
        'GNT': [],
        'OMG': []
    }

    def __init__(self):
        self.personalAssets = {
                'BTC': 0.01000024,
                'ETH': 0.00,
                'XRP': 110.00,
                'LTC': 0.41,
                'BCH': 0.00,
                'INR': 90.82
        }

        self.lastTradePrice = {
                'BTC': 0.00,
                'ETH': 0.00,
                'XRP': 0.00,
                'LTC': 0.00,
                'BCH': 0.00,
        }

        self.balances = {}
        self.lastUpdateTime = 0
        self.updateInterval = 30
        self.plotting = False
        self.plotData = False
        self.fig = False
        self.ax = False

        self.stdscr = curses.initscr()
        curses.noecho()
        curses.cbreak()
        curses.curs_set(0)

    def getDataFromKoinexTicker(self):
        if (time.time() - self.lastUpdateTime) > self.updateInterval:

            try:
                if Path(certFile).is_file():
                    self.tickerData = json.loads(urllib.request.urlopen(self.koinexTickerURL, cafile=certFile).read())
                else:
                    self.tickerData = json.loads(urllib.request.urlopen(self.koinexTickerURL).read())
            except urllib.error.HTTPError:
                return -1

            for key in self.tickerData['prices'].keys():
                self.tickerData['prices'][key] = float(self.tickerData['prices'][key])

            for curr in self.tickerData['stats'].keys():
                for key in self.tickerData['stats'][curr].keys():
                    self.tickerData['stats'][curr][key] = float(self.tickerData['stats'][curr][key])

            self.lastUpdateTime = time.time()
            self.recordHistory()
            if self.plotting != False:
                #self.refreshPlot()
                pass

            return 1

        else:
            return 0

    def recordHistory(self):
        self.priceHistory['timestamp'].append(self.lastUpdateTime)

        for key in self.tickerData['prices']:
            self.priceHistory[key].append(self.tickerData['prices'][key])

    def updatePersonalAssets(self):
        pass

    def automaticTrader(self, currency):
        # SELL
        if self.personalAssets['BTC'] > 0:
            if (self.tickerData['prices'][currency] >= self.tickerData['stats'][currency]['max_24hrs']) and \
                (((self.tickerData['prices'][currency] - self.lastTradePrice[currency])/self.tickerData['prices'][currency])*100 > 2):
                    with open('trade-log-2.txt', 'a') as logFile:
                        logFile.write("Sold {:15.8f} BTC at the rate of {:15.2f} per BTC.\n".format(self.balances['BTC'], self.tickerData['prices'][currency]))

                    self.balances['INR'] += self.tickerData['prices'][currency] * self.balances['BTC']
                    self.balances['BTC'] = 0.00

        # BUY
        if self.personalAssets['INR'] > 0:
            if (self.tickerData['prices'][currency] <= self.tickerData['stats'][currency]['min_24hrs']*1.1) and \
                (((self.lastTradePrice[currency] - self.tickerData['prices'][currency])/self.lastTradePrice[currency])*100 > 2):
                    self.balances['BTC'] += (self.balances['INR'] - self.balances['INR']*0.0025) / self.tickerData['prices'][currency]
                    self.balances['INR'] = 0.00
                    
                    with open('trade-log-2.txt', 'a') as logFile:
                        logFile.write("Bought {:15.8f} BTC at the rate of {:15.2f} per BTC.\n".format(self.balances['BTC'], self.tickerData['prices'][currency]))

    def autoTrade(self, updateInterval=30):
        self.updateInterval = updateInterval

        while self.getDataFromKoinexTicker() != 1:
            time.sleep(1)

        self.lastTradePrice = self.tickerData['prices']

        while True:
            if self.getDataFromKoinexTicker() == -1:
                self.stdscr.addstr(13, 0, "{:<50}".format("Ticker not working. Retrying ..."))
            else:
                self.stdscr.addstr(13, 0, "{:<50}".format("Ticker Updated Successfully."))
                self.automaticTrader('BTC')

            self.printBalances('INR')
            time.sleep(1)

    def printBalances(self, currency='INR'):
        totalBalance = 0
        conversionFactor = 1
        if currency != 'INR':
            conversionFactor = 1.00/self.tickerData['prices'][currency]

        self.stdscr.addstr(0, 0, '{:>6} |{:>15} |{:>15} |{:>15}'.format('CUR', 'Balance', 'Rate', currency))
        self.stdscr.addstr(1, 0, '{:->57}'.format(''))
        
        for index, key in enumerate(['BTC', 'LTC', 'ETH', 'XRP', 'BCH', 'INR']):
            rate = (1 if (key=='INR') else self.tickerData['prices'][key]) * conversionFactor
            balance = self.personalAssets[key] * rate
            totalBalance += balance
            self.stdscr.addstr(index + 2, 0, '{:>6} |{:15.8f} |{:15.2f} |{:15.5f}'.format(key, self.personalAssets[key], rate, balance))

        self.stdscr.addstr(8, 0, '{:->57}'.format(''))
        self.stdscr.addstr(9, 0, '{:>6} |{:>15} |{:>15} |{:>15.5f}'.format('Total', '', '', totalBalance))
        self.stdscr.addstr(11, 0, 'Reupdating balances in %d seconds ...' % (self.updateInterval - (time.time() - self.lastUpdateTime)))
        self.stdscr.refresh()

    def initPlot(self, currency):
        self.plotting = currency
        self.fig = plt.figure()
        self.ax = self.fig.add_subplot(111)
        #self.plotData, = self.ax.plot(self.priceHistory['timestamp'], self.priceHistory[currency])
        self.plotData, = self.ax.plot([1,2,3],[1,2,3])
        self.fig.canvas.draw()
        plt.show(block=False)

    def refreshPlot(self):
        self.plotData.set_xdata(self.priceHistory['timestamp'])
        self.plotData.set_ydata(self.priceHistory[self.plotting])

        self.ax.relim()
        self.ax.autoscale_view(True, True, True)

        self.fig.canvas.draw()

if __name__ == '__main__':
    try:
        trader = koinexTrader()
        trader.initPlot('BTC')
        trader.autoTrade(30)

        while True:
            time.sleep(100)

    except KeyboardInterrupt:
        os.system('stty sane')
        os.system('clear')
        exit(0)

    except:
        os.system('stty sane')
        os.system('clear')
        raise
