import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import requests
import csv
import numpy as np
from sklearn.linear_model import LinearRegression
import copy
import pandas as pd
import matplotlib.pyplot as plt
from dateutil import parser
from datetime import datetime, timedelta
from utils.cwlogin import CWLogin
from utils.data import DataSet

# Load configurations
configurations = DataSet.get_schema(os.path.join('..', 'historicConfigurations.json'))
# Get CW Houses file and turn it into a dictionary
CWHouses = DataSet.get_schema(os.path.join('..', configurations.get('CWfile').get('path')))

class DataProcesser():
    def __init__(self, time, unit, house):
        self._houseData = CWHouses.get(house, [])
        self._house = house
        self._unit = unit
        self._session_time = 0
        self._connection_params = configurations.get('CWhistoricalServer')
        self._date = "2022-01-01T00:00:00"
        self._allTags = {}

        self._toSeconds(time, unit)
        self._menu()

    def dataRequester(self, tag):
        # Check if the session has expired
        if (datetime.now().timestamp() - self._session_time) >= 3599:
                # If it has, login again
                self._login()
        url = f"{self._connection_params}&tags={tag}&from={self._date}"
        response = requests.get(url, headers=self._header)
        if response.status_code == 200:   
            return response.json()
        
    #este método funciona assumindo que os dados estão por ordem cronológica (do masi antigo para o mais recente)
    def loadData(self):
        dict = {}
        todaysDate = datetime.now()
        for tag in self._houseData:
            tagId = tag.get('id')
            fdate = None
            thereIsAlreadyData = False
            startDate = datetime.strptime(self._date, "%Y-%m-%dT%H:%M:%S")
            all_rows = []
            
            rdata = self.dataRequester(tagId)
            if rdata is not None:
                data = copy.deepcopy(rdata)
                if rdata is not None:
                    while todaysDate > startDate:
                        thereIsData = 0
                        if len(rdata) > 0:
                            # Remove timezone from `time` to make it a naive datetime
                            time = parser.isoparse(rdata[0].get('Date')).replace(tzinfo=None)
                            while time >= startDate and time < startDate + timedelta(seconds=self._time) and len(rdata) > 0:
                                dt = rdata.pop(0)
                                if not thereIsAlreadyData:
                                    fdate = dt.get('Date')
                                    thereIsAlreadyData = True
                                thereIsData+=1
                                if len(rdata) > 0:
                                    # Remove timezone from `time` to make it a naive datetime
                                    time = parser.isoparse(rdata[0].get('Date')).replace(tzinfo=None)
                        if thereIsAlreadyData:
                            dict = {"time" : startDate.strftime("%Y-%m-%dT%H:%M:%S"), "NumberOfData": thereIsData}
                            all_rows.append(dict)

                        startDate += timedelta(seconds=self._time)

                self._allTags[tagId] = {"Gap Frequency": all_rows, "First Date": fdate, "Data":data, "Tag": tag}
                
                    
                with open(tagId, mode='w', newline='') as file:
                    writer = csv.DictWriter(file, fieldnames=dict.keys())
                    writer.writeheader()
                    writer.writerows(all_rows)
    
    def percentageOfNonExistentData(self, tag): 
        gapFrequency = self._allTags[tag].get("Gap Frequency")  
        dataSize = len(gapFrequency)
        numberOfPeriodsWithoutData = 0
        for data in gapFrequency:
            if data["NumberOfData"] == 0:
                numberOfPeriodsWithoutData+=1

        percentage = (numberOfPeriodsWithoutData/dataSize)*100
        print(f"Percentage of Non Existent Data: {percentage}%")

    def linePlot(self, tag):
        data = self._allTags[tag].get("Gap Frequency")
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

        # Create folder if it doesn't exist
        folder_path = os.path.join(self._house, "totalData")
        print(folder_path)
        os.makedirs(folder_path, exist_ok=True)

        # Define file path and save the plot
        file_path = os.path.join(folder_path, f"{tag}.png")
        plt.savefig(file_path)
        print(f"Graph saved at: {file_path}")
    
    def monthLinePlot(self, tag):
        data = self._allTags[tag].get("Gap Frequency")  
        df = pd.DataFrame(data)

        # Convert the 'time' column to datetime
        df['time'] = pd.to_datetime(df['time'])

        # Criar uma coluna separada para o mês-ano
        df['year_month'] = df['time'].dt.to_period('M')


        # Criar uma pasta para salvar os gráficos
        folder_path = os.path.join(self._house, "monthData")        
        os.makedirs(folder_path, exist_ok=True)

        # Iterar sobre cada mês disponível nos dados
        for period, month_data in df.groupby('year_month'):
            # Identify zero data days
            zero_days = month_data[month_data['NumberOfData'] == 0].copy()
            
            # Find sequences of zero days
            zero_days['group'] = (zero_days['time'] - zero_days['time'].shift(1) > pd.Timedelta('1 day')).cumsum()

            # Prepare for plotting
            plt.figure(figsize=(10, 5))
            plt.plot(month_data['time'], month_data['NumberOfData'], label='Number of Data', marker='o')
            plt.xlabel('Date')
            plt.ylabel('Number of Data')
            plt.title('Number of Data Over Time')

            # Highlight zero data periods
            if not zero_days.empty:
                print(zero_days)
                sequences = zero_days.groupby('group').agg({'time': ['first', 'last']}).reset_index()
                sequences.columns = ['group', 'start_date', 'end_date']
                for _, row in sequences.iterrows():
                    plt.axvspan(row['start_date'], row['end_date'], color='red', alpha=0.3)
            else:
                print("No sequences of zero data days found for this period.")

            all_days = pd.date_range(start=month_data['time'].min(), end=month_data['time'].max(), freq='D')
            plt.xticks(all_days, all_days.strftime('%d'), rotation=45)
            plt.legend()
            plt.grid(True)
            plt.xticks(rotation=45)
            plt.tight_layout()

            # Create folder if it doesn't exist
            folder_path = os.path.join(self._house, "monthData", tag)
            print(folder_path)
            os.makedirs(folder_path, exist_ok=True)

            # Define file path and save the plot
            file_path = os.path.join(folder_path, f"{period}.png")
            plt.savefig(file_path)
            plt.close()
            print(f"Graph saved at: {file_path}")


    def averageGapTime(self, tag):
        data = self._allTags[tag].get("Gap Frequency")  
        gapSize = 0
        gapTime = 0
        itsGap = False
        for dic in data:
            if dic["NumberOfData"] == 0:
                gapTime+=self._time
                if not itsGap:
                    itsGap = True
                    gapSize+=1
            else:
                itsGap = False
        # gapSize*self._time é necessário porque em cada gap falta semopre adicionar uma vez o tempo
        averageGapTime = (gapTime+gapSize*self._time)/gapSize
        print(f"Number of Gaps: {gapSize}")
        print(f"Gap Time Average: {self._toUnit(averageGapTime)}")

    def longestSequence(self, tag):
        data = self._allTags[tag].get("Gap Frequency")  
        gapSize = 0
        longestGap = 0
        for dic in data:
            if dic["NumberOfData"] == 0:
                gapSize+=1
                if gapSize > longestGap:
                    longestGap = gapSize
            else:
                gapSize = 0

        print(f"Longest Gap: {self._toUnit((longestGap+1)*self._time)}")

    def dataLossTrend(self, tag):
        data = self._allTags[tag].get("Gap Frequency")  
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
        
    def _menu(self):
        print("Loading Data...")
        self.loadData()
        while True:
            self._menuOptions()
            option = input("Enter your choice: ")
            if option == "1":
                for tag in self._allTags:
                    self._tagInfo(tag)
                    self.linePlot(tag)
            elif option == "2":
                for tag in self._allTags:
                    self._tagInfo(tag)
                    self.percentageOfNonExistentData(tag)
            elif option == "3":
                for tag in self._allTags:
                    self._tagInfo(tag)
                    self.averageGapTime(tag)
            elif option == "4":
                for tag in self._allTags:
                    self._tagInfo(tag)
                    self.longestSequence(tag)
            elif option == "5":
                for tag in self._allTags:
                    self._tagInfo(tag)
                    self.dataLossTrend(tag)
            elif option == "6":
                for tag in self._allTags:
                    self._tagInfo(tag)
                    self.monthLinePlot(tag)
            elif option == "0":
                break
            else:
                print("Opção inválida. Por favor, insira uma opção válida.")
       
    def _menuOptions(self):  
        print("\n1) Generate frequency charts of missing records")
        print("2) Percentage of missing data")
        print(f"3) Average period of missing records in {self._unit} and number of periods with no data")
        print("4) Longest sequence without data")
        print("5) Data loss trend over time")
        print("6) Generate frequency charts of missing records by month")
        print("0) Exit")

    def _tagInfo(self, tag):
        tagInfo = self._allTags[tag].get("Tag")
        print(f"\nID: {tagInfo.get('id')}")
        print(f"Name: {tagInfo.get('name')}")
        print(f"Unit: {tagInfo.get('measurementunit')}")

    def _toSeconds(self, time, unit):
        self._time=time*60
        if unit == "hours":
            self._time*=60
        elif unit == "days":
            self._time*=60*24

    def _toUnit(self, time):
        if self._unit == "minutes":
            return time/60
        elif self._unit == "hours":
            return time/(60*60)
        elif self._unit == "days":
            return time/(60*60*24)
        
    def _login(self):
        try: 
            token = CWLogin.login() 
        except Exception as e:
            print(e)
            exit()
        self._header = {'Authorization': f"CW {token}"}
        self._session_time = datetime.now().timestamp()

       
def main():
    timeUnits = ["minutes", "hours", "days"] #POSSO METER ESTAS UNIDADES NAS CONFIGURAÇÕES
    # Loop until the user chooses a valid time unit
    print("Enter the time unit:")
    for i, tu in enumerate(timeUnits):
        print(f"{i + 1}) {tu}")

    while True:
        unit= input("Enter your choice: ")
        if unit.isdigit():
            unit = int(unit)  # Convert the string to an integer
            if 0 < unit <= len(timeUnits):
                unit = timeUnits[unit-1]
                break
        else:
            print("Invalid input. Please enter a valid number.")
    
    # Loop until the user inputs a valid number
    while True:
        time = input("Enter the period: ")
        if time.isdigit():
            time = int(time)  # Convert the string to an integer
            break  # Exit the loop if the number is valid
        else:
            print("Invalid input. Please enter a valid number.")

    # Remove provider key because it does not contain any useful information here
    CWHouses.pop('provider')
    
    houses = list(CWHouses.keys())

    print("Available houses:")
    for i, house in enumerate(houses):
        print(f"{i+ 1}) {house}")
    
    # Ask the user to enter one of the house names
    while True:
        house = input("Enter the name of one of the houses: ")
        if house.isdigit():
            house = int(house)  # Convert the string to an integer
            if 0 < house <= len(houses):
                house= houses[house-1]
                break
        else:
            print("Invalid house name. Please enter a valid house name.")
    
    print(f"\nThe data from installation {house} will be grouped in periods of {time} {unit}")

    DataProcesser(time, unit, house)
    

if __name__ == "__main__":
    main()
