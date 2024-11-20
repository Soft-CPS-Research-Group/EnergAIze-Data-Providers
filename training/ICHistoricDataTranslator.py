from datetime import datetime
from collections import OrderedDict
import pika
import os
import json
import csv
import time
import sys
import pandas as pd
import numpy as np
from Translator import Translator
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from data import DataSet

# Load configurations
configurations = DataSet.get_schema(os.path.join('..', 'historicConfigurations.json'))


class ICHistoricDataTranslator(Translator):
    @staticmethod
    def translate(house, devices, data, start_date, end_date, period):
        print(f'Translating historic data for house {house}...')
        dataById = {}
        messageIC = configurations['messageIC']
        for entry in data:
            for device in devices:
                for pm in messageIC.keys():
                    #print(f'{pm} in {entry} and {device} \n')
                    if pm in entry and device.get('label') == messageIC[pm]:
                        deviceId = device.get('id')
                        dici = {'Date': entry.get('time'), 'Value': entry.get(pm)}
                        if deviceId not in dataById:
                            dataById[deviceId] = [dici]
                        else:
                            dataById[deviceId].append(dici)
    
        for deviceId in dataById.keys():
            df = ICHistoricDataTranslator._data_format(dataById[deviceId], period, start_date, end_date, ['Date', 'Value'])
            tosend = ICHistoricDataTranslator._interpolateMissingValues(df)
            tosend = {date: value for date, value in tosend.items() if start_date <= pd.to_datetime(date) <= end_date}
            tosend = OrderedDict(sorted(tosend.items()))
            ICHistoricDataTranslator._send(house, deviceId, tosend)
            ICHistoricDataTranslator._tocsv(f'{deviceId}.csv', tosend, ['Date', 'Value'])


    
     
        