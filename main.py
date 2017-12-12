import urllib.request
import json
import threading

class koinexTrader:
    ''' A simple algorithmic trader to trade cryptocurrency on koinex '''

    koinexTickerURL = "https://koinex.in/api/ticker"
    tickerData = {}

    def __init__(self):
        self.personalAssets = {
                'BTC': 0.01000024,
                'ETH': 0.00,
                'XRP': 0.00,
                'LTC': 0.00,
                'BCH': 0.00,
                'INR': 0.00
        }

    def getDataFromKoinexTicker(self):
        self.tickerData = json.loads(urllib.request.urlopen(self.koinexTickerURL, cafile='Cyberoam_SSL_CA.cert').read())

        for key in self.tickerData['prices'].keys():
            self.tickerData['prices'][key] = float(self.tickerData['prices'][key])

        for curr in self.tickerData['stats'].keys():
            for key in self.tickerData['stats'][curr].keys():
                self.tickerData['stats'][curr][key] = float(self.tickerData['stats'][curr][key])

    def updatePersonalAssets(self):
        pass

    def computeTotalValue(self, currency='INR'):
        totalValue = self.personalAssets['INR']

        for key in (self.personalAssets.keys() - ['INR']):
            totalValue += self.tickerData['prices'][key] * self.personalAssets[key]

        if currency != 'INR':
            totalValue /= self.tickerData['prices'][currency]
        return totalValue
    
    def automaticTrader(self):
        threading.Timer(1 * 60, self.automaticTrader).start()
        self.getDataFromKoinexTicker()
        print(self.computeTotalValue())

if __name__ == '__main__':
    trader = koinexTrader()
    trader.automaticTrader()
