# pragma pylint: disableBBmissing-docstring, invalid-name, pointless-string-statement

# --- Do not remove these libs ---
import numpy as np # noqa
import pandas as pd # noqa
from pandas import DataFrame

from freqtrade.strategy.interface import IStrategy

# --------------------------
# Add your lib to import here
import talib.abstract as ta
import freqtrade.vendor.qtpylib.indicators as qtpylib


# This is the class of the strategy
class RSIBB01(IStrategy):
    """
    Default Strategy provided by freqtrade bot.
    You can override it with your own strategy
    """

    # Minimal ROI designed for the strategy
    minimal_roi = {
    }

    # Optimal stoploss designed for the strategy
    """ Iniciaremos com stop loss infinito porque
    ainda precisamos encontrar um stop adequado
    e para isso precisamos executar testes
    -0.99 = stop loss infinit0""" 
    stoploss = -0.99

    # Optimal ticker interval for the strategy
    ticker_interval = '1h'

    # Optional order type mapping
    order_types = {
        'buy': 'limit',
        'sell': 'limit',
        'stoploss': 'limit',
        'stoploss_on_exchange': False
    }

    # Optional time in force for orders
    order_time_in_force = {
        'buy': 'gtc',
        'sell': 'gtc',
    }

    def populate_indicators(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        """
        Adds several different TA indicators to the given DataFrame
      
        """

        # Momentum Indicator
        # ------------------------------------
        # RSI
        dataframe['rsi'] = ta.RSI(dataframe)

        # Overlap Studies
        # ------------------------------------

        # Bollinger bands
        bollinger = qtpylib.bollinger_bands(qtpylib.typical_price(dataframe), window=20, stds=2)
        dataframe['bb_lowerband'] = bollinger['lower']
        dataframe['bb_middleband'] = bollinger['mid']
        dataframe['bb_upperband'] = bollinger['upper']


        return dataframe

    def populate_buy_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        """
        Lógica do RSI: não queremos comprar um ativo sobrevendido (RSI < 30), pois, 
        indica que ninguem quer e pode ficar a este nivel de preço baixo por muito tempo
        Lógica da BB: o preço tende a voltar para a média, então, se for < que a banda inferior,
        acreditamos que vai subir, em direção à média.  
        """
        dataframe.loc[
            (

                (dataframe['rsi'] > 30) &
                (dataframe["close"] < dataframe['bb_lowerband'] )
            ),
            'buy'] = 1
        return dataframe

    def populate_sell_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        """
        Lógica do RSI: não queremos comprar um ativo sobrecomprado (RSI < 83), pois, 
        indica que está muito caro, pode não subir mais. Cair é mais provável
        Lógica da BB: o preço tende a voltar para a média, então, se for > que a banda superior,
        acreditamos que vai cair, em direção à média.  
        """

        dataframe.loc[
            (
                (dataframe["close"] > dataframe['bb_middleband'] )
            ),
            'sell'] = 1

        return dataframe