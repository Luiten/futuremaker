import asyncio
import signal
import sys
import time
import traceback
from datetime import datetime

from futuremaker import utils, indicators
from futuremaker.binance_api import BinanceAPI
from futuremaker.bot import Bot
from futuremaker.algo import Algo
from futuremaker import log
from futuremaker.position_type import Type


class KamaEntry(Algo):
    def __init__(self, base='BTC', quote='USDT', floor_decimals=3, init_capital=10000, max_budget=10000):
        super().__init__(base=base, quote=quote, floor_decimals=floor_decimals, init_capital=init_capital, max_budget=max_budget)

    def ready(self):
        self.wallet_summary()

    # 1. 손절하도록. 손절하면 1일후에 집입토록.
    # 2. MDD 측정. 손익비 측정.
    # 3. 자본의 %를 투입.
    def update_candle(self, df, candle):

        candle = indicators.kama(df)
        # print(candle['kama'], candle['direction'])
        time = candle.name
        self.estimated_profit(time, candle.close)

        # buy_entry =  kamaEntry[0]>kamaEntry[1] and roc[1]<0 and roc[0] >0
        # sell_entry = kamaEntry[0]<kamaEntry[1] and roc[1]<0 and roc[0] <0
        # buy_exit = kamaEntry<kamaEntry[1] or (roc[1]>0 and roc[0]<0)
        # sell_exit =  kamaEntry>kamaEntry[1] or (roc[1]<0 and roc[0]>0)

        kamaEntry = df['kama']
        roc = df['direction']

        buy_entry = kamaEntry[-1] > kamaEntry[-2] and roc[-2] < 0 and roc[-1] > 0
        sell_entry = kamaEntry[-1] < kamaEntry[-2] and roc[-2] < 0 and roc[-1] < 0

        buy_exit = kamaEntry[-1] < kamaEntry[-2] or (roc[-2] > 0 and roc[-1] < 0)
        sell_exit = kamaEntry[-1] > kamaEntry[-2] or (roc[-2] < 0 and roc[-1] > 0)

        if buy_entry:
            # buy_entry
            if self.position_quantity < 0:
                log.logger.info(f'--> Close Short <-- {time}')
                quantity = self.close_short()
                self.calc_close(time, candle.close, self.position_entry_price, quantity)
            if self.position_quantity == 0:
                log.logger.info(f'--> Enter Long <-- {time}')
                self.open_long()
                self.calc_open(Type.LONG, time, candle.close, 0)
        elif buy_exit and self.position_quantity > 0:
            # close long
            log.logger.info(f'--> Exit Long <-- {time}')
            quantity = self.close_long()
            self.calc_close(time, candle.close, self.position_entry_price, quantity)

        if sell_entry:
            # sell_entry
            if self.position_quantity > 0:
                log.logger.info(f'--> Close Long <-- {time}')
                quantity = self.close_long()
                self.calc_close(time, candle.close, self.position_entry_price, quantity)
            if self.position_quantity == 0:
                log.logger.info(f'--> Enter Short <-- {time}')
                self.open_short()
                self.calc_open(Type.SHORT, time, candle.close, 0)
        elif sell_exit and self.position_quantity < 0:
            # close sell
            log.logger.info(f'--> Exit Short <-- {time}')
            quantity = self.close_short()
            self.calc_close(time, candle.close, self.position_entry_price, quantity)


if __name__ == '__main__':
    params = utils.parse_param_map(sys.argv[1:])
    year = 2019
    test_bot = Bot(None, symbol='BTCUSDT', candle_limit=24 * 7 * 2,
                   candle_period='1h',
                   test_start=f'{year}-01-01', test_end=f'{year}-12-31',
                   test_data='../candle_data/BINANCE_BNBUSDT, 240.csv'
                   # test_data='../candle_data/BINANCE_BTCUSDT, 60.csv'
                   # test_data='../candle_data/BITFINEX_BTCUSD, 120.csv'
                   # test_data='../candle_data/BINANCE_ETCUSDT, 60.csv'
                   # test_data='../candle_data/BITFINEX_ETHUSD, 60.csv'
                   )
    real_bot = Bot(BinanceAPI(), symbol='BTCUSDT', candle_limit=24 * 7 * 2,
                   backtest=False,
                   candle_period='1m',
                   telegram_bot_token='852670167:AAExawLUJfb-lGKVHQkT5mthCTEOT_BaQrg',
                   telegram_chat_id='352354994'
                   )

    algo = KamaEntry(base='BTC', quote='USDT', floor_decimals=3, init_capital=10000, max_budget=1000000)

    asyncio.run(test_bot.run(algo))
    # asyncio.run(real_bot.run(algo))

"""
# BINANCE_BTCUSDT, 60.csv
SUMMARY TOT_EQUITY:21220 TOT_PROFIT:11220 (112.20%) DD:18.7% MDD:31.7% TOT_TRADE:864 WIN%:50.1% P/L:1.2

# 

"""


