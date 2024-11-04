import pandas as pd
import numpy as np
from sklearn.linear_model import LinearRegression
import matplotlib.pyplot as plt

data = [
    {"time": "2024-06-01T00:00:00", "NumberOfData": 84},
    {"time": "2024-06-02T00:00:00", "NumberOfData": 81},
    {"time": "2024-06-03T00:00:00", "NumberOfData": 82},
    {"time": "2024-06-04T00:00:00", "NumberOfData": 84},
    {"time": "2024-06-05T00:00:00", "NumberOfData": 83},
    {"time": "2024-06-06T00:00:00", "NumberOfData": 80},
    {"time": "2024-06-07T00:00:00", "NumberOfData": 81},
    {"time": "2024-06-08T00:00:00", "NumberOfData": 82},
    {"time": "2024-06-09T00:00:00", "NumberOfData": 0},
    {"time": "2024-06-10T00:00:00", "NumberOfData": 0},
    {"time": "2024-06-11T00:00:00", "NumberOfData": 0},
    {"time": "2024-06-12T00:00:00", "NumberOfData": 0},
    {"time": "2024-06-13T00:00:00", "NumberOfData": 0},
    {"time": "2024-06-14T00:00:00", "NumberOfData": 80},
    {"time": "2024-06-15T00:00:00", "NumberOfData": 83},
    {"time": "2024-06-16T00:00:00", "NumberOfData": 85},
    {"time": "2024-06-17T00:00:00", "NumberOfData": 81},
    {"time": "2024-06-18T00:00:00", "NumberOfData": 0},
    {"time": "2024-06-19T00:00:00", "NumberOfData": 0},
    {"time": "2024-06-20T00:00:00", "NumberOfData": 83},
    {"time": "2024-06-21T00:00:00", "NumberOfData": 85},
    {"time": "2024-06-22T00:00:00", "NumberOfData": 82},
    {"time": "2024-06-23T00:00:00", "NumberOfData": 84},
    {"time": "2024-06-24T00:00:00", "NumberOfData": 80},
    {"time": "2024-06-25T00:00:00", "NumberOfData": 0},
    {"time": "2024-06-26T00:00:00", "NumberOfData": 0},
    {"time": "2024-06-27T00:00:00", "NumberOfData": 81},
    {"time": "2024-06-28T00:00:00", "NumberOfData": 84},
    {"time": "2024-06-29T00:00:00", "NumberOfData": 82},
    {"time": "2024-06-30T00:00:00", "NumberOfData": 80},
    {"time": "2024-07-01T00:00:00", "NumberOfData": 85},
    {"time": "2024-07-02T00:00:00", "NumberOfData": 0},
    {"time": "2024-07-03T00:00:00", "NumberOfData": 82},
    {"time": "2024-07-04T00:00:00", "NumberOfData": 80},
    {"time": "2024-07-05T00:00:00", "NumberOfData": 83},
    {"time": "2024-07-06T00:00:00", "NumberOfData": 0},
    {"time": "2024-07-07T00:00:00", "NumberOfData": 81},
    {"time": "2024-07-08T00:00:00", "NumberOfData": 82},
    {"time": "2024-07-09T00:00:00", "NumberOfData": 80},
    {"time": "2024-07-10T00:00:00", "NumberOfData": 84},
    {"time": "2024-07-11T00:00:00", "NumberOfData": 0},
    {"time": "2024-07-12T00:00:00", "NumberOfData": 0},
    {"time": "2024-07-13T00:00:00", "NumberOfData": 81},
    {"time": "2024-07-14T00:00:00", "NumberOfData": 84},
    {"time": "2024-07-15T00:00:00", "NumberOfData": 82},
    {"time": "2024-07-16T00:00:00", "NumberOfData": 80},
    {"time": "2024-07-17T00:00:00", "NumberOfData": 85},
    {"time": "2024-07-18T00:00:00", "NumberOfData": 0},
    {"time": "2024-07-19T00:00:00", "NumberOfData": 0},
    {"time": "2024-07-20T00:00:00", "NumberOfData": 83},
    {"time": "2024-07-21T00:00:00", "NumberOfData": 81},
    {"time": "2024-07-22T00:00:00", "NumberOfData": 82},
    {"time": "2024-07-23T00:00:00", "NumberOfData": 80},
    {"time": "2024-07-24T00:00:00", "NumberOfData": 84},
    {"time": "2024-07-25T00:00:00", "NumberOfData": 85},
    {"time": "2024-07-26T00:00:00", "NumberOfData": 83},
    {"time": "2024-07-27T00:00:00", "NumberOfData": 81},
    {"time": "2024-07-28T00:00:00", "NumberOfData": 82},
    {"time": "2024-07-29T00:00:00", "NumberOfData": 0},
    {"time": "2024-07-30T00:00:00", "NumberOfData": 0},
    {"time": "2024-07-31T00:00:00", "NumberOfData": 80},
    {"time": "2024-08-01T00:00:00", "NumberOfData": 84},
    {"time": "2024-08-02T00:00:00", "NumberOfData": 81},
    {"time": "2024-08-03T00:00:00", "NumberOfData": 82},
    {"time": "2024-08-04T00:00:00", "NumberOfData": 85},
    {"time": "2024-08-05T00:00:00", "NumberOfData": 83},
    {"time": "2024-08-06T00:00:00", "NumberOfData": 0},
    {"time": "2024-08-07T00:00:00", "NumberOfData": 0},
    {"time": "2024-08-08T00:00:00", "NumberOfData": 81},
    {"time": "2024-08-09T00:00:00", "NumberOfData": 82},
    {"time": "2024-08-10T00:00:00", "NumberOfData": 80},
    {"time": "2024-08-11T00:00:00", "NumberOfData": 84},
    {"time": "2024-08-12T00:00:00", "NumberOfData": 85},
    {"time": "2024-08-13T00:00:00", "NumberOfData": 83},
    {"time": "2024-08-14T00:00:00", "NumberOfData": 81},
    {"time": "2024-08-15T00:00:00", "NumberOfData": 82},
    {"time": "2024-08-16T00:00:00", "NumberOfData": 0},
    {"time": "2024-08-17T00:00:00", "NumberOfData": 0},
    {"time": "2024-08-18T00:00:00", "NumberOfData": 80},
    {"time": "2024-08-19T00:00:00", "NumberOfData": 84},
    {"time": "2024-08-20T00:00:00", "NumberOfData": 81},
    {"time": "2024-08-21T00:00:00", "NumberOfData": 82},
    {"time": "2024-08-22T00:00:00", "NumberOfData": 85},
    {"time": "2024-08-23T00:00:00", "NumberOfData": 83},
    {"time": "2024-08-24T00:00:00", "NumberOfData": 81},
    {"time": "2024-08-25T00:00:00", "NumberOfData": 82},
    {"time": "2024-08-26T00:00:00", "NumberOfData": 80},
    {"time": "2024-08-27T00:00:00", "NumberOfData": 84},
    {"time": "2024-08-28T00:00:00", "NumberOfData": 85},
    {"time": "2024-08-29T00:00:00", "NumberOfData": 0},
    {"time": "2024-08-30T00:00:00", "NumberOfData": 0},
    {"time": "2024-08-31T00:00:00", "NumberOfData": 81},
    {"time": "2024-09-01T00:00:00", "NumberOfData": 82},
    {"time": "2024-09-02T00:00:00", "NumberOfData": 80},
    {"time": "2024-09-03T00:00:00", "NumberOfData": 84},
    {"time": "2024-09-04T00:00:00", "NumberOfData": 85},
    {"time": "2024-09-05T00:00:00", "NumberOfData": 83},
    {"time": "2024-09-06T00:00:00", "NumberOfData": 81},
    {"time": "2024-09-07T00:00:00", "NumberOfData": 82},
    {"time": "2024-09-08T00:00:00", "NumberOfData": 0},
    {"time": "2024-09-09T00:00:00", "NumberOfData": 0},
    {"time": "2024-09-10T00:00:00", "NumberOfData": 80},
    {"time": "2024-09-11T00:00:00", "NumberOfData": 84},
    {"time": "2024-09-12T00:00:00", "NumberOfData": 85},
    {"time": "2024-09-13T00:00:00", "NumberOfData": 83},
    {"time": "2024-09-14T00:00:00", "NumberOfData": 81},
    {"time": "2024-09-15T00:00:00", "NumberOfData": 82},
    {"time": "2024-09-16T00:00:00", "NumberOfData": 80},
    {"time": "2024-09-17T00:00:00", "NumberOfData": 84},
    {"time": "2024-09-18T00:00:00", "NumberOfData": 85},
    {"time": "2024-09-19T00:00:00", "NumberOfData": 83},
    {"time": "2024-09-20T00:00:00", "NumberOfData": 81},
    {"time": "2024-09-21T00:00:00", "NumberOfData": 82},
    {"time": "2024-09-22T00:00:00", "NumberOfData": 0},
    {"time": "2024-09-23T00:00:00", "NumberOfData": 0},
    {"time": "2024-09-24T00:00:00", "NumberOfData": 80},
    {"time": "2024-09-25T00:00:00", "NumberOfData": 84},
    {"time": "2024-09-26T00:00:00", "NumberOfData": 85},
    {"time": "2024-09-27T00:00:00", "NumberOfData": 83},
    {"time": "2024-09-28T00:00:00", "NumberOfData": 81},
    {"time": "2024-09-29T00:00:00", "NumberOfData": 82},
    {"time": "2024-09-30T00:00:00", "NumberOfData": 80},
     {"time": "2024-10-01T00:00:00", "NumberOfData": 84},
    {"time": "2024-10-02T00:00:00", "NumberOfData": 85},
    {"time": "2024-10-03T00:00:00", "NumberOfData": 83},
    {"time": "2024-10-04T00:00:00", "NumberOfData": 81},
    {"time": "2024-10-05T00:00:00", "NumberOfData": 82},
    {"time": "2024-10-06T00:00:00", "NumberOfData": 0},
    {"time": "2024-10-07T00:00:00", "NumberOfData": 0},
    {"time": "2024-10-08T00:00:00", "NumberOfData": 80},
    {"time": "2024-10-09T00:00:00", "NumberOfData": 84},
    {"time": "2024-10-10T00:00:00", "NumberOfData": 85},
    {"time": "2024-10-11T00:00:00", "NumberOfData": 83},
    {"time": "2024-10-12T00:00:00", "NumberOfData": 81},
    {"time": "2024-10-13T00:00:00", "NumberOfData": 82},
    {"time": "2024-10-14T00:00:00", "NumberOfData": 0},
    {"time": "2024-10-15T00:00:00", "NumberOfData": 0},
    {"time": "2024-10-16T00:00:00", "NumberOfData": 80},
    {"time": "2024-10-17T00:00:00", "NumberOfData": 84},
    {"time": "2024-10-18T00:00:00", "NumberOfData": 85},
    {"time": "2024-10-19T00:00:00", "NumberOfData": 83},
    {"time": "2024-10-20T00:00:00", "NumberOfData": 81},
    {"time": "2024-10-21T00:00:00", "NumberOfData": 82},
    {"time": "2024-10-22T00:00:00", "NumberOfData": 80},
    {"time": "2024-10-23T00:00:00", "NumberOfData": 84},
    {"time": "2024-10-24T00:00:00", "NumberOfData": 85},
    {"time": "2024-10-25T00:00:00", "NumberOfData": 83},
    {"time": "2024-10-26T00:00:00", "NumberOfData": 81},
    {"time": "2024-10-27T00:00:00", "NumberOfData": 82},
    {"time": "2024-10-28T00:00:00", "NumberOfData": 0},
    {"time": "2024-10-29T00:00:00", "NumberOfData": 0},
    {"time": "2024-10-30T00:00:00", "NumberOfData": 80},
    {"time": "2024-10-31T00:00:00", "NumberOfData": 84},
    {"time": "2024-11-01T00:00:00", "NumberOfData": 85},
    {"time": "2024-11-02T00:00:00", "NumberOfData": 83},
    {"time": "2024-11-03T00:00:00", "NumberOfData": 81},
    {"time": "2024-11-04T00:00:00", "NumberOfData": 82},
    {"time": "2024-11-05T00:00:00", "NumberOfData": 80},
    {"time": "2024-11-06T00:00:00", "NumberOfData": 84},
    {"time": "2024-11-07T00:00:00", "NumberOfData": 85},
    {"time": "2024-11-08T00:00:00", "NumberOfData": 83},
    {"time": "2024-11-09T00:00:00", "NumberOfData": 81},
    {"time": "2024-11-10T00:00:00", "NumberOfData": 82},
    {"time": "2024-11-11T00:00:00", "NumberOfData": 81},
    {"time": "2024-11-12T00:00:00", "NumberOfData": 85},
    {"time": "2024-11-13T00:00:00", "NumberOfData": 80},
    {"time": "2024-11-14T00:00:00", "NumberOfData": 84},
    {"time": "2024-11-15T00:00:00", "NumberOfData": 85},
    {"time": "2024-11-16T00:00:00", "NumberOfData": 83},
    {"time": "2024-11-17T00:00:00", "NumberOfData": 81},
    {"time": "2024-11-18T00:00:00", "NumberOfData": 82},
    {"time": "2024-11-19T00:00:00", "NumberOfData": 80},
    {"time": "2024-11-20T00:00:00", "NumberOfData": 84},
    {"time": "2024-11-21T00:00:00", "NumberOfData": 85},
    {"time": "2024-11-22T00:00:00", "NumberOfData": 83},
    {"time": "2024-11-23T00:00:00", "NumberOfData": 81},
    {"time": "2024-11-24T00:00:00", "NumberOfData": 82},
    {"time": "2024-11-25T00:00:00", "NumberOfData": 80},
    {"time": "2024-11-26T00:00:00", "NumberOfData": 84},
    {"time": "2024-11-27T00:00:00", "NumberOfData": 85},
    {"time": "2024-11-28T00:00:00", "NumberOfData": 83},
    {"time": "2024-11-29T00:00:00", "NumberOfData": 81},
    {"time": "2024-11-30T00:00:00", "NumberOfData": 82},
    {"time": "2024-12-01T00:00:00", "NumberOfData": 80},
    {"time": "2024-12-02T00:00:00", "NumberOfData": 84},
    {"time": "2024-12-03T00:00:00", "NumberOfData": 85},
    {"time": "2024-12-04T00:00:00", "NumberOfData": 83},
    {"time": "2024-12-05T00:00:00", "NumberOfData": 81},
    {"time": "2024-12-06T00:00:00", "NumberOfData": 82},
    {"time": "2024-12-07T00:00:00", "NumberOfData": 0},
    {"time": "2024-12-08T00:00:00", "NumberOfData": 0},
    {"time": "2024-12-09T00:00:00", "NumberOfData": 80},
    {"time": "2024-12-10T00:00:00", "NumberOfData": 84},
    {"time": "2024-12-11T00:00:00", "NumberOfData": 85},
    {"time": "2024-12-12T00:00:00", "NumberOfData": 83},
    {"time": "2024-12-13T00:00:00", "NumberOfData": 81},
    {"time": "2024-12-14T00:00:00", "NumberOfData": 82},
    {"time": "2024-12-15T00:00:00", "NumberOfData": 80},
    {"time": "2024-12-16T00:00:00", "NumberOfData": 84},
    {"time": "2024-12-17T00:00:00", "NumberOfData": 0},
    {"time": "2024-12-18T00:00:00", "NumberOfData": 0},
    {"time": "2024-12-19T00:00:00", "NumberOfData": 0},
    {"time": "2024-12-20T00:00:00", "NumberOfData": 0},
    {"time": "2024-12-21T00:00:00", "NumberOfData": 0},
    {"time": "2024-12-22T00:00:00", "NumberOfData": 0},
    {"time": "2024-12-23T00:00:00", "NumberOfData": 0},
    {"time": "2024-12-24T00:00:00", "NumberOfData": 0},
    {"time": "2024-12-25T00:00:00", "NumberOfData": 0},
    {"time": "2024-12-26T00:00:00", "NumberOfData": 0},
    {"time": "2024-12-27T00:00:00", "NumberOfData": 0},
    {"time": "2024-12-28T00:00:00", "NumberOfData": 0},
    {"time": "2024-12-29T00:00:00", "NumberOfData": 0},
    {"time": "2024-12-30T00:00:00", "NumberOfData": 0},
    {"time": "2024-12-31T00:00:00", "NumberOfData": 0}
]

def plot1():
    df = pd.DataFrame(data)

    # Convert the 'time' column to datetime
    df['time'] = pd.to_datetime(df['time'])

    # Identify zero data days
    zero_days = df[df['NumberOfData'] == 0].copy()
    print(zero_days)
    # Find sequences of zero days
    zero_days['group'] = (zero_days['time'] - zero_days['time'].shift(1) > pd.Timedelta('1 day')).cumsum()
    sequences = zero_days.groupby('group').agg({'time': ['first', 'last']}).reset_index()
    sequences.columns = ['group', 'start_date', 'end_date']

    # Prepare for plotting
    plt.figure(figsize=(10, 5))
    plt.plot(df['time'], df['NumberOfData'], label='Number of Data', marker='o')
    plt.xlabel('Date')
    plt.ylabel('Number of Data')
    plt.title('Number of Data Over Time')

    # Highlight zero data periods
    for _, row in sequences.iterrows():
        plt.axvspan(row['start_date'], row['end_date'], color='red', alpha=0.3)

    plt.legend()
    plt.grid(True)
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.show()

def plot2():
    df = pd.DataFrame(data)

    # Converter 'time' para datetime e extrair o mês
    df['time'] = pd.to_datetime(df['time'])
    df['month'] = df['time'].dt.to_period('M')

    # Agrupar por mês e somar dias sem dados
    monthly_loss = df[df['NumberOfData'] == 0].groupby('month').size().reset_index(name='DaysWithNoData')

    # Gerar a regressão linear para a tendência
    X = np.array(monthly_loss.index).reshape(-1, 1)  # Índice do mês como variável independente
    y = monthly_loss['DaysWithNoData'].values  # Dias sem dados como variável dependente

    model = LinearRegression()
    model.fit(X, y)

    # Previsão de tendência
    trend = model.predict(X)

    # Plotar o gráfico
    plt.plot(monthly_loss['month'].astype(str), monthly_loss['DaysWithNoData'], label='Dias sem dados')
    plt.plot(monthly_loss['month'].astype(str), trend, label='Tendência', linestyle='--')
    plt.xlabel('Mês')
    plt.ylabel('Dias sem dados')
    plt.title('Tendência de Perda de Dados ao Longo do Tempo')
    plt.xticks(rotation=45)
    plt.legend()
    plt.tight_layout()
    plt.show()

plot2()