import pandas as pd
import warnings
import matplotlib.pyplot as plt
from statsmodels.tsa.stattools import adfuller
from statsmodels.graphics.tsaplots import plot_acf, plot_pacf
from statsmodels.tsa.statespace.sarimax import SARIMAX
from statsmodels.tsa.seasonal import seasonal_decompose;

warnings.filterwarnings("ignore")

# Substitua 'seattle-weather.csv' pelo caminho correto para o seu arquivo CSV
df = pd.read_csv('seattle-weather.csv')

# Selecionar apenas as colunas 'date' e 'temp_max'
df_filtered = df[['date', 'temp_max']]

# Converter a coluna 'date' para datetime
df_filtered['date'] = pd.to_datetime(df_filtered['date'])

# Definir a coluna 'date' como índice
df_filtered.set_index('date', inplace=True)

# plotar decomposição
decomposition = seasonal_decompose(df_filtered['temp_max'], model='additive', period=365)	
fig = decomposition.plot()
# Função para testar estacionaridade
def test_stationarity(timeseries):
    result = adfuller(timeseries)
    print('Estatística ADF:', result[0])
    print('Valor p:', result[1])
    print('Número de Lags usados:', result[2])
    print('Número de Observações usadas para ADF:', result[3])
    print('Valores críticos:')
    for key, value in result[4].items():
        print(f'\t{key}: {value}')

# Teste de estacionaridade da série original
print("Teste de Estacionaridade para a série original:")
test_stationarity(df_filtered['temp_max'])

# Diferenciação não sazonal
df_diff = df_filtered['temp_max'].diff().dropna()
print("\nTeste de Estacionaridade após 1ª diferenciação:")
test_stationarity(df_diff)

# Diferenciação sazonal (exemplo para 1 ano)
df_seasonal_diff = df_filtered['temp_max'].diff(365).dropna()
print("\nTeste de Estacionaridade após diferenciação sazonal:")
test_stationarity(df_seasonal_diff)

# Plotar a série original, a diferença e a diferença sazonal
plt.figure(figsize=(15, 10))

# Subplot da série original
plt.subplot(3, 1, 1)
plt.plot(df_filtered.index, df_filtered['temp_max'], color='b')
plt.title('Temperatura Máxima Original')
plt.xlabel('Data')
plt.ylabel('Temperatura Máxima (°C)')
plt.grid(True)

# Subplot da diferenciação não sazonal
plt.subplot(3, 1, 2)
plt.plot(df_diff.index, df_diff, color='orange')
plt.title('Temperatura Máxima - 1ª Diferenciação')
plt.xlabel('Data')
plt.ylabel('Diferenciação (°C)')
plt.grid(True)

# Subplot da diferenciação sazonal
plt.subplot(3, 1, 3)
plt.plot(df_seasonal_diff.index, df_seasonal_diff, color='green')
plt.title('Temperatura Máxima - Diferenciação Sazonal')
plt.xlabel('Data')
plt.ylabel('Diferenciação Sazonal (°C)')
plt.grid(True)

plt.tight_layout()
plt.show()

# Plotar a ACF
plt.figure(figsize=(12, 6))
plot_acf(df_filtered['temp_max'], lags=15)
plt.title('Função de Autocorrelação (ACF)')
plt.show()

# Plotar a PACF
plt.figure(figsize=(12, 6))
plot_pacf(df_filtered['temp_max'], lags=15)
plt.title('Função de Autocorrelação Parcial (PACF)')
plt.show()

train_size = int(len(df_filtered) * 0.8)
train, test = df_filtered.iloc[:train_size], df_filtered.iloc[train_size:]

sarima = SARIMAX(train['temp_max'], order=(1,1,1), seasonal_order=(1,0,1,12))
sarima_fit = sarima.fit()

# Gerando previsões do modelo SARIMA
predicted = sarima_fit.predict()

# Plotando os dados originais e as previsões do modelo
plt.figure(figsize=(12, 6))
plt.plot(train.index, train['temp_max'], label='Dados Originais', color='blue', alpha=0.6)
plt.plot(train.index, predicted, label='Previsões SARIMA', color='red', linestyle='--')
plt.title('Série Temporal Original e Previsões do Modelo SARIMA')
plt.xlabel('Data')
plt.ylabel('Temperatura Máxima (°C)')
plt.legend()
plt.grid(True)
plt.show()

# Gerar previsões para o conjunto de teste
test_start = test.index[0]
test_end = test.index[-1]
predicted_test = sarima_fit.predict(start=test_start, end=test_end)

# Plotando os dados originais, os dados de teste e as previsões do modelo
plt.figure(figsize=(12, 6))
plt.plot(df_filtered.index, df_filtered['temp_max'], label='Dados Originais', color='blue', alpha=0.6)
plt.plot(test.index, test['temp_max'], label='Dados de Teste', color='green', linestyle='--')
plt.plot(test.index, predicted_test, label='Previsões SARIMA', color='red', linestyle='--')
plt.title('Série Temporal Original, Dados de Teste e Previsões do Modelo SARIMA')
plt.xlabel('Data')
plt.ylabel('Temperatura Máxima (°C)')
plt.legend()
plt.grid(True)
plt.show()