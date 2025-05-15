from collections import OrderedDict
import os
import pandas as pd
from training.Translator import Translator
from utils.config_loader import load_configurations

configurations, logger = load_configurations('./configs/historicConfigurations.json',"cleanwatts")

class CWHistoricDataTranslator(Translator):
    @staticmethod
    def translate(tagId, data, house, start_date, end_date, period):
        df = CWHistoricDataTranslator._data_format(data, period, start_date, end_date, ['Date', 'Value'])
        
        tosend = CWHistoricDataTranslator._interpolateMissingValues(df)

        tosend = {date: value for date, value in tosend.items() if start_date <= pd.to_datetime(date) <= end_date}
        tosend = OrderedDict(sorted(tosend.items()))
        #print(f"Data to send: {tosend}")
        CWHistoricDataTranslator._send(house, tagId, tosend)
        directory = 'devicesAndTags'
        if not os.path.exists(directory):
            os.makedirs(directory)
        filename = os.path.join(directory, f"{tagId}.csv")
        CWHistoricDataTranslator._tocsv(filename, tosend, ['Date', 'Value'])      
                    