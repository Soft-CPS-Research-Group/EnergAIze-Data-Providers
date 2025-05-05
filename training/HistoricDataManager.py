import json
import os
import csv
from datetime import datetime, timedelta, timezone
from utils.config_loader import load_configurations

configurations, logger = load_configurations('./configs/historicConfigurations.json',"accumulator")

class HistoricDataManager:
    def __init__(self, house_specs, house, stop_event):
        self._house = house
        self._devices = {}
        self._algorithmFormat = configurations.get('AlgorithmAtributes')
        self._stop_event = stop_event
        self.header_written = False
    
        for device in house_specs["devices"]:
            if 'label' in device and device['label'] != "ChargersSession":
                self._devices[device.get('id')] = device.get('label')
        print(f"Devices: {self._devices}")
        self._nDev = len(self._devices)
        if self._nDev == 0:
            self.close_connection()
        self._nDevF = 0
        self._data = {}
        self._stop_callback = None 

    def newMessage(self, ch, method, properties, body):
        body_str = body.decode('utf-8')
        jsonbody = json.loads(body_str)
        device_id = jsonbody.get('id')
        data = jsonbody.get('data')
        print(f"Device: {device_id}")
        #print(f"Data: {data}")
        if data is not None:
            for inst in data:
                timestamp = datetime.fromisoformat(inst)
                if timestamp not in self._data:
                    self._data[timestamp] = []
                self._data[timestamp].append({'label': self._devices.get(device_id), 'data': data[inst]})  
        else:
            self._nDevF = self._nDevF + 1

        if self._nDevF == self._nDev:  
            sorted(self._data.keys())
            self.algorithm_format()
        #print(f"Data: {self._data}")


    def algorithm_format(self):
        timestamps = list(self._data.keys())
        timestampsL = len(timestamps) - 1
        sd = timestamps[0].strftime("%Y-%m-%d")
        ed = timestamps[timestampsL].strftime("%Y-%m-%d")
        directory = 'datasets'
        if not os.path.exists(directory):
            os.makedirs(directory)
        filename = os.path.join(directory, f"{self._house}.csv")
        all_rows = []

        for timestamp in timestamps: 
            #print(f"Timestamp: {timestamp}")
            batteryChargingEnergy = 0
            self._algorithmFormat['month'] = timestamp.month
            self._algorithmFormat['hour'] = timestamp.hour
            self._algorithmFormat['minutes'] = timestamp.minute
            self._algorithmFormat['day_type'] = timestamp.weekday() 
            self._algorithmFormat['daylight_savings_status'] = self.is_daylight_saving(timestamp)
            for device in self._data.get(timestamp):
                label = device.get('label')
                #print(f"Dados uhgyhjj: {label} {device.get('data')}")
                if label == "non_shiftable_load":
                    for other_device in self._data.get(timestamp):
                        if other_device.get('label') == "battery_charging_energy":
                            batteryChargingEnergy =  other_device.get('data')
                    self._algorithmFormat['non_shiftable_load'] = device.get('data') - batteryChargingEnergy
                else:
                    if label in self._algorithmFormat.keys():
                        self._algorithmFormat[label] = device.get('data')
                        #SO ESTOU A CONSIDERAR UM DISPOSITIVO DE CADA

            for key in self._algorithmFormat.keys():
                if self._algorithmFormat[key] == "":
                    self._algorithmFormat[key] = 0
            #print(f"Data to send: {self._algorithmFormat}")       
            all_rows.append(self._algorithmFormat.copy())
            
            # Resetting the values in _algorithmFormat
            for key in self._algorithmFormat.keys():
                self._algorithmFormat[key] = 0 if isinstance(self._algorithmFormat[key], (int, float)) else ""
        #print(f"Data to send: {all_rows}")
        with open(filename, mode='w', newline='') as file:
            writer = csv.DictWriter(file, fieldnames=self._algorithmFormat.keys())
            writer.writeheader()
            writer.writerows(all_rows)
            self.close_connection()
        print(f"File {filename} created")

    def is_daylight_saving(self, date):
        year = date.year
        lastSundayMarch = datetime(year,4,1,2,tzinfo=timezone.utc)
        lastSundayMarch += timedelta(6-lastSundayMarch.weekday())
        lastSundayMarch -= timedelta(days=7) 

        lastSundayOctober = datetime(year,11,1,2,tzinfo=timezone.utc)
        lastSundayOctober += timedelta(6-lastSundayOctober.weekday())
        lastSundayOctober -= timedelta(days=7) 

        return lastSundayMarch <= date < lastSundayOctober

    def close_connection(self):
        self._stop_event.set()