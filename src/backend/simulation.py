import pandas as pd
from typing import Dict, List, Tuple

class OrderBookWalker:
    def __init__(self):
        pass

    def simulate_trade(self, order_book: Dict[str, Any], side: str, amount_usd: float) -> Dict[str, float]:
        """
        Simulates a trade by walking the order book.
        
        Args:
            order_book: Dictionary containing 'bids' and 'asks'.
            side: 'buy' or 'sell'.
            amount_usd: Total trade size in USD.
            
        Returns:
            Dictionary containing:
            - total_asset_acquired
            - avg_price
            - weighted_price_sum
            - slippage_percent (vs top of book)
            - filled: Boolean, True if simulating full amount was possible
        """
        if not order_book or 'bids' not in order_book or 'asks' not in order_book:
            return {
                "total_asset_acquired": 0.0,
                "avg_price": 0.0,
                "filled": False
            }

        # Determine which side of the book to consume
        # If we BUY, we consume ASKS.
        # If we SELL, we consume BIDS.
        orders = order_book['asks'] if side.lower() == 'buy' else order_book['bids']
        
        if not orders:
             return {
                "total_asset_acquired": 0.0,
                "avg_price": 0.0,
                "filled": False
            }

        remaining_usd = float(amount_usd)
        total_asset_acquired = 0.0
        weighted_price_sum = 0.0
        
        top_price = orders[0][0] # Price of the best offer/bid

        for entry in orders:
            price = entry[0]
            amount = entry[1]
            if remaining_usd <= 0:
                break
                
            level_value_usd = price * amount
            
            if remaining_usd >= level_value_usd:
                # Consume entire level
                total_asset_acquired += amount
                weighted_price_sum += price * amount
                remaining_usd -= level_value_usd
            else:
                # Partial fill
                partial_amount = remaining_usd / price
                total_asset_acquired += partial_amount
                weighted_price_sum += price * partial_amount
                remaining_usd = 0
                
        if total_asset_acquired == 0:
             return {
                "total_asset_acquired": 0.0,
                "avg_price": 0.0,
                "slippage_percent": 0.0,
                "filled": False
            }

        avg_price = weighted_price_sum / total_asset_acquired
        
        # Calculate slippage
        # For BUY: Avg Price > Top Price (Slippage is positive cost)
        # For SELL: Avg Price < Top Price (Slippage is positive cost relative to ideal)
        if side.lower() == 'buy':
            slippage_percent = (avg_price - top_price) / top_price
        else:
            slippage_percent = (top_price - avg_price) / top_price


        return {
            "total_asset_acquired": total_asset_acquired,
            "avg_price": avg_price,
            "slippage_percent": slippage_percent,
            "filled": remaining_usd <= 1.0 # Consider filled if remaining is negligible
        }
