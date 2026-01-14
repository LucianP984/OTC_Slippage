class CostCalculator:
    def __init__(self, exchange_fee_rate: float = 0.001):
        """
        Args:
            exchange_fee_rate: Standard taker fee (e.g., 0.001 for 0.1%).
        """
        self.exchange_fee_rate = exchange_fee_rate

    def calculate_total_drag(self, avg_execution_price: float, mid_price: float, side: str) -> dict:
        """
        Calculates the total cost implications of the trade.
        
        Args:
            avg_execution_price: The simulated average price.
            mid_price: The reference mid-market price before trade.
            side: 'buy' or 'sell'.
            
        Returns:
            Dict with slippage_cost, fee_cost, total_cost_percent
        """
        if mid_price == 0:
             return {"slippage_percent": 0.0, "fee_percent": self.exchange_fee_rate, "total_percent": 0.0}

        # Calculate price impact (Slippage)
        if side.lower() == 'buy':
            slippage_percent = (avg_execution_price - mid_price) / mid_price
        else:
            slippage_percent = (mid_price - avg_execution_price) / mid_price
            
        # Total cost is Slippage + Fees
        # Note: Fees are usually applied to the executed amount.
        # Ideally, we sum the percentages approximation.
        total_percent = slippage_percent + self.exchange_fee_rate
        
        return {
            "slippage_percent": slippage_percent,
            "fee_percent": self.exchange_fee_rate,
            "total_percent": total_percent
        }

    def compare_otc(self, exchange_total_percent: float, otc_spread_percent: float) -> dict:
        """
        Compares Exchange execution vs OTC Desk execution.
        
        Args:
            exchange_total_percent: Total drag (slippage + fees).
            otc_spread_percent: OTC premium/fee (e.g. 0.005 for 50bps).
            
        Returns:
            Dict with recommendation and savings.
        """
        savings_percent = otc_spread_percent - exchange_total_percent
        
        return {
            "recommendation": "EXCHANGE" if savings_percent > 0 else "OTC",
            "savings_percent": abs(savings_percent)
        }
