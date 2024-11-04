import requests

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
        max_attempts = 3
        attempts = 0

        while attempts < max_attempts:
            response = requests.post(loginURL, json=login_data, timeout=60)
            if response.status_code == 201:
                token = response.json().get('Token')
                return token
            attempts += 1

        # Se chegou aqui, todas as tentativas falharam
        raise Exception("Failed to login after {} attempts".format(max_attempts))
