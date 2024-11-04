import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from statsmodels.tsa.stattools import adfuller
from statsmodels.tsa.statespace.sarimax import SARIMAX
from sklearn.metrics import mean_absolute_error, mean_squared_error
from statsmodels.graphics.tsaplots import plot_acf, plot_pacf

df = pd.read_csv('33682.csv')
df['Date'] = pd.to_datetime(df['Date'])
df.set_index('Date',inplace=True)
df = df.asfreq('h')

plt.figure(figsize=(12, 6))
plt.plot(df['Value'], color='blue')
plt.show()

start_date = '2024-05-01'
end_date = '2024-05-15'
dfOnlyOneMonth = df.loc[start_date:end_date]
plt.figure(figsize=(12,6))
plt.plot(dfOnlyOneMonth['Value'],color='blue')
for date in pd.date_range(start=start_date, end=end_date, freq='D'):
    plt.axvline(x=date, color='red', linestyle='--')
plt.show()

# Plotar ACF e PACF
plt.figure(figsize=(12,6))
dfp_acf = df.dropna(subset=['Value'])
result = adfuller(dfp_acf['Value'].dropna())
'''
Estatística do Teste de Dickey-Fuller: -8.11612168001309
Valor p: 1.1897118604341205e-12
'''
print(f'Estatística do Teste de Dickey-Fuller: {result[0]}')
print(f'Valor p: {result[1]}')
# ACF para identificar q
plt.subplot(121)
plot_acf(dfp_acf ['Value'], lags=48, ax=plt.gca())  # lags=48 assume duas sazonalidades diárias (24 horas)
plt.title('ACF')

# PACF para identificar p
plt.subplot(122)
plot_pacf(dfp_acf ['Value'], lags=48, ax=plt.gca())
plt.title('PACF')

plt.tight_layout()
plt.show()

train = df[df.index < '2024-01-14']
test = df[(df.index >= '2024-01-14') & (df.index <= '2024-01-16')]

model = SARIMAX(train['Value'], order=(2, 2, 1), seasonal_order=(2, 0, 0, 24*7), missing='drop')
results = model.fit()

# Fazer previsões para os dados de teste
forecast = results.get_forecast(steps=len(test))
forecast_index = test.index
forecast_values = forecast.predicted_mean

# Calcular intervalos de confiança
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

# Calcular sMAPE
def smape(actual, forecast):
    return 100 * np.mean(2 * np.abs(forecast - actual) / (np.abs(actual) + np.abs(forecast)))

smape_value = smape(test['Value'], forecast_values)

# Exibir os resultados
print(f'RMSE: {rmse}')
print(f'sMAPE: {smape_value}')