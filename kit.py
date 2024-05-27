# Modified get_enctoken function
import requests

def get_enctoken(user_id, password, twofa):
    login_url = "https://kite.zerodha.com/api/login"
    session_url = "https://kite.zerodha.com/api/session/token"

    login_payload = {
        "user_id": user_id,
        "password": password
    }

    session_payload = {
        "user_id": user_id,
        "twofa_value": twofa,
    }

    with requests.Session() as session:
        response = session.post(login_url, data=login_payload)
        
        # Print the response JSON to debug
        print("Login response JSON:", response.json())
        
        if 'data' in response.json() and 'request_id' in response.json()['data']:
            request_id = response.json()['data']['request_id']
            session_payload['request_id'] = request_id
        else:
            raise KeyError("request_id not found in the response")

        response = session.post(session_url, data=session_payload)
        
        # Print the response JSON to debug
        print("Session response JSON:", response.json())
        
        if 'data' in response.json() and 'enctoken' in response.json()['data']:
            return response.json()['data']['enctoken']
        else:
            raise KeyError("enctoken not found in the response")

# Test the modified function
user_id = "FVK571"
password = "Ravi@966366"
twofa = "494401"

enctoken = get_enctoken(user_id, password, twofa)
print("Encrypted token:", enctoken)

