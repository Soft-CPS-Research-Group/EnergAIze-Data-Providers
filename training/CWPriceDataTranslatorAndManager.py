from datetime import timedelta
from collections import OrderedDict
import os
import pandas as pd
from training.Translator import Translator
from utils.config_loader import load_configurations

configurations, logger = load_configurations('./configs/historicConfigurations.json',"cleanwatts")

class CWPriceDataTranslatorAndManager(Translator):
        
    @staticmethod
    def translate(tagId, data, house, start_date, end_date, period):
        df = CWPriceDataTranslatorAndManager._data_format(data, period, start_date, end_date, ['Date', 'Value'])
        #print(df)
        tosend = CWPriceDataTranslatorAndManager._interpolateMissingValues(df)
        
        pred = CWPriceDataTranslatorAndManager._predictions(tosend)
        pred = {date: value for date, value in pred.items() if start_date <= pd.to_datetime(date) <= end_date}
        pred = OrderedDict(sorted(pred.items()))

        directory = 'datasets'
        if not os.path.exists(directory):
            os.makedirs(directory)
        filename = os.path.join(directory, "pricing.csv")
        CWPriceDataTranslatorAndManager._tocsv(filename, pred, ['electricity_pricing', 'electricity_pricing_predicted_6h', 'electricity_pricing_predicted_12h', 'electricity_pricing_predicted_24h'])

    @staticmethod
    def _data_format(data, period, start_date, end_date, columns_to_keep):
        end_date+=timedelta(days=1)

        df = pd.DataFrame(data)[columns_to_keep]
        
        df['Date'] = pd.to_datetime(df['Date'], utc=True)
        df.set_index('Date', inplace=True)

        df = df.resample(f'{period}min').last(min_count=1)

        full_date_range = pd.date_range(start=start_date, end=end_date, freq=f'{period}min', tz='UTC')
        
        df_full = pd.DataFrame(full_date_range, columns=['Date']).merge(df, on='Date', how='left')
        df_full.set_index('Date', inplace=True)
        df_full.sort_index(inplace=True)

        CWPriceDataTranslatorAndManager._remove_outliers(df_full)
        return df_full
        
    @staticmethod
    def _predictions(data):
        predicted_data = {}
        for entry in data:
            current_value = data[entry]
        
            
            # Cria uma data para a previsão (6 horas à frente)
            prediction_date_6h = f'{pd.to_datetime(entry) + pd.Timedelta(hours=6)}'
            prediction_date_12h = f'{pd.to_datetime(entry) + pd.Timedelta(hours=12)}'
            prediction_date_24h = f'{pd.to_datetime(entry) + pd.Timedelta(hours=24)}'
            
            if prediction_date_24h in data:
                # Armazena o valor atual e a previsão no novo dicionário
                predicted_data[entry] = {
                    'electricity_pricing': current_value,
                    'electricity_pricing_predicted_6h': data[prediction_date_6h],
                    'electricity_pricing_predicted_12h': data[prediction_date_12h],
                    'electricity_pricing_predicted_24h': data[prediction_date_24h],
                }

        return predicted_data
                                
                        
                            
                
                        