import streamlit as st
from pybit.unified_trading import HTTP

# Initialize Bybit session (testnet for this example, set to False for real trading)
bybit_session = HTTP(testnet=True)

def fetch_bybit_order_book(symbol="BTCUSDT"):
    """Fetch order book data from Bybit."""
    response = bybit_session.get_orderbook(category="linear", symbol=symbol)
    if response["retCode"] == 0:
        return response["result"]
    else:
        st.write("Error fetching Bybit data:", response["retMsg"])
        return None

st.title('Simple Bybit Order Book Viewer')

# Fetch and display order book
order_book = fetch_bybit_order_book()

if order_book:
    st.write("Bids:", order_book["b"])
    st.write("Asks:", order_book["a"])
