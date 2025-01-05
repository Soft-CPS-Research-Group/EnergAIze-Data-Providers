import os
import requests
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from data import DataSet
from cwlogin import CWLogin

# Load configurations
configurations = DataSet.get_schema(os.path.join('..', 'runtimeConfigurations.json'))

class EnergyPrice:
    @staticmethod
    def getEnergyPrice():
        connection_params = configurations.get('CWserver')

        try: 
            token = CWLogin.login() 
        except Exception as e:
            print(e)
            exit()
 
        header = {'Authorization': f"CW {token}"}
        lastvalue_url = f"{connection_params}13389"
        response = requests.get(lastvalue_url, headers=header)

        if response.status_code == 200:
            json_response = response.json()
            if isinstance(json_response, list):
                return json_response[0]['Read']
            else:
                print("Unexpected JSON response structure")
        else:
            return None
        
