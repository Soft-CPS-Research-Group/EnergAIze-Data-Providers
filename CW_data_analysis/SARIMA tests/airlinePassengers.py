import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from statsmodels.tsa.stattools import adfuller
from statsmodels.tsa.seasonal import seasonal_decompose
from statsmodels.graphics.tsaplots import plot_acf, plot_pacf
from statsmodels.tsa.arima.model import ARIMA
from sklearn.metrics import mean_squared_error

# create a function that returns the necessary metrics to test stationarity
def test_stationarity(timeseries):
    dftest_initial = adfuller(timeseries)
    dfoutput_initial = pd.Series(dftest_initial[0:4], 
          index=['Statistical Test', 
                 'p-value', 
                 '#Lags used', 
                 'Number of observations'
                 ])
    for key, value in dftest_initial[4].items():
        dfoutput_initial['Critical value ' + key] = value
    print(dfoutput_initial)
    print('\n') 

# define function that returns the ACF and PACF plots for a given time series
def autocorrelation_plots(timeseries, description, n_lags):
    plt.figure(figsize=(15,5))
    plt.subplot(121)
    plot_acf(timeseries, ax=plt.gca(), lags=n_lags)
    plt.title('Autocorrelation ({})'.format(description))
    plt.xlabel('Number of lags')
    plt.ylabel('correlation')
    plt.subplot(122)
    plot_pacf(timeseries, ax=plt.gca(), lags=n_lags)
    plt.title('Partial Autocorrelation ({})'.format(description))
    plt.xlabel('Number of lags')
    plt.ylabel('correlation')
    plt.show()    

df = pd.read_csv('airline-passengers.csv')
df['Month'] = pd.to_datetime(df['Month'])
df = df.set_index('Month')
df = df.asfreq(pd.infer_freq(df.index))  

df.info()
plt.figure(figsize=(20,5))
plt.plot(df)
plt.show()

test_stationarity(df)
test_stationarity(df.diff().dropna())
test_stationarity(df.diff(12).dropna())

# decompose the time series into its trend, seasonal and residuals components
result_decompose = seasonal_decompose(df, model='additive')
trend     = result_decompose.trend
seasonal  = result_decompose.seasonal
residuals = result_decompose.resid
# plot every component
plt.figure(figsize=(20,10))
plt.subplot(311)
plt.plot(trend)
plt.title('trend')
plt.subplot(312)
plt.plot(seasonal)
plt.title('seasonality')
plt.subplot(313)
plt.plot(residuals)
plt.title('residuals')
plt.show()

testing_timeframe = 6

train1 = df[:-testing_timeframe]
test1  = df[-testing_timeframe:]
print('training set (past data): ', len(train1))
print('test set (days to be forecasted ahead): ', len(test1))  

autocorrelation_plots(train1, 'original', 48)
autocorrelation_plots(train1.diff().dropna(), '1st diff', 15)
autocorrelation_plots(train1.diff(12).dropna(), 'seasonal diff', 14)

model_fit = ARIMA(train1,  
                  order = (2,1,1)
                ).fit()
print(model_fit.summary())
print('\n')

# create forecasts on training set (to evaluate how the model behaves to known-training data)
forecasts_on_train = model_fit.predict()
# create forecasts on test set (to evaluate how the model behaves to unknown-test data)
forecasts_on_test  = model_fit.forecast(len(test1))
# calculate the root mean squared error on the test set
RMSE = np.sqrt(mean_squared_error(test1['Passengers'], forecasts_on_test))
# print the AIC and RMSE 
print('AIC: ' , model_fit.aic)
print('RMSE: ', RMSE)
# plot the train and test daat against their corresponding forecasts
# on train data
plt.figure(figsize=(16,4))
plt.plot(train1['Passengers'], label="Actual")
plt.plot(forecasts_on_train, label="Predicted")
plt.legend()
plt.show()
# on test data
plt.figure(figsize=(16,4))
plt.plot(test1['Passengers'], label="Actual")
plt.plot(forecasts_on_test, label="Predicted")
plt.legend() 
plt.show()