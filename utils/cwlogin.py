import requests
import time

credentials =  {
    "loginURL": "https://ks.innov.cleanwatts.energy/api/2.0/sessions",
    "login": "opevaapiaccess",
    "password": "I7z5eFoa"
}
class CWLogin():
    @staticmethod
    def login():
        login_data = {
            "Login": credentials.get('login'),
            "Password": credentials.get('password')
        }

        loginURL = credentials.get('loginURL')
        attempts = 0
        max_attempts = 3

        while attempts <= max_attempts:
            try: 
                response = requests.post(loginURL, json=login_data, timeout=60)

                if response.status_code == 201:
                    token = response.json().get('Token')
                    return token
                
                print(f"Attempt {attempts + 1} failed. Status code: {response.status_code}")

            except requests.exceptions.Timeout:
                print(f"Attempt {attempts + 1} failed: Connection timeout.")

            except requests.exceptions.ConnectionError:
                print(f"Attempt {attempts + 1} failed: No internet connection.")

            except requests.exceptions.RequestException as e:
                print(f"Attempt {attempts + 1} failed: Unexpected error - {e}")

            attempts += 1

        return None