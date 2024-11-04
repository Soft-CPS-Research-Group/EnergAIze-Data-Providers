import pandas as pd
import warnings
import matplotlib.pyplot as plt
from statsmodels.tsa.stattools import adfuller
from statsmodels.graphics.tsaplots import plot_acf, plot_pacf
from statsmodels.tsa.statespace.sarimax import SARIMAX

warnings.filterwarnings("ignore")

def check_stationarity(timeseries): 
    # Perform the Dickey-Fuller test 
    result = adfuller(timeseries, autolag='AIC') 
    p_value = result[1] 
    print(f'ADF Statistic: {result[0]}') 
    print(f'p-value: {p_value}') 
    print('Stationary' if p_value < 0.05 else 'Non-Stationary') 

df = pd.read_csv('seattle-weather.csv')
df_filtered = df[['date', 'temp_max']]
df.filtered = pd.DataFrame(df_filtered)
df_filtered['date'] = pd.to_datetime(df_filtered['date'])
print(df_filtered.head())
df_filtered.set_index('date')
monthly_temp = df_filtered.resample('M', on='date').mean()
print(monthly_temp.head())

plt.figure(figsize=(12, 6)) 
plt.plot(monthly_temp['temp_max'], linewidth=3,c='cyan') 
plt.title("Mean max temperature in Seattle") 
plt.xlabel("Date") 
plt.ylabel("Mean max temperature") 
plt.show()

check_stationarity(monthly_temp['temp_max'])

plt.figure(figsize=(12, 6))
plot_pacf(df_filtered['temp_max'], lags=12)
plt.title('Função de Autocorrelação Parcial (PACF)')
plt.show()

p, d, q = 1, 1, 1
P, D, Q, s = 1, 1, 1, 12  
  
model = SARIMAX(monthly_temp, order=(p, d, q), seasonal_order=(P, D, Q, s)) 
results = model.fit() 
model 

# Forecast future values 
forecast_periods = 12 # Forecast the next 12 months 
forecast = results.get_forecast(steps=forecast_periods) 
forecast_mean = forecast.predicted_mean 
forecast_ci = forecast.conf_int() 

# Plot the forecast 
plt.figure(figsize=(12, 6)) 
plt.plot(monthly_temp, label='Observed') 
plt.plot(forecast_mean, label='Forecast', color='red') 
plt.fill_between(forecast_ci.index, forecast_ci.iloc[:, 0], forecast_ci.iloc[:, 1], color='pink') 
plt.title("Mean Max temperature Forecast") 
plt.xlabel("Date") 
plt.ylabel("Mean Max temperature") 
plt.legend() 
plt.show()