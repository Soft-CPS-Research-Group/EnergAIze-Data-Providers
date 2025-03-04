import json
import datetime
import copy
from apscheduler.schedulers.background import BackgroundScheduler
from runtime.Predictor import Predictor
from threading import Lock
from runtime.EnergyPrice import EnergyPrice
from utils.data import DataSet
from utils.config_loader import load_configurations

# Load configurations
configurations, logger = load_configurations('./configs/runtimeConfigurations.json',"accumulator")

class Manager():
    def __init__(self, devices, house):
        self._time_interval = DataSet.calculate_interval(configurations.get('frequency'))
        self._start_sched()
        self._house = house
        self._devices = devices
        self._predictor = Predictor(devices,house)
        self._substitute_dict = {}
        self._dict = {}

        self._algorithm_format = configurations.get('AlgorithmAtributes')
        self._charger_session_format = configurations.get('ChargingSessionsFormat')
       
        self._timer_ended = Lock()

        self._message = ''
        self._energy_price = 0
     
    def non_shiftable_load(self, device):
        batteryChargingEnergy = 0
        for other_device in self._devices:
            if 'label' in other_device and other_device.get('label') == "battery_charging_energy":
                batteryChargingEnergy +=  self._dict[other_device.get('id')]['data']
                if other_device.get('generated') == 1:
                    self._message['generated'] = 1
    
        self._message['non_shiftable_load'] = self._dict[device.get('id')]['data'] - batteryChargingEnergy
                
    def charging_sessions(self, device):
        cs = self._dict[device.get('id')]['data']
        '''carId = cs['flexibility']['vehicle.model']
        
        for device in self._devices:
            if 'label' in device and device.get('label') == 'car' and device.get('id') == carId:
                cs['soc'] = device.get('data').get('stateOfCharge')
                break'''
        self._message['charging_sessions'].append(cs)

    def energy_price(self):
        energyPrice = EnergyPrice.getEnergyPrice()
        if (energyPrice is not None):
            self._message['energy_price'] = energyPrice
            self._energy_price = energyPrice
        else:
            self._message['energy_price'] = self._energy_price

    def solar_generation(self, device):
        self._message['solar_generation'] = self._dict[device.get('id')]['data']

    labels_functions_mapper = {
        "non_shiftable_load": non_shiftable_load,
        "solar_generation": solar_generation,
        "charging_sessions": charging_sessions
    }

    def newMessage(self, body):            
        body_str = body.decode('utf-8')
        jsonbody = json.loads(body_str)
        print(f"House: {self._house}, received message: {jsonbody}\n")
        try:             
            with self._timer_ended:
                bodyId = str(jsonbody['id'])
                bodyTimestamp = jsonbody['timestamp']
                bodyValue = jsonbody['value']
                self._dict[bodyId] = {'timestamp': bodyTimestamp, 'data': bodyValue, 'generated':0}

            return True
        except Exception as e:
            print(f"An unexpected error occurred: {e}")
            return False

    def _send(self):
        self._timer_ended.acquire()

        self._verify_and_replace_missing_data()
        self._format_data_for_model()
        self._predictor.predict(self._message)
        self._dict.clear()

        self._timer_ended.release()
    
    def _verify_and_replace_missing_data(self):
        for device in self._devices:
            if device.get('id') not in self._dict.keys():
                logger.warning(f"Device {device.get('id')} was not found.")
                if device.get('label') != "charging_sessions":
                    if device.get('id') in self._substitute_dict.keys():
                        self._dict[device.get('id')] = self._substitute_dict[device.get('id')]
                    else:
                        logger.warning(f"Device not found in substitute_dict: {device.get('id')}")
                        self._dict[device.get('id')] = {'timestamp': 0, 'data': 0, 'generated': 1}
                else:
                    aux = copy.deepcopy(self._charger_session_format)
                    aux['Charger Id'] = device.get('id')
                    self._dict[device.get('id')] = {'timestamp': 0, 'data': aux, 'generated': 1}
            else:
                self._substitute_dict[device.get('id')] = self._dict[device.get('id')]
                self._substitute_dict[device.get('id')]['generated'] = 0


    def _format_data_for_model(self):
        timestamp = datetime.datetime.now()
        self._message = copy.deepcopy(self._algorithm_format)
        self._message['month'] = timestamp.month
        self._message['hour'] = timestamp.hour
        self._message['day_type'] = timestamp.weekday()  # Obtém o tipo de dia (por exemplo, 'Weekday' ou 'Weekend')

        for device in self._devices:
            if 'label' in device and device.get('label') in self._algorithm_format.keys():
                label = device.get('label')
                
                if label in self.labels_functions_mapper:
                    self.labels_functions_mapper[label](self, device)
                
                if self._dict[device.get('id')]['generated'] == 1:
                    self._message['generated'] = 1
        
        self.energy_price()
        print(f"Message to the AI Model: {self._message}\n")

    
    def stop(self):
        self._scheduler.shutdown()

    def _start_sched(self):
        self._scheduler = BackgroundScheduler()
        self._scheduler.add_job(self._send, 'interval', seconds=self._time_interval, misfire_grace_time=10, coalesce=True)
        self._scheduler.start()
