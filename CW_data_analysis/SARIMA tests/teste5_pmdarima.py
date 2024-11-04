import pandas as pd
import warnings
import numpy as np
import matplotlib.pyplot as plt
from pmdarima import auto_arima  # Importar auto_arima do pmdarima
from sklearn.metrics import mean_squared_error

warnings.filterwarnings("ignore")

# Carregar e preparar os dados
df = pd.read_csv('seattle-weather.csv')
df_filtered = df[['date', 'temp_max']]
df_filtered['date'] = pd.to_datetime(df_filtered['date'])
df_filtered.set_index('date', inplace=True)

# Dividir os dados: treino (2 anos) e teste (2 anos)
train = df_filtered[df_filtered.index < '2014-01-01']  # Treinar até o final de 2016
test = df_filtered[df_filtered.index >= '2014-01-01']  # Testar de 2017 a 2018

# Plotar os dados de treino e teste
plt.figure(figsize=(12, 6))
plt.plot(train['temp_max'], label='Treino (dados até 2013)', color='blue')
plt.plot(test['temp_max'], label='Teste (dados de 2013-2015)', color='green')
plt.title("Dados de Treinamento e Teste")
plt.xlabel("Data")
plt.ylabel("Temperatura Máxima (°C)")
plt.legend()
plt.show()

print(df.head())  # Exibe as primeiras linhas do DataFrame
print(df_filtered.head())  # Exibe as primeiras linhas do DataFrame filtrado
print(f"Número de dados de treino: {len(train)}")  # Verifica o número de dados de treino
print(f"Número de dados de teste: {len(test)}")  # Verifica o número de dados de teste
print(train.isnull().sum())  # Verifica se há valores nulos

# Ajustar o modelo SARIMA usando auto_arima nos dados de treino
model = auto_arima(train['temp_max'], seasonal=True, m=365, d=1, D=1,
                   trace=True, error_action='ignore', 
                   suppress_warnings=True)

print("Modelo ajustado!")

# Fazer a previsão para os próximos 2 anos (o período de teste)
forecast = model.predict(n_periods=len(test))

# Plotar as previsões versus os dados reais de teste
plt.figure(figsize=(12, 6))
plt.plot(test.index, test['temp_max'], label='Real (2013-2015)', color='blue')  # Dados reais (linha azul)
plt.plot(test.index, forecast, label='Previsão (2013-2015)', color='red')  # Previsão (linha vermelha)
plt.title("Previsão da Temperatura Máxima para 2013-2015")
plt.xlabel("Data")
plt.ylabel("Temperatura Máxima (°C)")
plt.legend()
plt.show()

# Calcular e imprimir RMSE
rmse = np.sqrt(mean_squared_error(test['temp_max'], forecast))
print(f"RMSE: {rmse}")