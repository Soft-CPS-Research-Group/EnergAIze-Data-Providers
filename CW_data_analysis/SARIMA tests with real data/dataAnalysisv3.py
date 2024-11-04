import pandas as pd
import re
import matplotlib.pyplot as plt
import numpy as np
import itertools
import csv
from statsmodels.tsa.stattools import adfuller
from sklearn.metrics import mean_absolute_error, mean_squared_error
from statsmodels.tsa.statespace.sarimax import SARIMAX
from statsmodels.graphics.tsaplots import plot_acf, plot_pacf

def smape(actual, forecast):
    return 100 * np.mean(2 * np.abs(forecast - actual) / (np.abs(actual) + np.abs(forecast)))

def fitChecker(filename):
    existing_combinations = []
    with open(filename, 'r') as file:
        for line in file:
            match = re.search(r'SARIMAX\((\d+, \d+, \d+)\)x\((\d+, \d+, \d+, \d+)\)', line)
            if match:
                order = match.group(1)
                seasonal_order = match.group(2)
                existing_combinations.append(f"SARIMAX({order})x({seasonal_order})")
    return existing_combinations

def checkMetricas(filename):
    bestRMSE = ''
    bestSMAPE = ''
    rmseC = 200
    smapeC = 200
    with open(filename, 'r') as file:
        for line in file:
            match = re.search(r'SARIMAX\((\d+, \d+, \d+)\)x\((\d+, \d+, \d+, \d+)\) - AIC:(\d+\.\d+) - RMSE:(\d+\.\d+) - SMAPE:(\d+\.\d+)', line)
            if match: 
                order = match.group(1)
                seasonal_order = match.group(2)
                rmse = float(match.group(4))
                smape = float(match.group(5))
                if (rmse < rmseC):
                    rmseC = rmse
                    bestRMSE = f'({order})x({seasonal_order}) RMSE = {rmse} SMAPE = {smape}'
                if(smape < smapeC):
                    smapeC = smape
                    bestSMAPE = f'({order})x({seasonal_order}) RMSE = {rmse} SMAPE = {smape}'
    print(f'Best RMSE: {bestRMSE}\n')
    print(f'Best SMAPE: {bestSMAPE}')



tag = '33682'
df = pd.read_csv(f'{tag}.csv')
df['Date'] = pd.to_datetime(df['Date'])
df.set_index('Date',inplace=True)
df = df.asfreq('h')


trainDate = '2024-01-14'
train = df[df.index < trainDate]
test = df[(df.index >= trainDate) & (df.index <= '2024-01-16')]
filename = f'SARIMAresults_{trainDate}_{tag}.txt'
'''
existing_combinations = fitChecker(filename)
p = d = q = range(0, 3)
pdq = list(itertools.product(p, d, q))
seasonal_pdq = [(x[0], x[1], x[2], 24) for x in pdq]

best_aic = float("inf")
best_params = None

# Iterar sobre todas as combinações possíveis de parâmetros
for param in pdq:
    for param_seasonal in seasonal_pdq:
        try:
            print(f'Fitting SARIMAX{param}x{param_seasonal}')
            if f"SARIMAX{param}x{param_seasonal}" in existing_combinations:
                print(f'SARIMAX{param}x{param_seasonal} already fitted')
                continue
            model = SARIMAX(train['Value'], order=param, seasonal_order=param_seasonal, missing='drop')
            results = model.fit()
            forecast = results.get_forecast(steps=len(test))
            forecast_index = test.index
            forecast_values = forecast.predicted_mean
            rmse = np.sqrt(mean_squared_error(test['Value'], forecast_values))
            smape_value = smape(test['Value'], forecast_values)
            with open(filename,'a') as file:
                writer = csv.writer(file)
                writer.writerow([f'SARIMAX{param}x{param_seasonal} - AIC:{results.aic} - RMSE:{rmse} - SMAPE:{smape_value}'])
            print(f'SARIMAX{param}x{param_seasonal} - AIC:{results.aic} - RMSE:{rmse} - SMAPE:{smape_value}')
        except Exception as e:
            continue
'''
checkMetricas(filename)