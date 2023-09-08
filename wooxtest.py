import requests
import time
import streamlit as st
from pybit.unified_trading import HTTP

# Initialize Bybit session (set testnet to False for real trading)
bybit_session = HTTP(testnet=True)

# Constants
API_ENDPOINT = 'https://api.woo.network/v1/public/orderbook/'
RATE_LIMIT_REQUESTS = 10
RATE_LIMIT_DURATION = 1  # in seconds

# Rate limit variables
REQUEST_COUNT = 0
LAST_REQUEST_TIME = time.time()


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


def fetch_bybit_order_book(symbol):
    """
    Fetch order book data from Bybit.
    """
    response = bybit_session.get_orderbook(category="linear", symbol=symbol)
    if response["retCode"] == 0:
        order_book = {
            'bids': [{'price': float(bid[0]), 'quantity': float(bid[1])} for bid in response["result"]["b"]],
            'asks': [{'price': float(ask[0]), 'quantity': float(ask[1])} for ask in response["result"]["a"]]
        }
        return order_book
    else:
        return {"success": False, "error": response["retMsg"]}


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


def simulate_market_buy(order_book, order_size):
    total_spent = 0
    total_quantity = 0

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


# Load pairs from the file
with open("woox_pairs.txt", "r") as file:
    pairs = [pair.strip() for pair in file.readlines()]

# Streamlit UI
st.title('Market Buy Simulator')

exchange = st.selectbox("Select an exchange:", ["Woo Network", "Bybit"])
selected_symbol = st.selectbox("Select a trading pair:", pairs)  # Ensure pairs list includes Bybit pairs

order_size = st.number_input("Enter Order Size ($):", min_value=0.0, step=50.0)

# Fee input field
fee_percentage = st.number_input("Fees (%):", value=0.03, step=0.01)

if st.button('Simulate Market Buy'):
    # Fetching order book data based on selected exchange
    if exchange == "Woo Network":
        order_book = fetch_order_book(selected_symbol)
    elif exchange == "Bybit":
        order_book = fetch_bybit_order_book(selected_symbol)

    # Displaying the live order book
    if order_book:
        top_n = 10  # Show top 10 bids and asks
        bids_data = order_book['bids'][:top_n]
        asks_data = order_book['asks'][:top_n]

        st.write("### Live Order Book")

        # Creating columns for side by side display
        col1, col2 = st.columns(2)

        with col1:
            st.write("#### Bids")
            st.table(bids_data)

        with col2:
            st.write("#### Asks")
            st.table(asks_data)

    if order_book and order_book.get("success"):
        last_traded_price = order_book['bids'][0]['price']
        bought_quantity, avg_price = simulate_market_buy(order_book, order_size)

        lowest_ask_price = order_book['asks'][0]['price']

        spread = lowest_ask_price - last_traded_price

        # Calculate slippage
        slippage = avg_price - last_traded_price
        fee_amount = (fee_percentage / 100) * order_size

        # Adjusting the slippage and spread calculations
        total_slippage_cost = slippage * bought_quantity
        total_spread_cost = spread * bought_quantity
        total_cost = fee_amount + total_slippage_cost + total_spread_cost

        # Display the results
        st.write(f'Quantity Bought: {round(bought_quantity, 3)}')
        st.write(f'Average Price: ${round(avg_price, 4)}')
        st.write(f'Total Slippage Cost: ${round(total_slippage_cost, 6)}')
        st.write(f'Fee Amount: ${round(fee_amount, 5)}')
        st.write(f'Total Spread Cost: ${round(total_spread_cost, 6)}')
        st.write(f'Total Cost of Trade: ${round(total_cost, 6)}')


    else:
        # Display more detailed error message
        st.write(f"Failed to fetch data. Error: {order_book.get('error', 'Unknown error')}")
