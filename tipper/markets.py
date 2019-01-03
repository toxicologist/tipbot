import requests
import threading


class Market:
    def __init__(self, site='', ticker='', interval=0, enabled=True):
        if enabled:
            site = site.lower()

            self.error = False
            self.ticker = ticker
            self.site = site
            self.interval = float(interval)

            if site == 'cryptopia':
                self.url = 'https://www.cryptopia.co.nz/api/GetMarket/%s_BTC' % ticker
            elif site == 'tradesatoshi':
                self.url = 'https://tradesatoshi.com/api/public/getticker?market=%s_BTC' % ticker
            elif site == 'yobit':
                self.url = 'https://yobit.net/api/3/ticker/%s_btc' % ticker
            elif site == 'coinexchange':
                self.url = 'https://www.coinexchange.io/api/v1/getcurrency?ticker_code=%s' % ticker
            elif site == 'cryptohub':
                self.url = 'https://cryptohub.online/api/market/ticker/%s' % ticker
            else:
                self.error = True
                    
            self.update_prices()
        else:
            self.price_btc = 0.00000001
            self.btc_price = 7000
            self.error = False

    def update_prices(self):
        threading.Timer(self.interval, self.update_prices).start()
        print("Updating prices")
        self.get_bitcoin_price()
        self.get_exchange_price()

    def get_bitcoin_price(self):
        r = requests.get('https://api.coindesk.com/v1/bpi/currentprice.json')
        r = r.json()
        self.btc_price = float(r['bpi']['USD']['rate_float'])
        print(self.btc_price)

    def get_exchange_price(self):
        r = requests.get(self.url)
        r = r.json()
        if self.site == "cryptopia":
            price = r['Data']['LastPrice']
        elif self.site == "tradesatoshi":
            price = r['result']['last']
        elif self.site == "yobit":
            price = r['%s_btc' % self.ticker]['last']
        elif self.site == "coinexchange":
            mid = r['result']['CurrencyID']
            r = requests.get('https://www.coinexchange.io/api/v1/getmarketsummary?market_id=%s' % mid)
            r = r.json()
            price = r['result']['LastPrice']
        elif self.site == "cryptohub":
            price = r['BTC_%s' % self.ticker.upper()]['last']
        else:
            print("Error, market not configured correctly!")
        self.price_btc = float(price)
        print(self.price_btc)

    def get_price(self, amount=1):  # returns [price_btc, price_usd]
        if self.error:
            return "Error, market not configured correctly!"

        price_usd = self.price_btc * self.btc_price

        return [float("%.8f" % (self.price_btc * amount)), price_usd * amount]
