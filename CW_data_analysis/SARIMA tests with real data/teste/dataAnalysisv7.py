import pandas as pd
import numpy as np
from sklearn.metrics import mean_squared_error

# Calcular sMAPE
def smape(actual, forecast):
    return 100 * np.mean(2 * np.abs(forecast - actual) / (np.abs(actual) + np.abs(forecast)))

# Loading and converting the Date column
df = pd.read_csv('33682.csv')
df['Date'] = pd.to_datetime(df['Date'])

# Set the Date column as the index
df.set_index('Date', inplace=True)

forecast = {}
actual = {}

for i in range(len(df)):
    hoje = df.index[i]
    ontem = hoje - pd.Timedelta(days=1)
    amanha = hoje + pd.Timedelta(days=1)
    if (ontem in df.index) and (amanha in df.index):  
        if (not np.isnan(df.loc[ontem]['Value'])) and (not np.isnan(df.loc[amanha]['Value'])):
            forecast[hoje] = (df.loc[ontem]['Value'] + df.loc[amanha]['Value'])/2
            actual[hoje] = df.loc[hoje]['Value']
    
rmse_list = []
smape_list = []

forecast_series = pd.Series(forecast)
actual_series = pd.Series(actual)


for i in range(len(forecast_series)):
    if (not np.isnan(forecast_series.iloc[i])) and (not np.isnan(actual_series.iloc[i])):
        rmse_day = np.sqrt(mean_squared_error([actual_series.iloc[i]], [forecast_series.iloc[i]]))
        rmse_list.append(rmse_day)

        smape_day = smape(actual_series.iloc[i], forecast_series.iloc[i])
        if np.isnan(smape_day):
            print(f'{actual_series.index[i]} : {actual_series.iloc[i]}   ,   {forecast_series.index[i]} : {forecast_series.iloc[i]}')
            smape_day = 0
        smape_list.append(smape_day)

for i in range(len(forecast_series)):
    print(f'{actual_series.index[i]} : {actual_series.iloc[i]}   ,   {forecast_series.index[i]} : {forecast_series.iloc[i]}\n')

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

    
