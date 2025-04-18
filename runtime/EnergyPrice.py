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
            return None
 
        header = {'Authorization': f"CW {token}"}

        try:
            lastvalue_url = f"{connection_params}13389"
            response = requests.get(lastvalue_url, headers=header)
            if response.status_code == 200:
                logger.info(f"EnergyPrice: Energy Price successfully retrieved!")
                json_response = response.json()
                return json_response[0]['Read']
            else:
                logger.warning(f"EnergyPrice: Error getting data from Energy Price: {response.status_code}")
        except requests.exceptions.Timeout:
            logger.error("EnergyPrice: Connection timeout.")  # Descobrir tempo de timeout
        except requests.exceptions.ConnectionError as e:
            logger.error(f"EnergyPrice: {e}")
        except requests.exceptions.RequestException as e:
            logger.error(f"EnergyPrice: Unexpected error - {e}")

        return None
