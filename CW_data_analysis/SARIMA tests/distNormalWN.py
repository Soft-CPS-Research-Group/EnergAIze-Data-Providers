import numpy as np
import matplotlib.pyplot as plt

# Definindo os parâmetros
mu = 20  # média da temperatura
sigma = 1  # desvio padrão
n = 30  # número de dias

# Gerando valores de white noise
np.random.seed(42)  # para reprodutibilidade
epsilon = np.random.normal(0, sigma, n)

# Calculando as temperaturas
T = mu + epsilon

# Plotando os resultados
plt.plot(T, marker='o', label='Temperatura')
plt.axhline(mu, color='r', linestyle='--', label='Média (20 °C)')
plt.title('Temperatura Diária Simulada com White Noise')
plt.xlabel('Dias')
plt.ylabel('Temperatura (°C)')
plt.legend()
plt.grid()
plt.show()

n = 100  # Número de pontos de dados
mean = 0  # Média
std_dev = 1  # Desvio padrão

# Gerando os valores de white noise
white_noise = np.random.normal(mean, std_dev, n)

# Plotando os resultados
plt.plot(white_noise, marker='o', linestyle='-', label='White Noise')
plt.axhline(0, color='r', linestyle='--', label='Média (0)')
plt.title('Gráfico de White Noise')
plt.xlabel('Pontos de Dados')
plt.ylabel('Valor do White Noise')
plt.legend()
plt.grid()
plt.show()
