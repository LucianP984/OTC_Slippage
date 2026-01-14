import ccxt
import pandas as pd
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta

class ExchangeClient:
    def __init__(self, exchange_id: str = 'binance'):
        self.exchange_id = exchange_id
        try:
            exchange_class = getattr(ccxt, exchange_id)
            self.exchange = exchange_class()
        except AttributeError:
            raise ValueError(f"Exchange {exchange_id} not found in ccxt")

    def fetch_order_book(self, symbol: str, limit: int = 100) -> Dict[str, Any]:
        """
        Fetches the order book for a given symbol.
        Returns a dictionary with 'bids' and 'asks' lists.
        """
        if self.exchange_id.lower() == 'kucoin' and limit > 100:
             limit = 100

        # Let exceptions bubble up to be handled by the caller/UI
        return self.exchange.fetch_order_book(symbol, limit=limit)

    def get_available_symbols(self) -> List[str]:
        """Fetches available markets/symbols from the exchange."""
        try:
            self.exchange.load_markets()
            return list(self.exchange.markets.keys())
        except Exception as e:
            print(f"Error fetching markets: {e}")
            return []

    def fetch_historical_volatility(self, symbol: str, timeframe: str = '1h', days: int = 30) -> pd.DataFrame:
        """
        Fetches historical OHLCV data to analyze volatility trends.
        
        Returns:
            DataFrame with columns: ['timestamp', 'open', 'high', 'low', 'close', 'volume', 'date', 'hour', 'volatility_pct']
        """
        try:
            # Helper to fetch OHLCV (Limited by exchange API usually 500-1000 candles)
            # For 30 days of 1h data: 30 * 24 = 720 candles.
            if not self.exchange.has['fetchOHLCV']:
                return pd.DataFrame()
            
            since = self.exchange.milliseconds() - (days * 24 * 60 * 60 * 1000)
            ohlcv = self.exchange.fetch_ohlcv(symbol, timeframe, since=since, limit=1000)
            
            if not ohlcv:
                return pd.DataFrame()

            df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
            df['date'] = pd.to_datetime(df['timestamp'], unit='ms')
            df['hour'] = df['date'].dt.hour
            
            # Volatility Calculation: (High - Low) / Open
            df['volatility_pct'] = (df['high'] - df['low']) / df['open']
            
            return df

        except Exception as e:
            print(f"Error fetching historical data for {symbol}: {e}")
            return pd.DataFrame()
