import json
import os
import datetime
import pika
import copy
import sys	
import time
from threading import Timer
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
        self._chargerSessionFormat = configurations.get('ChargersSessionFormat')
        self._connection_params = pika.ConnectionParameters(host=configurations['internalAMQPServer']['host'],port=configurations['internalAMQPServer']['port'])
       
        self._timer = None
        self._timerEnded = False
        self._stopTimer = False
        self.start_timer()

        self._message = ''

    def newMessage(self, ch, method, properties, body):
        body_str = body.decode('utf-8')
        jsonbody = json.loads(body_str)
        '''se estiver a ser enviado um dicionário, não é possível processar a próxima mensagem, não é critico se uma mensagem
        ultrapassar o lock do self.send a correção é feita pelo gestor e será sempre considerado o valor mais recente
        a mensagem seguinte ficará sem valor mas em caso de falha existe o substitute_dict'''
        while self._timerEnded:
            pass
        
        bodyId = str(jsonbody['id'])
        bodyTimestamp = jsonbody['timestamp']
        bodyValue = jsonbody['value']
        self._dict[bodyId] = {'timestamp': bodyTimestamp, 'data': bodyValue, 'generated':0}
        print(f"Id: {bodyId}, received message: {self._dict[bodyId]}\n")


    def stop(self):
        print(f"Stopping thread {self._house}...")
        self._stopTimer = True
        self._timer.cancel()


    def send(self):
        self._timerEnded = True
        #verificar se chegaram dados de todos os dispositivos, se não, recorrer ao substitute_dict
        print(self._dict.keys())
        for device in self._devices:
            print(f"Device: {device.get('id')}, {device.get('label')}")
            if device.get('id') not in self._dict.keys():
                if device.get('label') != "ChargersSession":
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

        self.algorithm_format()
        self.save_data()
        self.send_to_queue()  

        if not self._stopTimer:
            self.restart()
            
        self._timerEnded = False
    

    def algorithm_format(self):
        timestamp = datetime.datetime.now()
        self._message = copy.deepcopy(self._algorithmFormat)
        batteryChargingEnergy = 0
        self._message['Month'] = timestamp.month
        self._message['Hour'] = timestamp.hour
        self._message['Minute'] = timestamp.minute
        self._message['Day Type'] = timestamp.weekday()  # Obtém o tipo de dia (por exemplo, 'Weekday' ou 'Weekend')

        for device in self._devices:
            if 'label' in device and device.get('label') in self._algorithmFormat.keys():
                label = device.get('label')
                if label == "Non Shiftable Load [kWh]":
                    for other_device in self._devices:
                        if 'label' in other_device and other_device.get('label') == "Battery Charging Energy [kWh]":
                            batteryChargingEnergy =  self._dict[other_device.get('id')]['data']
                            if other_device.get('generated') == 1:
                                self._message['Generated'] = 1
                    self._message['Non Shiftable Load [kWh]'] = self._dict[device.get('id')]['data'] - batteryChargingEnergy
                elif label == "ChargersSession":
                    self._message[label].append(self._dict[device.get('id')]['data'])
                else:
                    self._message[label] = self._dict[device.get('id')]['data']
                
                if self._dict[device.get('id')]['generated'] == 1:
                    self._message['Generated'] = 1
        self._message['Energy Price'] = EnergyPrice.getEnergyPrice()
        print(f'House: {self._house}, body: {self._message}\n')


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
        self._timer=Timer(self._timeInterval - 1,self.send) #secalhar aqui retiro um segundo para não correr o risco de chegarem mensagens do proximo intervalo, problema: se a mensagem do periodo atual que falta chegar nesse segundo...
        self._timer.start()


    def restart(self):
        self._dict.clear()
        self.start_timer()