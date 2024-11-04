import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from statsmodels.graphics.tsaplots import plot_acf

# Definir uma semente para reprodução
np.random.seed(42)

# Criar uma série AR(1)
n = 1000  # Número de observações
ar_params = [0.7]  # Coeficientes AR
ar_process = [0] * n  # Inicializa a série

# Gerar os dados AR(1)
for t in range(1, n):
    ar_process[t] = ar_params[0] * ar_process[t-1] + np.random.normal()

# Criar um DataFrame
df_ar = pd.DataFrame(ar_process, columns=['AR1'])

# Criar uma série MA(1)
ma_params = [0.5]  # Coeficientes MA
ma_process = [0] * n  # Inicializa a série

# Gerar os dados MA(1)
for t in range(1, n):
    ma_process[t] = np.random.normal() + ma_params[0] * np.random.normal()

# Criar um DataFrame
df_ma = pd.DataFrame(ma_process, columns=['MA1'])
# Plotar ACF para a série AR(1)
plt.figure(figsize=(14, 6))

plt.subplot(1, 2, 1)
plot_acf(df_ar['AR1'], lags=40)
plt.title('ACF da Série AR(1)')

# Plotar ACF para a série MA(1)
plt.subplot(1, 2, 2)
plot_acf(df_ma['MA1'], lags=40)
plt.title('ACF da Série MA(1)')

plt.tight_layout()
plt.show()
'''Interpretar os Gráficos de ACF
Série AR(1):

Você deve observar que a ACF para a série AR(1) decai lentamente ao longo das defasagens. Isso indica que os valores passados da série têm uma influência duradoura nas previsões futuras.
Isso sugere que um modelo AR seria adequado para modelar esta série.
Série MA(1):

Para a série MA(1), você deve ver um corte rápido na ACF, onde as autocorrelações se tornam insignificantes após algumas defasagens.
Isso sugere que um modelo MA seria apropriado para modelar esta série, uma vez que a previsão se baseia nos erros recentes.'''