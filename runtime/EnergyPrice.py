import requests
from utils.cwlogin import CWLogin
from utils.config_loader import load_configurations

# Load configurations
configurations, logger = load_configurations('./configs/runtimeConfigurations.json',"energyprice")

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
                logger.error("EnergyPrice: Unexpected JSON response structure")
        else:
            return None
        
