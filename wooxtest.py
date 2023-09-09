import requests
import time
import streamlit as st
import websocket
import json
import threading
from pybit.unified_trading import HTTP
from pybit.unified_trading import WebSocket
from time import sleep

class BybitWebSocketManager:
    def __init__(self, testnet=True, symbol="BTCUSDT"):
        self.ws = WebSocket(testnet=testnet, channel_type="linear")
        self.order_book = None
        self.symbol = symbol
        self.data_event = threading.Event()  # Add an event for data synchronization

    def handle_message(self, message):
        print("WebSocket message:", json.dumps(message, indent=4))  # Pretty print the entire message
        if 'orderbook' in message['topic']:
            orderbook_data = message['data']
            self.order_book = {
                'bids': [{'price': float(bid[0]), 'quantity': float(bid[1])} for bid in orderbook_data['b']],
                'asks': [{'price': float(ask[0]), 'quantity': float(ask[1])} for ask in orderbook_data['a']]
            }
            self.data_event.set()


    def start(self):
        try:
            self.ws.orderbook_stream(depth=50, symbol=self.symbol, callback=self.handle_message)
        except Exception as e:
            print(f"WebSocket error: {e}")

    def get_order_book(self):
        if self.order_book:
            return self.order_book

        # if no cached data, you can either return live data or None
        # depending on your desired behavior
        return None
    def set_symbol(self, symbol):
        if self.symbol != symbol:
            self.symbol = symbol
            self.order_book = None  # Reset the order book
            self.start()  # Restart the WebSocket for the new symbol

    def stop(self):
        try:
            self.ws.disconnect()
        except Exception as e:
            print(f"Error disconnecting WebSocket: {e}")


websocket_manager = BybitWebSocketManager(testnet=True, symbol="BTCUSDT")

def get_websocket_manager():
    return websocket_manager



def is_rate_limit_exceeded():
    global REQUEST_COUNT, LAST_REQUEST_TIME

    if time.time() - LAST_REQUEST_TIME > RATE_LIMIT_DURATION:
        REQUEST_COUNT = 0
        LAST_REQUEST_TIME = time.time()

    if REQUEST_COUNT < RATE_LIMIT_REQUESTS:
        REQUEST_COUNT += 1
        return False
    else:
        return True


# Initialize Bybit session (set testnet to False for real trading)
bybit_session = HTTP(testnet=True)

# Constants
API_ENDPOINT = 'https://api.woo.network/v1/public/orderbook/'
RATE_LIMIT_REQUESTS = 10
RATE_LIMIT_DURATION = 1  # in seconds

# Rate limit variables
REQUEST_COUNT = 0
LAST_REQUEST_TIME = time.time()

def fetch_bybit_order_book(symbol):
    order_book_data = websocket_manager.get_order_book()
    print("Fetched order book data:", order_book_data)
    if order_book_data:
        # Convert the data to your desired format, similar to the HTTP response.
        order_book = {
            'bids': [{'price': float(bid['price']), 'quantity': float(bid['size'])} for bid in order_book_data if bid['side'] == 'Buy'],
            'asks': [{'price': float(ask['price']), 'quantity': float(ask['size'])} for ask in order_book_data if ask['side'] == 'Sell']
        }
        return order_book
    else:
        return {"success": False, "error": "Failed to fetch data from WebSocket."}

def fetch_order_book(symbol):
    global LAST_REQUEST_TIME

    if is_rate_limit_exceeded():
        time.sleep(RATE_LIMIT_DURATION)

    response = requests.get(f'{API_ENDPOINT}{symbol}')
    LAST_REQUEST_TIME = time.time()

    if response.status_code == 200:
        return response.json()
    else:
        # Improved error handling
        return {"success": False, "error": f"Received status code: {response.status_code}"}

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

        # Display the results
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

# Streamlit UI
st.title('Market Buy Simulator')

col1, col2 = st.columns(2)

with col1:
    # Woo Network Exchange UI
    st.write("### Woo Network")
    selected_symbol_woo = st.selectbox("Select a trading pair:", woo_pairs, key="woo_select")
    order_size_woo = st.number_input("Enter Order Size ($):", min_value=0.0, step=100.0, key="woo_order_size")
    fee_percentage_woo = st.number_input("Fees (%):", value=0.03, step=0.01, key="woo_fee")

with col2:
    # Bybit Exchange UI
    st.write("### Bybit")
    selected_symbol_bybit = st.selectbox("Select a trading pair:", bybit_pairs, key="bybit_select")
    order_size_bybit = st.number_input("Enter Order Size ($):", min_value=0.0, step=100.0, key="bybit_order_size")
    fee_input_bybit = st.text_input("Fees (%):", value="0.055", key="bybit_fee")
    try:
        fee_percentage_bybit = float(fee_input_bybit)
    except ValueError:
        st.warning("Please enter a valid fee percentage for Bybit.")
        fee_percentage_bybit = 0.055  # default value in case of invalid input

# Combined button for both exchanges
if st.button('Simulate Market Buys for Both Exchanges'):
    # Woo Network
    order_book_woo = fetch_order_book(selected_symbol_woo)
    with col1:
        display_order_book_results(order_book_woo, order_size_woo, fee_percentage_woo)

    # Bybit
    websocket_manager.set_symbol(selected_symbol_bybit)
    websocket_manager.data_event.clear()
    websocket_manager.start()
    websocket_manager.data_event.wait(1)
    order_book_bybit = websocket_manager.get_order_book()
    websocket_manager.stop()
    with col2:
        display_order_book_results(order_book_bybit, order_size_bybit, fee_percentage_bybit)


















