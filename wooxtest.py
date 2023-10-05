import requests
import time
import streamlit as st
import ccxt
import pandas as pd
#from pybit.unified_trading import HTTP


def fetch_binance_order_book(symbol='BTCUSDT'):
    binance = ccxt.binance({
        'rateLimit': 1200,
        'enableRateLimit': True,
        'options': {'defaultType': 'swap'},
    })
    order_book = binance.fetch_order_book(symbol)
    if not order_book:
        return {"success": False, "error": "Failed to fetch data from Binance."}

    formatted_order_book = {
        'bids': [{'price': float(price), 'quantity': float(quantity)} for price, quantity in order_book['bids']],
        'asks': [{'price': float(price), 'quantity': float(quantity)} for price, quantity in order_book['asks']],
    }
    return formatted_order_book

def fetch_binance_swap_pairs():
    binance = ccxt.binance({
        'rateLimit': 1200,
        'enableRateLimit': True,
        'options': {'defaultType': 'swap'},
    })
    markets = binance.fetch_markets()
    binance_pairs = [market['symbol'] for market in markets if market['info'].get('contractType') == 'PERPETUAL']
    return binance_pairs

binance_pairs = fetch_binance_swap_pairs()


RATE_LIMIT_REQUESTS = 10
RATE_LIMIT_DURATION = 1  # in seconds



def fetch_bybit_order_book(symbol='BTC/USD'):
    bybit = ccxt.bybit({
        'rateLimit': 1200,
        'enableRateLimit': True,
        'options': {'defaultType': 'swap'},
    })
    order_book = bybit.fetch_order_book(symbol)
    if not order_book:
        return {"success": False, "error": "Failed to fetch data from Bybit."}

    formatted_order_book = {
        'bids': [{'price': float(price), 'quantity': float(quantity)} for price, quantity in order_book['bids']],
        'asks': [{'price': float(price), 'quantity': float(quantity)} for price, quantity in order_book['asks']],
    }
    return formatted_order_book




def fetch_woo_order_book(symbol='BTC/USDT'):
    woo = ccxt.woo({
        'rateLimit': 1200,
        'enableRateLimit': True,
        'options': {'defaultType': 'swap'},
    })
    order_book = woo.fetch_order_book(symbol)
    if not order_book:
        return {"success": False, "error": "Failed to fetch data from Woo."}

    formatted_order_book = {
        'bids': [{'price': float(price), 'quantity': float(quantity)} for price, quantity in order_book['bids']],
        'asks': [{'price': float(price), 'quantity': float(quantity)} for price, quantity in order_book['asks']],
    }
    return formatted_order_book

def fetch_okex_order_book(symbol='BTC-USDT-SWAP'):
    okex = ccxt.okex({
        'rateLimit': 1200,
        'enableRateLimit': True,
        'options': {'defaultType': 'swap'},
    })
    order_book = okex.fetch_order_book(symbol)
    if not order_book:
        return {"success": False, "error": "Failed to fetch data from OKEx."}

    formatted_order_book = {
        'bids': [{'price': float(price), 'quantity': float(quantity)} for price, quantity in order_book['bids']],
        'asks': [{'price': float(price), 'quantity': float(quantity)} for price, quantity in order_book['asks']],
    }
    return formatted_order_book



def display_order_book_results(order_book, order_size, fee_percentage):
    # If order book fetch is successful, display it
    if order_book and 'bids' in order_book and 'asks' in order_book:
        top_n = 10  # Show top 10 bids and asks
        bids_data = order_book['bids'][:top_n]
        asks_data = order_book['asks'][:top_n]

        with st.expander("Live Order Book", expanded=False):
            col1, col2 = st.columns(2)

            with col1:
                st.write("Bids")
                st.table(bids_data)

            with col2:
                st.write("Asks")
                st.table(asks_data)

        last_traded_price = order_book['bids'][0]['price']
        bought_quantity, avg_price = simulate_market_buy(order_book, order_size)

        lowest_ask_price = order_book['asks'][0]['price']
        spread = lowest_ask_price - last_traded_price

        # Calculate slippage
        slippage = avg_price - last_traded_price

        # Calculate fee amount
        fee_amount = (fee_percentage / 100) * order_size

        # Adjusting the slippage and spread calculations
        total_slippage_cost = slippage * bought_quantity
        total_spread_cost = spread * bought_quantity
        total_cost = fee_amount + total_slippage_cost + total_spread_cost

        # Calculate the average liquidity for the top 20 bids and asks
        top_n_ticks = 20
        avg_liquidity_bids = sum([bid['quantity'] for bid in order_book['bids'][:top_n_ticks]]) / top_n_ticks
        avg_liquidity_asks = sum([ask['quantity'] for ask in order_book['asks'][:top_n_ticks]]) / top_n_ticks

        avg_liquidity = (avg_liquidity_bids + avg_liquidity_asks) / 2

        # Display the results
        with st.expander("Trade Details", expanded=False):
            st.write(f'Average Order Book Liquidity 20Ticks: {round(avg_liquidity, 3)}')
            st.write(f'Quantity Bought: {round(bought_quantity, 3)}')
            st.write(f'Average Price: ${round(avg_price, 4)}')
            st.write(f'Total Slippage Cost: ${round(total_slippage_cost, 6)}')
            st.write(f'Fee Amount: ${fee_amount}')
            st.write(f'Total Spread Cost: ${round(total_spread_cost, 6)}')
        st.markdown(f'**Total Cost of Trade: ${round(total_cost, 6)}**')
    else:
        st.write("Failed to fetch or display the order book.")


def simulate_market_buy(order_book, order_size):
    total_spent = 0
    total_quantity = 0

    # Check if the order book is valid
    if not order_book or 'asks' not in order_book:
        return 0, 0

    for ask in order_book['asks']:
        if total_spent < order_size:
            price = ask['price']
            quantity = ask['quantity']
            cost = price * quantity

            if total_spent + cost <= order_size:
                total_spent += cost
                total_quantity += quantity
            else:
                remaining_budget = order_size - total_spent
                quantity_to_buy = remaining_budget / price
                total_spent += quantity_to_buy * price
                total_quantity += quantity_to_buy

    average_price = total_spent / total_quantity if total_quantity > 0 else 0
    return total_quantity, average_price



# Load pairs from files
with open("woox_pairs.txt", "r") as file:
    woo_pairs = [pair.strip() for pair in file.readlines()]

with open("bybit_perps.txt", "r") as file:
    bybit_pairs = [pair.strip() for pair in file.readlines()]

with open("okex_perps.txt", "r") as file:
        okex_pairs = [pair.strip() for pair in file.readlines()]

# Streamlit UI
st.title('Market Buy Simulator')

col1, col2, col3, col4 = st.columns(4)

with col1:
    # Woo Network Exchange UI
    st.write("### Woo Network")
    selected_symbol_woo = st.selectbox("Select a trading pair:", woo_pairs, key="woo_select")
    order_size_woo = st.number_input("Enter Order Size ($):", value=5000.0, min_value=0.0, step=100.0,
                                     key="woo_order_size")

    fee_input_woo = st.text_input("Taker Fee (%):", value="0.03", key="woo_fee")
    try:
        fee_percentage_woo = float(fee_input_woo)
    except ValueError:
        st.warning("Please enter a valid fee percentage for Woo Network.")
        fee_percentage_woo = 0.015  # default value in case of invalid input

with col2:
    # Bybit Exchange UI
    st.write("### Bybit")
    selected_symbol_bybit = st.selectbox("Select a trading pair:", bybit_pairs, key="bybit_select")
    order_size_bybit = st.number_input("Enter Order Size ($):", value=5000.0, min_value=0.0, step=100.0, key="bybit_order_size")
    fee_input_bybit = st.text_input("Taker Fee (%):", value="0.055", key="bybit_fee")
    try:
        fee_percentage_bybit = float(fee_input_bybit)
    except ValueError:
        st.warning("Please enter a valid fee percentage for Bybit.")
        fee_percentage_bybit = 0.055  # default value in case of invalid input

with col3:
    # Binance Exchange UI
    st.write("### BinFu")
    selected_symbol_binance = st.selectbox("Select a trading pair:", binance_pairs, key="binance_select")
    order_size_binance = st.number_input("Enter Order Size ($):", value=5000.0, min_value=0.0, step=100.0, key="binance_order_size")

    fee_input_binance = st.text_input("Taker Fee (%):", value="0.04", key="binance_fee")
    try:
        fee_percentage_binance = float(fee_input_binance)
    except ValueError:
        st.warning("Please enter a valid fee percentage for Binance.")
        fee_percentage_binance = 0.04  # default value in case of invalid input

with col4:
    st.write("### OKEx")
    selected_symbol_okex = st.selectbox("Select a trading pair:", okex_pairs, key="okex_select")
    order_size_okex = st.number_input("Enter Order Size ($):", value=5000.0, min_value=0.0, step=100.0, key="okex_order_size")
    fee_input_okex = st.text_input("Taker Fee (%):", value="0.06", key="okex_fee")
    try:
        fee_percentage_okex = float(fee_input_okex)
    except ValueError:
        st.warning("Please enter a valid fee percentage for OKEx.")
        fee_percentage_okex = 0.06  # default value in case of invalid input

# Combined button for both exchanges
if st.button('Simulate Market Buys'):
    # Woo Network
    order_book_woo = fetch_woo_order_book(selected_symbol_woo)
    with col1:
        display_order_book_results(order_book_woo, order_size_woo, fee_percentage_woo)

    # Bybit
    order_book_bybit = fetch_bybit_order_book(selected_symbol_bybit)

    with col2:
        display_order_book_results(order_book_bybit, order_size_bybit, fee_percentage_bybit)

    # Binance
    order_book_binance = fetch_binance_order_book(selected_symbol_binance)
    with col3:
        display_order_book_results(order_book_binance, order_size_binance, fee_percentage_binance)

    # OkeX
    order_book_okex = fetch_okex_order_book(selected_symbol_okex)
    with col4:
        display_order_book_results(order_book_okex, order_size_okex, fee_percentage_okex)




