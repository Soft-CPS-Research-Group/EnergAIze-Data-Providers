import pandas as pd
import numpy as np
from sklearn.metrics import mean_squared_error

# Calcular sMAPE
def smape(actual, forecast):
    return 100 * np.mean(2 * np.abs(forecast - actual) / (np.abs(actual) + np.abs(forecast)))

# Carregar os dados
df = pd.read_csv('33682.csv')
df['Date'] = pd.to_datetime(df['Date'])
df.set_index('Date', inplace=True)
df = df.asfreq('h')

#forecast = df[(df.index >= '2024-05-13') & (df.index <= '2024-07-29')]
#actual = df[(df.index >= '2024-05-14') & (df.index <= '2024-07-30')]
forecast = df[(df.index >= '2024-05-13 00:00:00+00:00') & (df.index <= '2024-07-29 23:00:00+00:00')]
actual = df[(df.index >= '2024-05-13 01:00:00+00:00') & (df.index <= '2024-07-30 00:00:00+00:00')]
#forecast = df[(df.index >= '2023-09-14') & (df.index <= '2023-10-09')]
#actual = df[(df.index >= '2024-09-14') & (df.index <= '2024-10-09')]
rmse_list = []
smape_list = []

for i in range(len(forecast)): 
    if((not np.isnan(forecast.iloc[i]['Value'])) and (not np.isnan(actual.iloc[i]['Value']))):
        rmse_day = np.sqrt(mean_squared_error([actual.iloc[i]['Value']], [forecast.iloc[i]['Value']]))
        rmse_list.append(rmse_day)
        
        smape_day = smape(actual.iloc[i]['Value'], forecast.iloc[i]['Value'])
        if(np.isnan(smape_day)):
            print(f'{actual.index[i]} : {actual.iloc[i]["Value"]}   ,   {forecast.index[i]} : {forecast.iloc[i]["Value"]}')
            smape_day = 0
        smape_list.append(smape_day)

# Calcular a média dos erros
mean_rmse = np.mean(rmse_list)
mean_smape = np.mean(smape_list)
for i in range(len(rmse_list)):
    if np.isnan(rmse_list[i]):
        print(f'RMSE NaN: {forecast.index[i]}')
    if np.isnan(smape_list[i]):
        print(f'sMAPE NaN: {forecast.index[i]}')

print(f'Média RMSE: {mean_rmse}')
print(f'Média sMAPE: {mean_smape}')

    
