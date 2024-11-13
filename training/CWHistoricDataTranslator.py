from collections import OrderedDict
import os
import sys
import pandas as pd
from Translator import Translator
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from data import DataSet

# Load configurations
configurations = DataSet.get_schema(os.path.join('..', 'runtimeConfigurations.json'))


class CWHistoricDataTranslator(Translator):
    @staticmethod
    def translate(tagId, data, house, start_date, end_date, period):
        df = CWHistoricDataTranslator._data_format(data, period, start_date, end_date, ['Date', 'Value'])
        
        tosend = CWHistoricDataTranslator._interpolateMissingValues(df)

        tosend = {date: value for date, value in tosend.items() if start_date <= pd.to_datetime(date) <= end_date}
        tosend = OrderedDict(sorted(tosend.items()))

        CWHistoricDataTranslator._send(house, tagId, tosend)
        CWHistoricDataTranslator._tocsv(f'{tagId}.csv', tosend, ['Date', 'Value'])      
                    