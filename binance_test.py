import streamlit as st
import ccxt

def fetch_order_book():
    binance = ccxt.binance({
        'rateLimit': 1200,
        'enableRateLimit': True,
        'options': { 'defaultType': 'future' },  # this line sets it to futures
    })
    symbol = 'BTCUSDT'
    order_book = binance.fetch_order_book(symbol)
    return order_book

def display_order_book(order_book):
    st.write("### Bids")
    st.write(order_book['bids'])

    st.write("### Asks")
    st.write(order_book['asks'])

st.title("Binance Futures BTCUSDT Order Book")

if st.button("Fetch Order Book"):
    order_book = fetch_order_book()
    display_order_book(order_book)
