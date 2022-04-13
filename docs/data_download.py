key = # TODO: fill this in for Alpha Vantage

import requests
import pandas as pd
from io import StringIO
import time

# ==============================================================================
# Helper Functions
# ==============================================================================
def to_pandas(r):
    return pd.read_csv(StringIO(r.text))

def to_lists(r):
    return list(csv.reader(r.text.splitlines()))


class AV_api:
    url_head = 'https://www.alphavantage.co/query?'

    def __init__(self, key):
        self.key = key
        self.currency_physical = []
        self.currency_digital = []
        # TODO: load currency list

    def get_request(self, url):
        return requests.get(url + '&apikey=' + self.key)

    # ==================================================================================================================
    # Intraday Data
    # ==================================================================================================================
    def get_intraday(self, sym, interval=1):
        if interval not in [1, 5, 15, 30, 60]:
            print("Invalid interval value!")
            return None

        url = self.url_head + 'function=TIME_SERIES_INTRADAY'
        url = url + '&symbol={}&interval={}min&outputsize=full&datatype=csv'.format(sym, interval)
        return self.get_request(url)

    def get_intraday_ext(self, sym, slice_y=1, slice_m=1, interval=1):
        assert 0 <= slice_y <= 2
        assert 1 <= slice_m <= 12
        assert interval in [1, 5, 15, 30, 60]

        url = self.url_head + 'function=TIME_SERIES_INTRADAY_EXTENDED&'
        url = url + '&symbol={}&interval={}min&slice=year{}month{}'.format(sym, interval, slice_y, slice_m)
        url = url + '&outputsize=full&datatype=csv'
        return self.get_request(url)

    def get_daily(self, sym):
        url = self.url_head + 'function=TIME_SERIES_DAILY&symbol={}&outputsize=full&datatype=csv'.format(sym)
        return self.get_request(url)

    def get_weekly(self, sym, adjusted=True):
        func = 'TIME_SERIES_WEEKLY'
        if adjusted:
            func = func + '_ADJUSTED'

        url = self.url_head + 'function=' + func + '&symbol={}&outputsize=full&datatype=csv'.format(sym)
        return self.get_request(url)

    def get_monthly(self, sym, adjusted=True):
        func = 'TIME_SERIES_MONTHLY'
        if adjusted:
            func = func + '_ADJUSTED'

        url = self.url_head + 'function=' + func + '&symbol={}&outputsize=full&datatype=csv'.format(sym)
        return self.get_request(url)

    def get_quote(self, sym):
        url = self.url_head + 'function=GLOBAL_QUOTE&symbol={}&datatype=json'.format(sym)
        return self.get_request(url).json()

    def search(self, keyword):
        url = self.url_head + f'function=SYMBOL_SEARCH&keywords={keyword}&datatype=json'
        return self.get_request(url).json()

    # ==================================================================================================================
    # Fundamental Data
    # ==================================================================================================================

    def get_fundamental(self, sym, type):
        assert type in ['INCOME_STATEMENT', 'BALANCE_SHEET', 'CASH_FLOW', 'OVERVIEW']
        url = self.url_head + f'function={type}&symbol={sym}'
        return self.get_request(url).json()

    def get_earnings(self, horizon=3):
        url = self.url_head + f'function=EARNINGS_CALENDAR&horizon={horizon}month'

        with requests.Session() as s:
            download = s.get(url)
            decoded_content = download.content.decode('utf-8')
            cr = csv.reader(decoded_content.splitlines(), delimiter=',')
            my_list = list(cr)

            return my_list

    # ==========================================================================
    # FOREX
    # ==========================================================================

    def get_forex(self, curr_from, curr_to):
        if not curr_to in self.currency_physical and not curr_to in self.currency_digital:
            print("Target currency not found")
        if not curr_from in self.currency_physical and not curr_from in self.currency_digital:
            print("Source currency not found")

        url = self.url_head + f'function=CURRENCY_EXCHANGE_RATE&from_currency={curr_from}&to_currency={curr_to}'




# ==============================================================================
# Actual Process
# ==============================================================================
import finnhub
finnhub_client = finnhub.Client(api_key="c08t2p748v6u1t46dmng")

# S&P 500 and Nasdaq symbols
constit_sp500 = finnhub_client.indices_const(symbol = "^GSPC")
constit_nasdaq = finnhub_client.indices_const(symbol = "^NDX")

# Get symbols that constitutes the indices
indices = [
    '^NDX',
    '^DJI',
    '^SP500-50',
    '^SP500-25',
    '^SP500-30',
    '^GSPE',
    '^SP500-40',
    '^SP500-35',
    '^SP500-20',
    '^SP500-15',
    '^SP500-60',
    '^SP500-45',
    '^SP500-55'
    ]

constituent_map = {}
constituents = set()
for index in indices:
    res = finnhub_client.indices_const(symbol = index)['constituents']
    constituent_map[index] = res
    constituents = constituents.union(res)
    
    
av = AV_api(key)
    
# The free API has a limit of 5 API / minute
for sym in constituents:
    av_sym = sym.replace('.', '-') # need to convert Finnhub convention to av
    df = to_pandas(av.get_weekly(av_sym))
    df.to_csv('./data/prices/' + av_sym + '.csv')
    print("Finished " + av_sym)
    time.sleep(12)
    
# Now get data from these sector ETFs for the above indices
ETFs = set(['QQQ', 'SPY', 'DIA', 'XLK', 'XLV', 'XLC', 'XLF', 'XLI', 'XLP', 'XLU', 'XLB', 'XLRE', 'XLE'])
for sym in ETFs:
    av_sym = sym.replace('.', '-')
    df = to_pandas(av.get_weekly(av_sym))
    df.to_csv('./data/prices/' + av_sym + '.csv')
    print("Finished " + av_sym)
    time.sleep(12)
    
ETFs = set(['QQQ', 'SPY', 'DIA', 'XLK', 'XLV', 'XLC', 'XLF', 'XLI', 'XLP', 'XLU', 'XLB', 'XLRE', 'XLE'])
all_symbols = ETFs.union(constituents)

# Get high-level stats on the symbols
df_dict = {'symbol':[], 'name':[], 'type':[], 'region':[], 'currency':[]}
for sym in all_symbols:
    av_sym = sym.replace('.', '-')
    ret = av.search(av_sym)
    if 'bestMatches' in ret:
        ret = ret['bestMatches'][0]
        df_dict['symbol'].append(ret['1. symbol'])
        df_dict['name'].append(ret['2. name'])
        df_dict['type'].append(ret['3. type'])
        df_dict['region'].append(ret['4. region'])
        df_dict['currency'].append(ret['8. currency'])
        print("Finished " + av_sym)
        time.sleep(12)
