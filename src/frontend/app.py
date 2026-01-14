import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import sys
import os

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), '../'))

import importlib
from backend import exchange_client
importlib.reload(exchange_client)
from backend.exchange_client import ExchangeClient
from backend.simulation import OrderBookWalker
from backend.calculator import CostCalculator

st.set_page_config(page_title="Best Execution Analyzer", layout="wide")

# --- Header ---
st.title("Best Execution & Slippage Analyzer")
st.markdown("Compare excessive slippage costs on public exchanges vs. OTC desks.")

# --- Sidebar Inputs ---
st.sidebar.header("Trade Parameters")

import concurrent.futures

# ... (Imports remain same)

# Initialize Exchange Client (Cached per exchange)
@st.cache_resource
def get_exchange_client_v2(exchange_id):
    return ExchangeClient(exchange_id)

# Trading Pair
symbol = st.sidebar.selectbox("Trading Pair", ["BTC/USDT", "ETH/USDT", "SOL/USDT"])

# Exchanges to Compare
exchanges = st.sidebar.multiselect("Exchanges to Compare", ["binance", "kraken", "coinbase", "kucoin"], default=["binance", "kraken"])

# Trade Side
side = st.sidebar.radio("Side", ["Buy", "Sell"])

# Trade Size
trade_size = st.sidebar.number_input("Trade Size (USD)", min_value=1000.0, value=1000000.0, step=10000.0, format="%f")

# OTC Assumptions
st.sidebar.header("OTC Assumptions")
otc_bps = st.sidebar.slider("OTC Fee / Premium (bps)", 0, 100, 50)
otc_fee_percent = otc_bps / 10000.0

# Exchange Assumptions
exchange_fee_bps = st.sidebar.number_input("Exchange Fee (bps)", value=10)
exchange_fee_percent = exchange_fee_bps / 10000.0

# --- Analysis Logic ---

def analyze_exchange(exchange_id, symbol, side, trade_size):
    """
    Helper function to run simulation for a single exchange.
    Returns a dict with results or error.
    """
    try:
        client = get_exchange_client_v2(exchange_id)
        # Fetch order book
        order_book = client.fetch_order_book(symbol, limit=3000)
        
        if not order_book['asks'] or not order_book['bids']:
            return {"exchange": exchange_id, "error": "No data"}

        # Run Simulation
        walker = OrderBookWalker()
        sim_result = walker.simulate_trade(order_book, side, trade_size)
        
        # Calculate Costs
        calculator = CostCalculator(exchange_fee_rate=exchange_fee_percent)
        
         # Get Mid Price
        best_bid = order_book['bids'][0][0] if order_book['bids'] else 0
        best_ask = order_book['asks'][0][0] if order_book['asks'] else 0
        mid_price = (best_bid + best_ask) / 2 if best_bid and best_ask else 0

        drag_metrics = calculator.calculate_total_drag(sim_result['avg_price'], mid_price, side)
        
        return {
            "exchange": exchange_id,
            "avg_price": sim_result['avg_price'],
            "total_drag_pct": drag_metrics['total_percent'],
            "slippage_pct": drag_metrics['slippage_percent'],
            "filled": sim_result['filled'],
            "mid_price": mid_price,
            "order_book": order_book, # Return for charting if needed (only for best usually)
            "error": None
        }
    except Exception as e:
        return {"exchange": exchange_id, "error": str(e)}


# --- Tabs ---
tab_live, tab_hist = st.tabs(["Live Execution", "Historical Time-of-Day"])

with tab_live:
    # --- Analysis Logic ---
    if st.button("Analyze Execution", type="primary"):
        with st.spinner(f"Simulating Trade across {len(exchanges)} exchanges..."):
            
            results = []
            # Parallel Execution
            with concurrent.futures.ThreadPoolExecutor(max_workers=len(exchanges)) as executor:
                future_to_exchange = {executor.submit(analyze_exchange, exc, symbol, side, trade_size): exc for exc in exchanges}
                for future in concurrent.futures.as_completed(future_to_exchange):
                    results.append(future.result())
            
            # Process Results
            valid_results = [r for r in results if r['error'] is None]
            errors = [r for r in results if r['error'] is not None]
            
            for err in errors:
                st.warning(f"Failed to fetch data for {err['exchange']}: {err['error']}")

            if not valid_results:
                st.error("No valid data retrieved from any exchange.")
                st.stop()

            # Find Best Execution
            
            # Recalculate effective price including fee
            for r in valid_results:
                fee_mult = 1 + exchange_fee_percent
                
                if side == 'Buy':
                    r['effective_price'] = r['avg_price'] * (1 + exchange_fee_percent)
                else:
                    r['effective_price'] = r['avg_price'] * (1 - exchange_fee_percent)
            
            # Sort
            if side == 'Buy':
                valid_results.sort(key=lambda x: x['effective_price']) # Lowest is best
                best_res = valid_results[0]
                otc_price = best_res['mid_price'] * (1 + otc_fee_percent) # OTC Ask
                display_savings = otc_price - best_res['effective_price'] # Positive = Exchange Cheaper
            else:
                valid_results.sort(key=lambda x: x['effective_price'], reverse=True) # Highest is best
                best_res = valid_results[0]
                otc_price = best_res['mid_price'] * (1 - otc_fee_percent) # OTC Bid
                display_savings = best_res['effective_price'] - otc_price # Positive = Exchange Better

            # --- Display Results ---
            st.subheader(f"🏆 Winner: {best_res['exchange'].upper()}")
            
            col1, col2 = st.columns([2, 1])
            with col1:
                total_savings_usd = display_savings * trade_size / best_res['effective_price'] # Approx units * savings per unit? 
                # Cleaner: Savings % * Trade Size
                # Savings % = (OTC Price - Exchange Price) / OTC Price
                # Let's just use raw difference in total amounts.
                
                if side == 'Buy':
                     exchange_cost = trade_size # We spend trade_size USD.
                     # Wait, trade_size is USD amount. 
                     # Asset Acquired = Trade Size / Effective Price
                     qty_exchange = trade_size / best_res['effective_price']
                     qty_otc = trade_size / otc_price
                     diff_asset = qty_exchange - qty_otc
                     diff_usd = diff_asset * best_res['mid_price'] # Value of difference
                     
                     is_exchange_better = qty_exchange > qty_otc
                else:
                    # Sell trade_size USD worth? No, usually size is in Asset or USD. 
                    # Prompt says: "Jane types 5,000,000 into Trade Size". Context implies USD value of asset.
                    # If Selling $5M USD worth (at start price), we have X units.
                    # Let's assume Trade Size is USD value.
                    # So we are selling (Trade Size / Mid Price) units.
                    units_to_sell = trade_size / best_res['mid_price']
                    
                    proceeds_exchange = units_to_sell * best_res['effective_price']
                    proceeds_otc = units_to_sell * otc_price
                    
                    diff_usd = proceeds_exchange - proceeds_otc
                    is_exchange_better = diff_usd > 0
                    
                
                if is_exchange_better:
                    st.success(f"✅ **USE EXCHANGE ({best_res['exchange'].upper()})**\n\nEst. Advantage vs OTC: **${abs(diff_usd):,.2f}**")
                else:
                    st.error(f"⚠️ **USE OTC DESK**\n\nEst. Advantage vs Exchange: **${abs(diff_usd):,.2f}**")

            with col2:
                st.metric("Best Execution Price", f"${best_res['effective_price']:,.2f}")
                st.metric("OTC Price", f"${otc_price:,.2f}")
                st.metric("Net Advantage", f"${abs(diff_usd):,.2f}")

            # Comparison Table
            st.divider()
            st.subheader("Exchange Comparison")
            comp_data = []
            for r in valid_results:
                comp_data.append({
                    "Exchange": r['exchange'].upper(),
                    "Effective Price": f"${r['effective_price']:,.2f}",
                    "Slippage %": f"{r['slippage_pct']*100:.4f}%",
                    "Total Drag %": f"{r['total_drag_pct']*100:.4f}%"
                })
            st.dataframe(pd.DataFrame(comp_data))

            # --- Visualizations (For Best Exchange) ---
            
            st.divider()
            chart_col1, chart_col2 = st.columns(2)
            
            order_book = best_res['order_book']
            mid_price = best_res['mid_price']
            
            with chart_col1:
                st.subheader(f"Liquidity Depth ({best_res['exchange'].upper()})")
                
                bids_data = [x[:2] for x in order_book['bids']]
                asks_data = [x[:2] for x in order_book['asks']]
                bids = pd.DataFrame(bids_data, columns=['price', 'amount'])
                asks = pd.DataFrame(asks_data, columns=['price', 'amount'])
                
                bids['total_val'] = bids['price'] * bids['amount']
                asks['total_val'] = asks['price'] * asks['amount']
                
                bids['cumulative'] = bids['total_val'].cumsum()
                asks['cumulative'] = asks['total_val'].cumsum()
                
                fig_depth = go.Figure()
                fig_depth.add_trace(go.Scatter(x=bids['price'], y=bids['cumulative'], fill='tozeroy', name='Bids (Buy Walls)', line_color='green'))
                fig_depth.add_trace(go.Scatter(x=asks['price'], y=asks['cumulative'], fill='tozeroy', name='Asks (Sell Walls)', line_color='red'))
                
                range_pct = 0.05
                fig_depth.update_layout(
                    xaxis_range=[mid_price * (1-range_pct), mid_price * (1+range_pct)],
                    title="Order Book Depth (Cumulative USD)",
                    xaxis_title="Price",
                    yaxis_title="Volume (USD)"
                )
                st.plotly_chart(fig_depth)

            with chart_col2:
                st.subheader(f"Slippage Curve ({best_res['exchange'].upper()})")
                
                # Recalculate curve for best exchange
                walker = OrderBookWalker()
                sizes = [trade_size * 0.1, trade_size * 0.25, trade_size * 0.5, trade_size * 0.75, trade_size]
                slippages = []
                
                for s in sizes:
                     res = walker.simulate_trade(order_book, side, s)
                     if side == 'Buy':
                         slip = (res['avg_price'] - mid_price) / mid_price
                     else:
                         slip = (mid_price - res['avg_price']) / mid_price
                     slippages.append(slip * 100)
                
                fig_slip = go.Figure()
                fig_slip.add_trace(go.Scatter(x=sizes, y=slippages, mode='lines+markers', name='Slippage %'))
                fig_slip.update_layout(
                    title="Slippage Impact vs Trade Size",
                    xaxis_title="Trade Size (USD)",
                    yaxis_title="Slippage (%)"
                )
                st.plotly_chart(fig_slip)
    else:
        st.info("👈 Set parameters and click 'Analyze Execution' to start.")

with tab_hist:
    st.header("Historical Time-of-Day Analysis")
    st.markdown("Analyze the last 30 days of price action to find the hour of day with the lowest volatility.")
    
    if st.button("Analyze Best Trading Times"):
        with st.spinner("Fetching Historical Data..."):
            # Default to first exchange logic for simplicity or selection
            # Let's use the first selected exchange
            if not exchanges:
                 st.error("Please select at least one exchange in the sidebar.")
            else:
                target_exchange = exchanges[0]
                client = get_exchange_client_v2(target_exchange)
                
                df_hist = client.fetch_historical_volatility(symbol)
                
                if df_hist.empty:
                    st.error(f"Could not fetch historical data for {symbol} from {target_exchange}.")
                else:
                    # Group by Hour
                    hourly_vol = df_hist.groupby('hour')['volatility_pct'].mean().reset_index()
                    hourly_vol['volatility_pct'] = hourly_vol['volatility_pct'] * 100 # Convert to %
                    
                    # Highlight Best
                    best_hour = hourly_vol.loc[hourly_vol['volatility_pct'].idxmin()]
                    
                    st.success(f"🕒 **Best Time to Trade:** {int(best_hour['hour'])}:00 UTC (Avg Volatility: {best_hour['volatility_pct']:.4f}%)")
                    
                    # Bar Chart
                    fig_hist = go.Figure(data=[
                        go.Bar(x=hourly_vol['hour'], y=hourly_vol['volatility_pct'], marker_color='indianred')
                    ])
                    # Highlight best bar
                    fig_hist.data[0].marker.color = ['green' if h == best_hour['hour'] else 'indianred' for h in hourly_vol['hour']]

                    fig_hist.update_layout(
                        title="Average Hourly Volatility (UTC) - Last 30 Days",
                        xaxis_title="Hour (UTC)",
                        yaxis_title="Avg Volatility (%)",
                         xaxis=dict(tickmode='linear', tick0=0, dtick=1)
                    )
                    st.plotly_chart(fig_hist)
