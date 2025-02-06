import random
import pymongo
from pydoc import locate
from utils.config_loader import load_configurations

# Load configurations
configurations, logger = load_configurations('./configs/runtimeConfigurations.json',"accumulator")

class Predictor():
    def __init__(self, devices, house):
        self._providers = configurations.get('Providers')
        self._devices = devices

        mongo_config = configurations.get('mongoDB')
        mongo_client = pymongo.MongoClient(mongo_config['host'], mongo_config['port'])
        db = mongo_client[mongo_config['database']]
        self._collection = db[house]

    def predict(self, message):
        result = self._energaize_simulator(message)
        self._forwarder(result)
        self._save_data(message, result)
        
    def _energaize_simulator(self, message):
        randomN = random.randint(1, len(self._devices))
        selected_items = random.sample(self._devices, randomN)
        results = []

        for item in selected_items:
            value = round(random.uniform(0, 1000), 2)  
            results.append({'id': item['id'], 'value': value})

        return results
    
    def _forwarder(self,result):
        for item in result:
            provider = next((device['provider'] for device in self._devices if device['id'] == item['id']), None)
            decisionForwarder = self._providers[provider]
            locate(decisionForwarder).toForward(item)  

    def _save_data(self,message,result):
        id = self._collection.insert_one(message).inserted_id
        print('Message saved with id:', id)
