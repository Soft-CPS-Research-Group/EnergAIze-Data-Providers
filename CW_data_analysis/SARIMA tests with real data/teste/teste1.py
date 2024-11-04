import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import csv
from pandas import Timestamp
from statsmodels.tsa.seasonal import seasonal_decompose

# Loading and converting the Date column
df = pd.read_csv('33682.csv')
df['Date'] = pd.to_datetime(df['Date'])

# Set the Date column as the index
df.set_index('Date', inplace=True)

forecast = {}

indexs = []
x = 0

for i in range(len(df)):
    forecast[df.index[i]] = df.iloc[i]['Value']
    if np.isnan(df.iloc[i]['Value']):
        x+=1
        indexs.append(df.index[i])
    elif x > 0:
        if x <= 6:
            value1 = df.loc[indexs[0] - pd.Timedelta(hours=1)]['Value']
            value2 = df.loc[indexs[-1] + pd.Timedelta(hours=1)]['Value']
            values = np.linspace(value1, value2, x+2)
            print(f'{value1} , {value2} , {values}')
            for j in range(x):
                forecast[indexs[j]] = values[j+1]
                print(f'{df.loc[indexs[j]]} : {df.loc[indexs[j]]["Value"]}   ,   {forecast[indexs[j]]}\n')
        else:
            daysAndHours = {}
            for j in range(x):
                hour = indexs[j].hour
                if hour in daysAndHours:
                    daysAndHours[hour].append(indexs[j])
                    daysAndHours[hour] = sorted(daysAndHours[hour], key=lambda item: item.time())
                else:
                    daysAndHours[hour] = [indexs[j]]
            for hour in daysAndHours:
                days = len(daysAndHours[hour])
                for j in range(days):
                    nDays1 = 1
                    nDays2 = 1 
                    value1 = df.loc[daysAndHours[hour][0] - pd.Timedelta(days=1)]['Value']
                    value2 = df.loc[daysAndHours[hour][-1] + pd.Timedelta(days=1)]['Value']
                    while np.isnan(value1):
                        nDays1 += 1
                        value1 = df.loc[daysAndHours[hour][0] - pd.Timedelta(days=nDays1)]['Value']
                    while np.isnan(value2):
                        nDays2 += 1
                        value2 = df.loc[daysAndHours[hour][-1] + pd.Timedelta(days=nDays2)]['Value']
                values = np.linspace(value1, value2, x+2)
                print(f'{value1} , {value2} , {values}')
                for j in range(days):
                    forecast[daysAndHours[hour][j]] = values[j+1]
                    print(f'{df.loc[daysAndHours[hour][j]]} : {df.loc[daysAndHours[hour][j]]["Value"]}   ,   {forecast[daysAndHours[hour][j]]}\n')

        x = 0       
        indexs = []

file_csv = 'forecast.csv'

with open(file_csv, mode='w', newline='') as file:
    writer = csv.writer(file)
    writer.writerow(['Date','Value'])
    for date, value in forecast.items():
        writer.writerow([date, value])

print('Data was writted with success!')

# Extraindo datas e valores
dates = list(forecast.keys())
values = list(forecast.values())

start_date = Timestamp('2024-06-29 11:00:00+00:00', tz='UTC')
end_date = Timestamp('2024-09-01 16:00:00+00:00', tz='UTC')

# Filtrando as datas e valores dentro do intervalo
dates = [date for date in dates if start_date <= date <= end_date]
values = [forecast[date] for date in dates]

# Plotando os valores filtrados
plt.figure(figsize=(12, 6))
plt.plot(dates, values, color='blue')
plt.xlabel('Date')
plt.ylabel('Value')
plt.title('Forecast Values from 01.08.2024 to 31.08.2024')
plt.show()

data = pd.DataFrame({'Date': dates, 'Value': values})
data.set_index('Date', inplace=True)

# Decomposição sazonal
decomposition = seasonal_decompose(data['Value'], model='additive', period=30)

# Plotar os componentes
plt.figure(figsize=(12, 8))

plt.subplot(411)
plt.plot(data['Value'], label='Original')
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

      

