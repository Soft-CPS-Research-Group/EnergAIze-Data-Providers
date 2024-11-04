import csv
import pandas as pd
import numpy as np
from datetime import datetime

class Translator:   
    @staticmethod
    def div_verification(sDate, fDate, days, df):
        div = days // 2
        rest = days % 2
        values = Translator.value(sDate, div + rest, df, 'sub')
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
