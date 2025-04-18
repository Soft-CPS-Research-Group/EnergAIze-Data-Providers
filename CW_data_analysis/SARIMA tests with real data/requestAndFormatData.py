import sys
import os
import csv
import requests
import numpy as np
import pandas as pd

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))
from utils.cwlogin import CWLogin

def main(tag, period, unit):
    token = CWLogin().login()

    url = f"https://ks.innov.cleanwatts.energy/api/2.0/data/request/Instant?from=2003-04-24&tags={tag}&instantType=avg"
    headers = {
        'Authorization': f'CW {token}'
    }
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        data = response.json()
        save_to_csv(tag, data)
        df = data_format(tag,data, period, unit, ['Date', 'Value'])
        remove_outliers(df)
        df.to_csv(f'{tag}.csv', na_rep='NaN') # na_rep='NaN' to replace NaN values with 'NaN' in the csv file
    else:
        print('Failed to get data')

def save_to_csv(tag, data):
    filename= f'{tag}ToComp.csv'
    with open(filename, mode='w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(['Date', 'Value'])
        for entry in data:
            date = entry.get('Date')
            value = entry.get('Value')
            writer.writerow([date, value])
    
def data_format(data, period, unit, columns_to_keep):
    df = pd.DataFrame(data)[columns_to_keep]    
    df['Date'] = pd.to_datetime(df['Date'], utc=True) # utc=True to avoid timezone problems, in Portugal it is UTC+0 in winter and UTC+1 in summer
    df.set_index('Date', inplace=True) # inplace=True modifies the original dataframe instead of returning a new one
    return df.resample(f'{period}{unit}').sum(min_count=1)# min_count=1 to avoid NaN values when there is at least one value in the period
    # resample just works if the index is a datetime object

# Após um gap torna o primeiro valor (que é um acumulado dos gaps com a própria leitura) em Nan
def remove_outliers(df):
    i=0
    while i < len(df) - 1:
        atual = df.iloc[i]['Value']  # Utiliza iloc para aceder às linhas pela posição e não pelo index (que é a data - df.loc)
        proxima = df.iloc[i + 1]['Value']
        if pd.isna(atual) and not pd.isna(proxima):
            df.iloc[i + 1, df.columns.get_loc('Value')] = np.nan  # Modifica o valor com base na posição da coluna
            i += 2  # Incrementa i em 2 para pular o próximo índice
        else:
            i += 1  # Se a condição não for atendida, incrementa normalmente

if __name__ == '__main__':
    if len(sys.argv) > 3:
        try:
            number = int(sys.argv[1])
            period = int(sys.argv[2])
            unit = sys.argv[3]
            main(number,period,unit)
        except ValueError:
            print('Invalid argument')
    else:
        print('No argument given')

# For testing purposes, I will consider the José Basilio's Active Energy tag 33682