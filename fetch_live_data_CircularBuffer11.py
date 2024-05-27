import threading
import time
import pandas as pd
import requests
import mysql.connector
from kite_trade import KiteApp

class CircularBuffer:
    def __init__(self, size):
        self.size = size
        self.buffer = []

    def add(self, data):
        if len(self.buffer) < self.size:
            self.buffer.append(data)
        else:
            self.buffer.pop(0)
            self.buffer.append(data)

    def get_data(self):
        return self.buffer

def get_enctoken(userid, password, twofa):
    session = requests.Session()
    response = session.post('https://kite.zerodha.com/api/login', data={
        'user_id': userid,
        'password': password,
        'twofa': twofa
    })

    # Check if the request was successful
    if response.status_code != 200:
        print(f"Failed to authenticate. Status code: {response.status_code}")
        print("Response content:", response.content.decode('utf-8'))
        return None

    # Parse the JSON response
    try:
        data = response.json()
        enctoken = data['data']['request_id']
        return enctoken
    except KeyError as e:
        print(f"KeyError: {e}. Response content: {response.content.decode('utf-8')}")
        return None

def login(user_id, password, twofa):
    enctoken = get_enctoken(user_id, password, twofa)
    if not enctoken:
        return None
    kite = KiteApp(enctoken=enctoken)
    return kite

def logoff(kite):
    # Perform any cleanup operations if needed
    pass

def fetch_and_store_live_data(kite, buffer, duration, interval, data_list):
    start_time = time.time()
    while True:
        elapsed_time = time.time() - start_time
        if elapsed_time >= duration:
            print("Duration reached. Stopping data fetching.")
            break
        
        try:
            response = kite.ltp(["NSE:NIFTY BANK", "NSE:NIFTY 50"])  # Fetch live data, adjust instruments as needed
            live_data = response['data']
            buffer.add(live_data)
            data_list.append(live_data)  # Append live data to the data list
        except KeyError:
            print(f"Error: 'data' key not found in response. Response content: {response}")
        except Exception as e:
            print(f"Error occurred while fetching/parsing response: {e}. Response content: {response}")

        time.sleep(interval)

def save_to_mysql(data_list):
    db_host = "database-1.cfyqg0kwq7od.ap-south-1.rds.amazonaws.com"
    db_user = "ancit"
    db_password = "Ravi12345"
    db_database = "kite_data"

    conn = mysql.connector.connect(
        host=db_host,
        user=db_user,
        password=db_password,
        database=db_database
    )
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS live_data (
        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        instrument VARCHAR(255),
        last_price DECIMAL(10, 2),
        `change` DECIMAL(10, 2),
        volume BIGINT
    )
    """)

    for data in data_list:
        for instrument, details in data.items():
            cursor.execute("""
            INSERT INTO live_data (instrument, last_price, `change`, volume)
            VALUES (%s, %s, %s, %s)
            """, (instrument, details['last_price'], details['change'], details['volume']))

    conn.commit()
    cursor.close()
    conn.close()

def main():
    data_list = []
    
    user_id = "FVK571"
    password = "Ravi@966366"
    twofa = "588381"
    kite = login(user_id, password, twofa)
    
    if not kite:
        print("Failed to log in to Zerodha API. Exiting.")
        return
    
    buffer_size = 1
    live_data_buffer = CircularBuffer(buffer_size)

    duration = 30  # Duration for data fetching in seconds
    interval = 1   # Interval between data fetches in seconds
    fetch_thread = threading.Thread(target=fetch_and_store_live_data, args=(kite, live_data_buffer, duration, interval, data_list))
    fetch_thread.start()

    while fetch_thread.is_alive():
        latest_data = live_data_buffer.get_data()
        print(latest_data)
        time.sleep(interval)

    fetch_thread.join()
    logoff(kite)
    save_to_mysql(data_list)

if __name__ == "__main__":
    main()

