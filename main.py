import urllib.request
import json
import threading
from pathlib import Path
import curses
import os
import time

certFile = 'Cyberoam_SSL_CA.cert'

class koinexTrader:
    ''' A simple algorithmic trader to trade cryptocurrency on koinex '''

    koinexTickerURL = "https://koinex.in/api/ticker"
    tickerData = {}

    def __init__(self):
        self.personalAssets = {
                'BTC': 0.01000024,
                'ETH': 0.00,
                'XRP': 0.00,
                'LTC': 0.41,
                'BCH': 0.00,
                'INR': 53.20
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

        self.stdscr = curses.initscr()
        curses.noecho()
        curses.cbreak()
        curses.curs_set(0)

    def getDataFromKoinexTicker(self):
        if (time.time() - self.lastUpdateTime) > self.updateInterval:

            try:
                if Path(certFile).is_file():
                    self.tickerData = json.loads(urllib.request.urlopen(self.koinexTickerURL, cafile='Cyberoam_SSL_CA.cert').read())
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
            return 1

        else:
            return 0

    def updatePersonalAssets(self):
        pass

    def computeBalances(self, currency='INR'):
        self.balances = {'TOT': 0.00}
        conversionFactor = 1

        if currency != 'INR':
            conversionFactor = 1.00/self.tickerData['prices'][currency]

        for key in self.personalAssets.keys():
            if key == 'INR':
                self.balances[key] = [self.personalAssets['INR'], self.personalAssets['INR'] * conversionFactor]
            else:
                self.balances[key] = [self.personalAssets[key], self.tickerData['prices'][key] * self.personalAssets[key] * conversionFactor]

            self.balances['TOT'] += self.balances[key][1]

        return self.balances
    
    def automaticTrader(self, currency):
        # SELL
        if self.balances['BTC'][0] > 0:
            if (self.tickerData['prices'][currency] >= self.tickerData['stats'][currency]['max_24hrs']) and \
                (((self.tickerData['prices'][currency] - self.lastTradePrice[currency])/self.tickerData['prices'][currency])*100 > 2):
                    with open('trade-log-2.txt', 'a') as logFile:
                        logFile.write("Sold {:15.8f} BTC at the rate of {:15.2f} per BTC.\n".format(self.balances['BTC'], self.tickerData['prices'][currency]))

                    self.balances['INR'] += self.tickerData['prices'][currency] * self.balances['BTC']
                    self.balances['BTC'] = 0.00

        # BUY
        if self.balances['INR'][0] > 0:
            if (self.tickerData['prices'][currency] <= self.tickerData['stats'][currency]['min_24hrs']*1.1) and \
                (((self.lastTradePrice[currency] - self.tickerData['prices'][currency])/self.lastTradePrice[currency])*100 > 2):
                    self.balances['BTC'] += (self.balances['INR'] - self.balances['INR']*0.0025) / self.tickerData['prices'][currency]
                    self.balances['INR'] = 0.00
                    
                    with open('trade-log-2.txt', 'a') as logFile:
                        logFile.write("Bought {:15.8f} BTC at the rate of {:15.2f} per BTC.\n".format(self.balances['BTC'], self.tickerData['prices'][currency]))

    def autoTrade(self, updateInterval=30):
        self.updateInterval = updateInterval

        while self.getDataFromKoinexTicker() != 1:
            sleep(1)

        self.lastTradePrice = self.tickerData['prices']

        while True:
            if self.getDataFromKoinexTicker() == -1:
                self.stdscr.addstr(13, 0, "{:<50}".format("Ticker not working. Retrying ..."))
            else:
                self.stdscr.addstr(13, 0, "{:<50}".format("Ticker Updated Successfully."))
                self.computeBalances('INR')
                self.automaticTrader('BTC')

            self.printBalances('INR')
            time.sleep(1)

    def printBalances(self, currency):
        self.stdscr.addstr(0, 0, '{:>6} |{:>15} |{:>15}'.format('CUR', 'Native', currency))
        self.stdscr.addstr(1, 0, '{:->40}'.format(''))
        
        for index, key in enumerate(['BTC', 'LTC', 'ETH', 'XRP', 'BCH', 'INR']):
            self.stdscr.addstr(index + 2, 0, '{:>6} |{:15.8f} |{:15.8f}'.format(key, self.balances[key][0], self.balances[key][1]))

        self.stdscr.addstr(8, 0, '{:->40}'.format(''))
        self.stdscr.addstr(9, 0, '{:>6} |{:>15} |{:>15.8f}'.format('Total', '', self.balances['TOT']))
        self.stdscr.addstr(11, 0, 'Reupdating balances in %d seconds ...' % (self.updateInterval - (time.time() - self.lastUpdateTime)))
        self.stdscr.refresh()

if __name__ == '__main__':
    try:
        trader = koinexTrader()
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
