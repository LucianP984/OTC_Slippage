import pytest
import sys
import os

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), '../src'))

from backend.simulation import OrderBookWalker
from backend.calculator import CostCalculator

class TestSimulation:
    def test_simple_buy(self):
        # Setup mock order book
        # Asks: Price, Qty
        mock_book = {
            'asks': [
                [100.0, 1.0],  # $100 value
                [101.0, 1.0],  # $101 value
            ],
            'bids': []
        }
        
        walker = OrderBookWalker()
        
        # Scenario 1: Buy $100 (exactly first level)
        res = walker.simulate_trade(mock_book, 'buy', 100.0)
        assert res['avg_price'] == 100.0
        assert res['total_asset_acquired'] == 1.0
        
        # Scenario 2: Buy $150 (consumes first level + ~0.5 of second)
        # 1.0 @ 100 = $100
        # remaining $50. $50 / 101 = 0.4950495...
        # Total Qty = 1.4950495
        # Weighted Money = 150
        # Avg Price = 150 / 1.4950495 = 100.331...
        
        res = walker.simulate_trade(mock_book, 'buy', 150.0)
        expected_qty = 1.0 + (50.0 / 101.0)
        assert abs(res['total_asset_acquired'] - expected_qty) < 0.0001
        assert abs(res['avg_price'] - (150.0/expected_qty)) < 0.0001


class TestCalculator:
    def test_drag_calc(self):
        calc = CostCalculator(exchange_fee_rate=0.001) # 0.1%
        
        # Mid price 100. Exec price 101 (1% slippage)
        # Side BUY
        res = calc.calculate_total_drag(101.0, 100.0, 'buy')
        
        assert abs(res['slippage_percent'] - 0.01) < 0.00001
        assert abs(res['fee_percent'] - 0.001) < 0.00001
        assert abs(res['total_percent'] - 0.011) < 0.00001

    def test_otc_compare(self):
        calc = CostCalculator()
        
        # Exchange Cost: 0.5%
        # OTC Cost: 1.0%
        # Should recommend EXCHANGE
        res = calc.compare_otc(0.005, 0.010)
        assert res['recommendation'] == 'EXCHANGE'
        assert abs(res['savings_percent'] - 0.005) < 0.0001
        
        # Exchange Cost: 1.5%
        # OTC Cost: 1.0%
        # Should recommend OTC
        res = calc.compare_otc(0.015, 0.010)
        assert res['recommendation'] == 'OTC'
