import requests
import json

def open_data_feed(tag_ids):
    url = f"https://ks.innov.cleanwatts.energy/api/2.0/feed?tags={'&tags='.join(map(str, tag_ids))}"
    headers = {
        "Authorization": "CW eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJVc2VySWQiOiI3MzgiLCJVc2VyS2V5IjoiNTk1ZDJjNDctZTVlMi00ZDA5LTg0NzYtODI5NjJlZWYyZmYyIiwiUHJvZmlsZVR5cGUiOiI2IiwiQ3VycmVuY3lTeW1ib2wiOiLigqwiLCJSYW5kb21CeXRlcyI6Im9ER2pGTjl0dkNVPSIsIm5iZiI6MTcxMzc3NDkzMiwiZXhwIjoxNzEzNzc4NTMyLCJpc3MiOiJodHRwOi8vY2xlYW53YXR0cy5lbmVyZ3kiLCJhdWQiOiJodHRwOi8vYXBpLmNsZWFud2F0dHMuZW5lcmd5In0.K6WNfJHnsfBMkRzS-6NmpWEu4RtoyhG1CzW1_2g83sY"
    }
    response = requests.get(url, headers=headers, stream=True)
    for line in response.iter_lines():
        if line:
            data = json.loads(line.decode('utf-8'))
            if data.get("TagId") == -1:
                print("Connection closed by server")
                break
            print(data)

if __name__ == "__main__":
    tag_ids = [30688]
    open_data_feed(tag_ids)
