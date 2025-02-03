from threading import Thread, Event
from apscheduler.schedulers.background import BackgroundScheduler
import requests
import time
import datetime
from runtime.CWTranslator import CWTranslator
from utils.data import DataSet
from cwlogin import CWLogin


# Load configurations
configurations = DataSet.get_schema('./configs/runtimeConfigurations.json')

class CWReceiver(Thread):
    def __init__(self, house_name, tags_list, connection_params):
        Thread.__init__(self)
        self._house = house_name
        self._tags_list = tags_list

        self._time_interval = DataSet.calculate_interval(configurations.get('frequency'))
        self._connection_params = connection_params
        self._session_time = 0
        self._stop_event = Event()
        self._count = 0

    def stop(self):
        self._stop_event.set()
        self._scheduler.shutdown()

    def _job(self):
        #from_time = (datetime.datetime.now() - datetime.timedelta(seconds=self._time_interval)).isoformat()
        if datetime.datetime.now().timestamp() - self._session_time > 3000:
            self._login()
        for tag in self._tags_list:
            try:
                # I wanted to do only one request with all the tags, but if I do that and one of the tags is not available, all the tags are compromised
                #url = f"{self._connection_params}{tag.get('id')}&from={from_time}"
                url = f"https://ks.innov.cleanwatts.energy/api/2.0/data/lastvalue/Instant?from=2003-06-11&tags={tag.get('id')}"
                response = requests.get(url, headers=self._header)
                if response.status_code == 200:               
                    CWTranslator.translate(self._house, response.json())
                else:
                    print(f"Error getting data from tag {tag.get('id')}: {response.status_code}")
            except requests.exceptions.Timeout:
                print(f"Connection timeout.")

            except requests.exceptions.ConnectionError:
                print(f"No internet connection.")

            except requests.exceptions.RequestException as e:
                print(f"Unexpected error - {e}")
            
        
            
    def _login(self):
        try: 
            token = CWLogin.login() 
        except Exception as e:
            print(e)
            exit()
        self._header = {'Authorization': f"CW {token}"}
        self._session_time = datetime.datetime.now().timestamp()

    def run(self):
        self._scheduler = BackgroundScheduler()
        self._scheduler.add_job(self._job, 'interval', seconds=self._time_interval)  
        self._scheduler.start()

        self._job()
        self._stop_event.wait() 

    def _log(self):
        self._count+=1
        filename = "logs2.csv"
        timestamp = datetime.datetime.now()
        with open(filename, 'a') as file:
            file.write(f"{self._count}'s observation {timestamp}\n")

def main():
    print("Starting CWReceiver...")
    # Get connection parameters
    connection_params = configurations.get('CWserver')
    # Get CW Houses file and turn it into a dictionary
    CWHouses = DataSet.get_schema(configurations.get('CWfile').get('path'))
    # Remove provider key because it does not contain any useful information here
    CWHouses.pop('provider')
    
    threads = []

    try:
        for house in CWHouses.keys():
            tags_list = CWHouses[house]
            receiver_thread = CWReceiver(house, tags_list, connection_params)
            receiver_thread.start()
            threads.append(receiver_thread)

        # Check if threads are alive, if not, remove them from the list and if all of them are dead, stop the program
        while threads:
            for thread in threads:
                if not thread.is_alive():
                    threads.remove(thread)
                time.sleep(0.1)

    except KeyboardInterrupt:
        print("KeyboardInterrupt: Stopping threads...")
        for thread in threads:
            thread.stop()

        for thread in threads:
            thread.join()
        print("All threads stopped.")



if __name__ == "__main__":
    main()
