import pandas as pd
import numpy as np

# Criar um DataFrame a partir dos dados
data = {
    'Date': [
        "2024-04-24T00:00:00+01:00",
        "2024-04-24T00:02:00+01:00",
        "2024-04-24T00:06:00+01:00",
        "2024-04-24T00:15:00+01:00",
        "2024-04-24T00:30:00+01:00",
        "2024-04-24T00:45:00+01:00",
        "2024-04-24T00:47:00+01:00",
        "2024-04-24T01:00:00+01:00",
        "2024-04-24T01:30:00+01:00",
        "2024-04-25T01:30:00+01:00"
    ],
    'Value': [
        0.377,
        0.267,
        0.307,
        0.371,
        0.373,
        0.374,
        0.354,
        0.355,
        0.305,
        0
    ]
}

df = pd.DataFrame(data)

# Converter a coluna 'Date' para datetime
df['Date'] = pd.to_datetime(df['Date'])

# Definir a coluna 'Date' como índice
df.set_index('Date', inplace=True)

# Reamostrar para cada 15 minutos, somando os valores e mantendo NaN
df_resampled = df.resample('15min').sum(min_count=1)

# Mostrar o resultado
print(df_resampled)