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
        
    @staticmethod
    def _data_format(data, period, start_date, end_date, columns_to_keep):
        if not data:
            full_date_range = pd.date_range(start=start_date, end=end_date, freq=f'{period}min', tz='UTC')
            df_full = pd.DataFrame(full_date_range, columns=['Date'])
            df_full['Value'] = float('nan')
            df_full.set_index('Date', inplace=True)
            return df_full
        
        df = pd.DataFrame(data)[columns_to_keep]
        
        df['Date'] = pd.to_datetime(df['Date'], utc=True)
        df.set_index('Date', inplace=True)
        df = df.resample(f'{period}min').sum(min_count=1)

        full_date_range = pd.date_range(start=start_date, end=end_date, freq=f'{period}min', tz='UTC')
        
        df_full = pd.DataFrame(full_date_range, columns=['Date']).merge(df, on='Date', how='outer') #Alterei para outer de maneira a que todas as datas fiquem
        df_full.set_index('Date', inplace=True)
        df_full.sort_index(inplace=True)
        
        CWHistoricDataTranslator._remove_outliers(df_full)
        return df_full       
                    
    @staticmethod
    def _send (house, tagId, data):
        connection_params = configurations['internalAMQPServer']
        max_reconnect_attempts = configurations.get('maxReconnectAttempts')
        
        while max_reconnect_attempts > 0:
            try:
                connection = pika.BlockingConnection(pika.ConnectionParameters(
                    host=connection_params.get('host'),
                    port=connection_params.get('port')
                ))

                message = {
                    "id": tagId,
                    "data": data
                }
                channel = connection.channel()
                message_bytes = json.dumps(message).encode('utf-8')    
                channel.basic_publish(exchange='', routing_key=house, body=message_bytes)
                message = {
                    "id": tagId,
                    "data": None
                }
                message_bytes = json.dumps(message).encode('utf-8')    
                channel.basic_publish(exchange='', routing_key=house, body=message_bytes)
                channel.close()
                connection.close()
                break  # Break out of the retry loop if successful

            except pika.exceptions.AMQPConnectionError as e:
                max_reconnect_attempts -= 1  # Decrement the retry counter
                if max_reconnect_attempts == 0:
                    print(f"{house} translator reached maximum reconnection attempts. The message was not sent.")
                else:
                    print(f"{house} translator lost connection, attempting to reconnect...")
                    time.sleep(5) 
            except Exception as e:
                print(f"An unexpected error occurred: {e}")
                break
        print(f"Data of tagId {tagId} translated and sent to {house} successfully.")
    



                                
                        
                            
                
                        