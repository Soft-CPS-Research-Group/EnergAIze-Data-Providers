import csv
import json
import time
import os
import sys
import pandas as pd
import numpy as np
import pika
from datetime import datetime
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from utils.data import DataSet

# Load configurations
configurations = DataSet.get_schema(os.path.join('..', 'runtimeConfigurations.json'))


class Translator:   
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
        #print(f'{df} and {df.dtypes}')
        df.set_index('Date', inplace=True)
        df = df.resample(f'{period}min').sum(min_count=1)

        full_date_range = pd.date_range(start=start_date, end=end_date, freq=f'{period}min', tz='UTC')
        
        df_full = pd.DataFrame(full_date_range, columns=['Date']).merge(df, on='Date', how='outer') #Alterei para outer de maneira a que todas as datas fiquem
        df_full.set_index('Date', inplace=True)
        df_full.sort_index(inplace=True)
        #print(f'{df} and {df_full}')
        Translator._remove_outliers(df_full)
        return df_full  
                       
    @staticmethod
    def div_verification(sDate, fDate, days, df):
        div = days // 2
        rest = days % 2
        #values = Translator.value(sDate, div + rest, df, 'sub')
        values = Translator.value(sDate, days, df, 'sub')
        if len(values) >= div + rest:
            values2 = Translator.value(fDate, div, df, 'sum')
            if len(values2) == div:
                values = values[-(div+rest):]
                values.extend(values2)
            else: 
                numberOfMissingValues = div - len(values2)
                if numberOfMissingValues < len(values)-div-rest:
                    values = values[-(div+rest-numberOfMissingValues):]
                    values.extend(values2)
                else:
                    values.extend(values2)       
        else:
            numberOfMissingValues = div + rest - len(values)
            values2 = Translator.value(fDate, div + numberOfMissingValues, df, 'sum')
            values.extend(values2)

        if len(values) < days:
            missing_values_count = days - len(values)
            for _ in range(missing_values_count):
                values.append({'Date': datetime(1, 1, 1, 0, 0), 'Value': 0})
        return values

    @staticmethod
    def value(date, days, df, operation):
        nDays = 0
        x = 1
        thereIsNoData = False
        values = []
        while nDays != days and not thereIsNoData:
            if operation == 'sum':
                newDate = date + pd.Timedelta(days=x)
            else:
                newDate = date - pd.Timedelta(days=x)
            
            if newDate not in df.index:
                thereIsNoData = True
            elif not np.isnan(df.loc[newDate]['Value']):
                values.append({'Date': newDate, 'Value': df.loc[newDate]['Value']}) 
                nDays+=1
            x+=1
    
        return sorted(values, key=lambda item: item['Date'])

    @staticmethod
    # Após um gap torna o primeiro valor (que é um acumulado dos gaps com a própria leitura) em Nan
    def _remove_outliers(df):
        i=0
        while i < len(df) - 1:
            atual = df.iloc[i]['Value']  # Utiliza iloc para aceder às linhas pela posição e não pelo index (que é a data - df.loc)
            proxima = df.iloc[i + 1]['Value']
            if pd.isna(atual) and not pd.isna(proxima):
                df.iloc[i + 1, df.columns.get_loc('Value')] = np.nan  # Modifica o valor com base na posição da coluna
                i += 2  # Incrementa i em 2 para pular o próximo índice
            else:
                i += 1  # Se a condição não for atendida, incrementa normalmente

    @staticmethod
    def _interpolateMissingValues(df):
        data = {}
        indexs = []
        x = 0

        for i in range(len(df)+1):
            if i != len(df):
                data[str(df.index[i])] = df.iloc[i]['Value']

            if i != len(df) and np.isnan(df.iloc[i]['Value']):
                #print(f'{df.index[i]}')
                x+=1
                indexs.append(df.index[i])
            elif x > 0:
                if x <= 6 and (indexs[0] - pd.Timedelta(hours=1)) in df.index and (indexs[-1] + pd.Timedelta(hours=1)) in df.index:  
                    value1 = df.loc[indexs[0] - pd.Timedelta(hours=1)]['Value']
                    value2 = df.loc[indexs[-1] + pd.Timedelta(hours=1)]['Value']
                    values = np.linspace(value1, value2, x+2)

                    for j in range(x):
                        data[str(indexs[j])] = values[j+1]
                else:
                    daysAndHours = {}
                    for j in range(x):
                        hour = indexs[j].hour
                        if hour in daysAndHours:
                            daysAndHours[hour].append(indexs[j])
                            daysAndHours[hour] = sorted(daysAndHours[hour], key=lambda item: item.time())
                        else:
                            daysAndHours[hour] = [indexs[j]]
                    for hour in daysAndHours:
                        days = len(daysAndHours[hour])
                        fDate = daysAndHours[hour][0]
                        lDate = daysAndHours[hour][-1]  
                        ver = Translator.div_verification(fDate, lDate, days, df)
                        for i in range(len(ver)):
                            data[str(daysAndHours[hour][i])] = ver[i]['Value'] 
                                                
                x = 0       
                indexs = []
        return data

    @staticmethod
    def _tocsv(filename, data, columns):
        with open(filename, mode='w', newline='') as file:
            writer = csv.DictWriter(file, fieldnames=columns)
            writer.writeheader()

            for date, values in data.items():
                # Inclui `Date` somente se estiver nas colunas e lida com valores simples (float/int) para `values`
                row = {'Date': date} if 'Date' in columns else {}

                # Verifica se `values` é um dicionário, caso contrário trata como valor simples
                if isinstance(values, dict):
                    row.update({col: values.get(col) for col in columns if col != 'Date'})
                else:
                    # Coloca o valor de `values` na coluna 'Value' se não for um dicionário
                    row['Value'] = values if 'Value' in columns else None

                writer.writerow(row)

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
    



                                
                        
                            
                
                        
