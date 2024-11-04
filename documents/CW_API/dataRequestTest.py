import requests
import json

def get_and_sort_data(url, headers):
    response = requests.get(url, headers=headers)
    
    if response.status_code == 200:
        data = response.json()
        
        sorted_data = sorted(data, key=lambda x: x['Date'], reverse=True)
        
        with open('dados_ordenados.json', 'w') as file:
            json.dump(sorted_data, file, indent=4)
            
        print("Os dados foram ordenados e salvos no arquivo 'dados_ordenados.json'.")
    else:
        print("Erro ao fazer o pedido HTTP:", response.status_code)

url = "https://ks.innov.cleanwatts.energy/api/2.0/data/request/Instant?from=2023-04-24&to=2024-05-13&instantType=avg&tags=29377"

headers = {
    "Authorization": "CW eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJVc2VySWQiOiI3MzgiLCJVc2VyS2V5IjoiNTk1ZDJjNDctZTVlMi00ZDA5LTg0NzYtODI5NjJlZWYyZmYyIiwiUHJvZmlsZVR5cGUiOiI2IiwiQ3VycmVuY3lTeW1ib2wiOiLigqwiLCJSYW5kb21CeXRlcyI6Im1NNDhZR3E4TnRzPSIsIm5iZiI6MTcxNTU5MDk2NywiZXhwIjoxNzE1NTk0NTY3LCJpc3MiOiJodHRwOi8vY2xlYW53YXR0cy5lbmVyZ3kiLCJhdWQiOiJodHRwOi8vYXBpLmNsZWFud2F0dHMuZW5lcmd5In0.RnEJTJvEbHFxpXDC-VrKx3J0-hxfnku2tt0DHLU2Ky0"
}

get_and_sort_data(url, headers)
