import mysql.connector
from kite_trade import *
import threading
import time
import datetime

# Establish MySQL connection
mydb = mysql.connector.connect(
    host="your_host",
    user="your_username",
    password="your_password",
    database="your_database"
)

mycursor = mydb.cursor()

# Define table schema
mycursor.execute("""
CREATE TABLE IF NOT EXISTS live_data (
    id INT AUTO_INCREMENT PRIMARY KEY,
    instrument VARCHAR(255),
    ltp FLOAT,
    timestamp TIMESTAMP
)
""")

# Kite API credentials
user_id = "QFW742"       # Login Id
password = "Dhinakar.s"  # Login password
twofa = "922182"         # Login Pin or TOTP

# Authenticate and initialize Kite API
enctoken = get_enctoken(user_id, password, twofa)
kite = KiteApp(enctoken=enctoken)

# Circular buffer implementation
class CircularBuffer:
    def __init__(self, size):
        self.buffer = [None] * size
        self.size = size
        self.next_index = 0
    
    def add(self, data):
        self.buffer[self.next_index] = data
        self.next_index = (self.next_index + 1) % self.size
    
    def get_data(self):
        return self.buffer

# Initialize circular buffer
buffer_size = 10  # Adjust the size as needed
live_data_buffer = CircularBuffer(buffer_size)

# Function to continuously fetch live data and store it in MySQL
def fetch_and_store_live_data(kite, buffer, duration, data_list):
    start_time = time.time()
    while True:
        elapsed_time = time.time() - start_time
        if elapsed_time >= duration:
            print("Duration reached. Stopping data fetching.")
            break
        
        live_data = kite.ltp(["NSE:NIFTY BANK", "NSE:NIFTY 50"])  # Fetch live data, adjust instruments as needed
        buffer.add(live_data)
        data_list.append(live_data)  # Append data to list

        # Store live data in MySQL
        for instrument, data in live_data.items():
            ltp = data['last_price']
            sql = "INSERT INTO live_data (instrument, ltp, timestamp) VALUES (%s, %s, %s)"
            val = (instrument, ltp, time.strftime('%Y-%m-%d %H:%M:%S'))
            mycursor.execute(sql, val)
            mydb.commit()
        
        time.sleep(1)  # Adjust the interval as needed

# Duration for data fetching (in seconds)
duration = 30  # 30 seconds

# Data list to store live data
data_list = []

# Start fetching thread
fetch_thread = threading.Thread(target=fetch_and_store_live_data, args=(kite, live_data_buffer, duration, data_list))
fetch_thread.start()

# Main loop to access live data
while fetch_thread.is_alive():
    # Access live data from the circular buffer whenever needed
    latest_data = live_data_buffer.get_data()
    print(latest_data)
    time.sleep(1)  # Adjust the interval as needed 

# Wait for the fetching thread to complete
fetch_thread.join()

# Additional Kite API operations

# Get instrument or exchange
print(kite.instruments("NSE"))
print(kite.instruments("NFO"))

# Basic calls
print(kite.margins())
print(kite.orders())
print(kite.positions())

# Get Live Data
print(kite.ltp("NSE:RELIANCE"))
print(kite.ltp(["NSE:NIFTY 50", "NSE:NIFTY BANK"]))
print(kite.quote(["NSE:NIFTY BANK", "NSE:ACC", "NFO:NIFTY22SEPFUT"]))

# Fetch and print quotes periodically (Run this in a separate thread to avoid blocking)
def fetch_periodic_quotes():
    while True:
        print(kite.quote(["NSE:NIFTY BANK"]))
        time.sleep(600)

periodic_thread = threading.Thread(target=fetch_periodic_quotes)
periodic_thread.start()

# Get Historical Data
instrument_token = 424961
from_datetime = datetime.datetime.now() - datetime.timedelta(days=90)
to_datetime = datetime.datetime.now()
interval = "5minute"
print(kite.historical_data(instrument_token, from_datetime, to_datetime, interval, continuous=False, oi=False))

# Fetch Instrument Token for a Specific Instrument
instruments = kite.ltp('NSE:ITC')
instrument_token = instruments['NSE:ITC']['instrument_token']
print(f"Instrument Token for ITC: {instrument_token}")

# Fetch historical data for another example
instrument_token = 424961
from_datetime = datetime.datetime.now() - datetime.timedelta(days=7)
to_datetime = datetime.datetime.now()
interval = "5minute"
historical_data = kite.historical_data(instrument_token, from_datetime, to_datetime, interval, continuous=False, oi=False)
print(historical_data)

