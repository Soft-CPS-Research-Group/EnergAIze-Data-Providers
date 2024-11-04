# Importar bibliotecas
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from statsmodels.graphics.tsaplots import plot_acf, plot_pacf

# Definir o tamanho da série
n = 50  # Número de pontos da série temporal

# Criar a série temporal
t = np.arange(1, n + 1)  # Tempo de 1 a n
y_t = 2 * t  # Série temporal sem ruído

# Criar um DataFrame para facilitar a visualização
data = pd.DataFrame({'Tempo': t, 'Valores': y_t})

# Plotar a série temporal
plt.figure(figsize=(10, 5))
plt.plot(data['Tempo'], data['Valores'], marker='o')
plt.title('Série Temporal: $y_t = 2t$')
plt.xlabel('Tempo')
plt.ylabel('Valores')
plt.grid()
plt.show()

# Plotar ACF
plt.figure(figsize=(12, 6))
plt.subplot(1, 2, 1)
plot_acf(data['Valores'], lags=20, ax=plt.gca())
plt.title('Autocorrelação (ACF)')

# Plotar PACF
plt.subplot(1, 2, 2)
plot_pacf(data['Valores'], lags=20, ax=plt.gca())
plt.title('Autocorrelação Parcial (PACF)')

plt.tight_layout()
plt.show()

