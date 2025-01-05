import os
import random
import sys
from pydoc import locate
from IManager import IManager
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from data import DataSet

# Load configurations
configurations = DataSet.get_schema(os.path.join('..', 'runtimeConfigurations.json'))

class AlgorithmReceiver(IManager):
    def __init__(self, devices, house):
        self._providers = configurations.get('Providers')
        self._house = house
        self._devices = devices

    def newMessage(self, ch, method, properties, body):
        result = self.energAIzeSimulator(body)
        print(f"{self._house} - {body}")
        for item in result:
            provider = next((device['provider'] for device in self._devices if device['id'] == item['id']), None)
            decisionForwarder = self._providers[provider]
            locate(decisionForwarder).toForward(item)
           
    def stop(self):
        print(f"Stopping thread {self._house}...")    
        
    def energAIzeSimulator(self, message):
        randomN = random.randint(1, len(self._devices))
        selected_items = random.sample(self._devices, randomN)
        results = []

        for item in selected_items:
            value = round(random.uniform(0, 1000), 2)  
            results.append({'id': item['id'], 'value': value})

        return results
    
