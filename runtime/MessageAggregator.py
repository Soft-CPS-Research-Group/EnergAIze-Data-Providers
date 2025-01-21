import json
import os
import datetime
import pika
import copy
import sys	
import time
from threading import Timer, Lock
from IManager import IManager
from EnergyPrice import EnergyPrice
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from data import DataSet

# Load configurations
configurations = DataSet.get_schema(os.path.join('..', 'runtimeConfigurations.json'))


class MessageAggregator(IManager):
    def __init__(self, devices, house):
        self._house = house
        self._devices = devices
        self._substitute_dict = {}
        self._dict = {}

        self._timeInterval = DataSet.calculate_interval(configurations.get('frequency'))

        self._algorithmFormat = configurations.get('AlgorithmAtributes')
        self._chargerSessionFormat = configurations.get('ChargingSessionsFormat')
        self._connection_params = pika.ConnectionParameters(host=configurations['internalAMQPServer']['host'],port=configurations['internalAMQPServer']['port'])
       
        self._timer = None
        self._timerEnded = Lock()
        self._stopTimer = False

        self.start_timer()

        self._message = ''
     
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
        self._message['energy_price'] = EnergyPrice.getEnergyPrice()

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
            with self._timerEnded:
                bodyId = str(jsonbody['id'])
                bodyTimestamp = jsonbody['timestamp']
                bodyValue = jsonbody['value']
                self._dict[bodyId] = {'timestamp': bodyTimestamp, 'data': bodyValue, 'generated':0}

            return True
        except Exception as e:
            print(f"An unexpected error occurred: {e}")
            return False

    def send(self):
        self._timerEnded.acquire()

        self.verify_and_replace_missing_data()
        self.format_data_for_model()
        self.save_data()
        self.send_to_queue()  

        self._timerEnded.release()

        if not self._stopTimer:
            self.restart()
    
    def verify_and_replace_missing_data(self):
        for device in self._devices:
            if device.get('id') not in self._dict.keys():
                if device.get('label') != "charging_sessions":
                    if device.get('id') in self._substitute_dict.keys():
                        self._dict[device.get('id')] = self._substitute_dict[device.get('id')]
                    else:
                        print("Device not found in substitute_dict: ",device.get('id'))
                        self._dict[device.get('id')] = {'timestamp': 0, 'data': 0, 'generated': 1}
                else:
                    aux = copy.deepcopy(self._chargerSessionFormat)
                    aux['Charger Id'] = device.get('id')
                    self._dict[device.get('id')] = {'timestamp': 0, 'data': aux, 'generated': 1}
            else:
                self._substitute_dict[device.get('id')] = self._dict[device.get('id')]
                self._substitute_dict[device.get('id')]['generated'] = 0

    def format_data_for_model(self):
        timestamp = datetime.datetime.now()
        self._message = copy.deepcopy(self._algorithmFormat)
        self._message['month'] = timestamp.month
        self._message['hour'] = timestamp.hour
        self._message['day_type'] = timestamp.weekday()  # Obtém o tipo de dia (por exemplo, 'Weekday' ou 'Weekend')

        for device in self._devices:
            if 'label' in device and device.get('label') in self._algorithmFormat.keys():
                label = device.get('label')
                
                if label in self.labels_functions_mapper:
                    self.labels_functions_mapper[label](self, device)
                
                if self._dict[device.get('id')]['generated'] == 1:
                    self._message['generated'] = 1
        
        self.energy_price()
        print(f"Message to the AI Model: {self._message}\n")
    
    def send_to_queue(self):
        attempts = 0
        max_attempts = 3
        while attempts < max_attempts:
            try:
                connection = pika.BlockingConnection(self._connection_params)
                channel = connection.channel()
                queue_name = self._house + '_alg'
                channel.queue_declare(queue=queue_name, durable=True)
                message_bytes = json.dumps(self._message).encode('utf-8')
                channel.basic_publish(exchange='', routing_key=queue_name, body=message_bytes)
                channel.close()
                connection.close()
                break 
            except pika.exceptions.AMQPConnectionError as e:
                attempts += 1
                print(f"Connection failed, attempt {attempts}/{max_attempts}. Error: {e}")
                if attempts < max_attempts:
                    time.sleep(2)  
                else:
                    print("Max attempts reached. Could not send message to queue.")


    def save_data(self):
        file_path = self._house + '.json'
        if os.path.exists(file_path):
            with open(file_path, 'r+') as json_file:
                existing_data = json.load(json_file)
                existing_data["AlgorithmAtributes"].append(self._message)
                json_file.seek(0)
                json.dump(existing_data, json_file, indent=4)
        else:
            data = {"AlgorithmAtributes": [self._message]}
            with open(file_path, 'w') as json_file:
                json.dump(data, json_file, indent=4)


    def start_timer(self):
        self._timer=Timer(self._timeInterval-1,self.send) 
        self._timer.start()


    def restart(self):
        self._dict.clear()
        self.start_timer()

    
    def stop(self):
        self._stopTimer = True
        self._timer.cancel()