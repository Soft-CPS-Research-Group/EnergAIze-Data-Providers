import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from sklearn.metrics import mean_squared_error
from statsmodels.tsa.statespace.sarimax import SARIMAX

# Calcular sMAPE
def smape(actual, forecast):
    return 100 * np.mean(2 * np.abs(forecast - actual) / (np.abs(actual) + np.abs(forecast)))

df = pd.read_csv('33682.csv')
df['Date'] = pd.to_datetime(df['Date'])
df.set_index('Date',inplace=True)
df = df.asfreq('h')

train = df[df.index < '2024-05-14']
test = df[(df.index >= '2024-05-14') & (df.index <= '2024-07-30')]

model = SARIMAX(train['Value'], order=(1, 1, 1), seasonal_order=(1, 0, 0, 24), missing='drop')
results = model.fit()

train_predictions = results.get_prediction(start=train.index[0], end=train.index[-1])
train_predicted_mean = train_predictions.predicted_mean
train_predicted_mean.index = train.index

# Plotar os resultados
plt.figure(figsize=(12, 6))
plt.plot(train.index, train, label='Dados de Treino Reais')
plt.plot(train.index, train_predicted_mean, label='Previsões para os Dados de Treino', color='red')
plt.title('SARIMAX')
plt.xlabel('Data')
plt.ylabel('Valor')
plt.legend()
plt.show()


# Fazer previsões para os dados de teste
forecast = results.get_forecast(steps=len(test))
forecast_index = test.index
forecast_values = forecast.predicted_mean


rmse_list = []
smape_list = []

# Iterar sobre os dias no array de teste
for date in test.index:
    actual = test.loc[date, 'Value']
    forecast_value = forecast_values.loc[date]
    
    # Verificar se o valor real não é NaN
    if not np.isnan(actual):
        # Calcular RMSE para o dia (usando apenas o valor atual)
        rmse_day = np.sqrt(mean_squared_error([actual], [forecast_value]))
        rmse_list.append(rmse_day)
        
        # Calcular sMAPE para o dia
        smape_day = smape(actual, forecast_value)
        smape_list.append(smape_day)

# Calcular a média do RMSE e sMAPE (ignorando NaNs)
mean_rmse = np.nanmean(rmse_list) if rmse_list else np.nan
mean_smape = np.nanmean(smape_list) if smape_list else np.nan

# Exibir os resultados
print(f'Média RMSE: {mean_rmse}')
print(f'Média sMAPE: {mean_smape}')
'''# Calcular intervalos de confiança
conf_int = forecast.conf_int()

# Plotar os resultados
plt.figure(figsize=(12, 6))
plt.plot(test['Value'], color='orange', label='Dados de Teste')
plt.plot(forecast_index, forecast_values, color='red', label='Previsões Teste', linewidth=2)
plt.fill_between(forecast_index, conf_int.iloc[:, 0], conf_int.iloc[:, 1], color='gray', alpha=0.2, label='Intervalo de Confiança')
plt.title('SARIMAX')
plt.xlabel('Data')
plt.ylabel('Valor')
plt.legend()
plt.show()

# Calcular RMSE
rmse = np.sqrt(mean_squared_error(test['Value'], forecast_values))

smape_value = smape(test['Value'], forecast_values)

# Exibir os resultados
print(f'RMSE: {rmse}')
print(f'sMAPE: {smape_value}')'''