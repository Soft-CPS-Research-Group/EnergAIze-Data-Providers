import random
import pymongo
from pymongo.errors import PyMongoError
from pydoc import locate
from utils.config_loader import load_configurations

# Load configurations
configurations, logger = load_configurations('./configs/runtimeConfigurations.json',"accumulator")

class Predictor():
    def __init__(self, house_specs, house):
        self._providers = configurations.get('Providers')
        self._devices = house_specs["devices"]
        self._site = house_specs["site"]
        self._mongo_config = configurations.get('mongoDB')
        self._house = house

        self._client = None
        self._collection = None
        self._connect_to_db()

    def _connect_to_db(self):
        try:
            # Create a MongoDB client using the provided configuration
            self._client = pymongo.MongoClient(
                host=self._mongo_config['host'],
                port=self._mongo_config['port'],
                username=self._mongo_config['credentials']['username'],
                password=self._mongo_config['credentials']['password'],
                authSource=self._mongo_config.get('authSource', 'admin'),
                serverSelectionTimeoutMS=5000
            )

            db = self._client[self._site]
            self._collection = db[f'building_{self._house}']
            logger.info(f"Connected to MongoDB for house {self._house}")

        except PyMongoError as e:
            self._client = None
            self._collection = None
            logger.warning(f"Could not connect to MongoDB: {e}")

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
        if self._collection is None:
            self._connect_to_db()

        if self._collection is not None:
            try:
                inserted_id = self._collection.insert_one(message).inserted_id
                logger.info(f'Message saved with id: {inserted_id}')
            except PyMongoError as e:
                logger.error(f'Failed to insert data: {e}')
                self._collection = None
        else:
            logger.warning("Skipping MongoDB insert: no active connection.")