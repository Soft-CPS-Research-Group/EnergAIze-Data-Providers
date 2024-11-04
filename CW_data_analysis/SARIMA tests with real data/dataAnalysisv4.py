import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from sklearn.metrics import mean_squared_error
from statsmodels.tsa.statespace.sarimax import SARIMAX

# Carregar os dados
df = pd.read_csv('33682.csv')
df['Date'] = pd.to_datetime(df['Date'])
df.set_index('Date', inplace=True)
df = df.asfreq('h')

# Definir parâmetros de validação cruzada
n_splits = 5  # Número de divisões para validação cruzada
train_size = int(len(df) * 0.8)  # 80% para treino
step_size = (len(df) - train_size) // n_splits  # Tamanho de cada passo

rmse_list = []
smape_list = []

for i in range(n_splits):
    # Definindo o conjunto de treino e validação
    train = df[:train_size + i * step_size]
    test = df[train_size + i * step_size: train_size + (i + 1) * step_size]

    # Treinando o modelo SARIMAX
    model = SARIMAX(train['Value'], order=(1, 1, 1), seasonal_order=(1, 0, 0, 24), missing='drop')
    results = model.fit(disp=False)

    # Fazendo previsões para os dados de teste
    forecast = results.get_forecast(steps=len(test))
    forecast_values = forecast.predicted_mean

    # Calcular RMSE
    rmse = np.sqrt(mean_squared_error(test['Value'], forecast_values))
    rmse_list.append(rmse)

    # Calcular sMAPE
    def smape(actual, forecast):
        denominator = np.abs(actual) + np.abs(forecast) + 1e-10  # Adiciona uma pequena constante para evitar divisão por zero
        return 100 * np.mean(2 * np.abs(forecast - actual) / denominator)

    smape_value = smape(test['Value'], forecast_values)
    smape_list.append(smape_value)

    # Plotar os resultados para a iteração atual
    plt.figure(figsize=(12, 6))
    plt.plot(train.index, train['Value'], label='Dados de Treino', color='blue')
    plt.plot(test.index, test['Value'], label='Dados de Teste', color='orange')
    plt.plot(test.index, forecast_values, label='Previsões Teste', color='red', linewidth=2)
    plt.fill_between(test.index, forecast.conf_int().iloc[:, 0], forecast.conf_int().iloc[:, 1], color='gray', alpha=0.2, label='Intervalo de Confiança')
    plt.title(f'SARIMAX - Iteração {i + 1}')
    plt.xlabel('Data')
    plt.ylabel('Valor')
    plt.legend()
    plt.show()

# Exibir os resultados médios
print(f'Média RMSE: {np.mean(rmse_list)}')
print(f'Média sMAPE: {np.mean(smape_list)}')
