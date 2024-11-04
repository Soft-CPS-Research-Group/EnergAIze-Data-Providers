import pandas as pd
import warnings
import numpy as np
import matplotlib.pyplot as plt
from statsmodels.tsa.statespace.sarimax import SARIMAX
from statsmodels.tsa.seasonal import seasonal_decompose
from sklearn.metrics import mean_squared_error

warnings.filterwarnings("ignore")

# Carregar e preparar os dados
df = pd.read_csv('seattle-weather.csv')
df_filtered = df[['date', 'temp_max']]
df_filtered['date'] = pd.to_datetime(df_filtered['date'])
df_filtered.set_index('date', inplace=True)
decomposition = seasonal_decompose(df['temp_max'], model='additive', period=365)
fig = decomposition.plot()
plt.show()
'''
# Dividir os dados: treino (2 anos) e teste (2 anos)
train = df_filtered[df_filtered.index < '2015-01-01']# Treinar até o final de 2016
test = df_filtered[df_filtered.index >= '2015-01-01']  # Testar de 2017 a 2018
print(type(train))

print(train.head())
print(test.head())
# Plotar os dados de treino e teste
plt.figure(figsize=(12, 6))
plt.plot(train['temp_max'], label='Treino (dados até 2015)', color='blue')
plt.plot(test['temp_max'], label='Teste (dados de 2015)', color='green')
plt.title("Dados de Treinamento e Teste")
plt.xlabel("Data")
plt.ylabel("Temperatura Máxima (°C)")
plt.legend()
plt.show()

# Definir os parâmetros do modelo SARIMAX para dados diários
p, d, q = 1, 1, 1  # Parâmetros ARIMA
P, D, Q, s = 1, 1, 1, 365  # Parâmetros sazonais (anual)

# Ajustar o modelo SARIMAX nos dados de treino (primeiros 2 anos)
model = SARIMAX(train['temp_max'], order=(p, d, q), seasonal_order=(P, D, Q, s))
print("Sarting to fit the model...")
results = model.fit()
print("Model fitted!")
results.save('modelo_sarimax.pkl')
print("Modelo salvo como 'modelo_sarimax.pkl'")
# Fazer a previsão para os próximos 2 anos (o período de teste)
forecast = results.get_forecast(steps=len(test))
forecast_mean = forecast.predicted_mean
forecast_ci = forecast.conf_int()

# Plotar as previsões versus os dados reais de teste
plt.figure(figsize=(12, 6))
plt.plot(test.index, test['temp_max'], label='Real (2017-2018)', color='blue')  # Dados reais (linha azul)
plt.plot(test.index, forecast_mean, label='Previsão (2017-2018)', color='red')  # Previsão (linha vermelha)
plt.fill_between(forecast_ci.index, forecast_ci.iloc[:, 0], forecast_ci.iloc[:, 1], color='pink', alpha=0.3)
plt.title("Previsão da Temperatura Máxima para 2017-2018")
plt.xlabel("Data")
plt.ylabel("Temperatura Máxima (°C)")
plt.legend()
plt.show()

rmse = np.sqrt(mean_squared_error(test['temp_max'], forecast_mean))
print(f"RMSE: {rmse}")
'''