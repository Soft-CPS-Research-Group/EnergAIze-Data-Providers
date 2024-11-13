from datetime import datetime
import threading
import os
import sys
import requests
import time
from CWHistoricDataTranslator import CWHistoricDataTranslator
from CWPriceDataTranslatorAndManager import CWPriceDataTranslatorAndManager
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from data import DataSet
from cwlogin import CWLogin

configurations = DataSet.get_schema(os.path.join('..', 'historicConfigurations.json'))

class CWHistoricDataRequest():
    def __init__(self, houses_list, connection_params, start_date, end_date, period, translator_class):
        self._connection_params = connection_params
        self._tag_dict = {}

        self._period = period
        self._start_date = start_date
        self._end_date = end_date
        self._translator_class = translator_class

        # Create a dictionary with the house and the tags that have label
        for house in houses_list.keys():
            for tag in houses_list.get(house):
                if 'label' in tag:
                    tagId = tag.get('id')
                    self._tag_dict[tagId] = house
        

    def login(self):
        token = CWLogin.login() 
        self._header = {'Authorization': f"CW {token}"}
        self._session_time = datetime.now().timestamp()

    def run(self):
        self.login()
        
        with requests.Session() as session:
            session.headers.update(self._header)  

            # Get the data for each tag
            for tagId in self._tag_dict.keys():
                
                if (datetime.now().timestamp() - self._session_time) >= 3599:
                    self.login()
                    session.headers.update(self._header) 

                url = f"{self._connection_params}&tags={tagId}&from={self._start_date.strftime('%Y-%m-%d')}"
                
                try:
                    response = session.get(url, timeout=100)
                except requests.exceptions.RequestException as e:
                    print(f"Error: {e}")
                    sys.exit(1)

                if response.status_code == 200:
                    data = response.json()
                    if data:
                        print(f"Data received for tag {tagId}. The translation will start.")
                    else:
                        print(f"The {tagId} tag has no content in the dates passed by parameter")

                    thread = threading.Thread(target=self._translator_class.translate, args=(tagId, data, self._tag_dict.get(tagId), self._start_date, self._end_date, self._period))
                    thread.start()
                else:
                    print(f"Error: {response.status_code} - {response.text}")

                time.sleep(1) # Sleep for 1 second to avoid the server blocking the requests
   
def main(start_date, end_date, period):
    print("Starting CWHistoricDataRequest...")

    connection_params = configurations.get('CWhistoricalServer')

    schema = DataSet.get_schema(os.path.join('..',configurations.get('CWfile').get('path')))
    schema.pop('provider')

    historicData = CWHistoricDataRequest(schema, connection_params, start_date, end_date, period, CWHistoricDataTranslator)
    historicData.run()

    priceData = CWHistoricDataRequest(configurations.get('ElectricityPrice'), connection_params, start_date, end_date, period, CWPriceDataTranslatorAndManager)
    priceData.run()

  
if __name__ == "__main__":
    if len(sys.argv) != 4:
        print("python CWHistoricDataRequest.py <start date> <end date> <period>")
        sys.exit(1)
    
    start_date = datetime.strptime(sys.argv[1], "%Y-%m-%dT%H:%M:%S%z")
    end_date = datetime.strptime(sys.argv[2], "%Y-%m-%dT%H:%M:%S%z")
    period = int(sys.argv[3])
    
    if start_date >= end_date:
        print("The start date must be before the end date.")
        sys.exit(1)
    
    main(start_date, end_date, period)