import pandas as pd
import matplotlib.pyplot as plt
from statsmodels.tsa.seasonal import seasonal_decompose

df = pd.read_csv('33711.csv')
df['Date'] = pd.to_datetime(df['Date'])
df.set_index('Date',inplace=True)
df = df.asfreq('h')

plt.figure(figsize=(12, 6))
plt.plot(df['Value'], color='blue')
plt.show()

decomposition = seasonal_decompose(df['Value'], model='additive')

# Plotar os componentes da decomposição
plt.figure(figsize=(12, 8))

plt.subplot(411)
plt.plot(decomposition.observed, label='Observed')
plt.legend(loc='upper left')

plt.subplot(412)
plt.plot(decomposition.trend, label='Trend')
plt.legend(loc='upper left')

plt.subplot(413)
plt.plot(decomposition.seasonal, label='Seasonal')
plt.legend(loc='upper left')

plt.subplot(414)
plt.plot(decomposition.resid, label='Residual')
plt.legend(loc='upper left')

plt.tight_layout()
plt.show()

start_date = '2024-05-01'
end_date = '2024-05-15'
df_withLessData= df.loc[start_date:end_date]
plt.figure(figsize=(12, 6))
plt.plot(df_withLessData['Value'], color='blue')
plt.show()