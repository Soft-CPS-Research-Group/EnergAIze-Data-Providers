import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from statsmodels.graphics.tsaplots import plot_acf, plot_pacf

# Definir uma semente para reprodução
np.random.seed(42)

# Criar dados para um modelo AR(1)
n = 100
ar_coefs = [0.8]  # Coeficiente para AR(1)
erro_ar = np.random.normal(0, 1, n)  # Erro aleatório

# Gerar a série temporal AR(1)
ar_series = [0]  # Valor inicial
for t in range(1, n):
    new_value = ar_coefs[0] * ar_series[t - 1] + erro_ar[t]
    ar_series.append(new_value)

# Criar um DataFrame para a série AR(1)
df_ar = pd.DataFrame(ar_series, columns=['valor_ar'])

# Criar dados para um modelo MA(1)
ma_coefs = [0.8]  # Coeficiente para MA(1)
erro_ma = np.random.normal(0, 1, n)  # Erro aleatório

# Gerar a série temporal MA(1)
ma_series = [0]  # Valor inicial
for t in range(1, n):
    new_value = erro_ma[t] + ma_coefs[0] * erro_ma[t - 1]
    ma_series.append(new_value)

# Criar um DataFrame para a série MA(1)
df_ma = pd.DataFrame(ma_series, columns=['valor_ma'])


# Plotar ACF e PACF para AR(1)
fig, ax = plt.subplots(2, 2, figsize=(12, 8))

# ACF para AR(1)
ax[0, 0].set_title('ACF para AR(1)')
plot_acf(df_ar['valor_ar'], lags=20, ax=ax[0, 0])

# PACF para AR(1)
ax[0, 1].set_title('PACF para AR(1)')
plot_pacf(df_ar['valor_ar'], lags=20, ax=ax[0, 1])

plt.tight_layout()
plt.show()

# Plotar ACF e PACF para MA(1)
fig, ax = plt.subplots(2, 2, figsize=(12, 8))

# ACF para MA(1)
ax[0, 0].set_title('ACF para MA(1)')
plot_acf(df_ma['valor_ma'], lags=20, ax=ax[0, 0])

# PACF para MA(1)
ax[0, 1].set_title('PACF para MA(1)')
plot_pacf(df_ma['valor_ma'], lags=20, ax=ax[0, 1])

plt.tight_layout()
plt.show()
