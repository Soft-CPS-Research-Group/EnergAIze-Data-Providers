import threading
import requests
import time
import datetime
import os
from data import DataSet
from cwlogin import CWLogin
from CWTranslator import CWTranslator

# Load configurations
configurations = DataSet.get_schema(os.path.join('..', 'runtimeConfigurations.json'))

class CWReceiver(threading.Thread):
    def __init__(self, house_name, tags_list, connection_params):
        threading.Thread.__init__(self)
        self._house = house_name
        self._tags_list = tags_list

        self._stop_event = threading.Event()
        self._connection_params = connection_params

    def stop(self):
        self._stop_event.set()

    def _job(self):
        for tag in self._tags_list:
            try:
                lastvalue_url = f"{self._connection_params}{tag.get('id')}"
                response = requests.get(lastvalue_url, headers=self._header)
                if response.status_code == 200:               
                    CWTranslator.translate(self._house, response.json())
            except Exception as e:
                print(f"Error processing tag {tag.get('id')}: {e}")
            
    def _login(self):
        try: 
            token = CWLogin.login() 
        except Exception as e:
            print(e)
            exit()
        self._header = {'Authorization': f"CW {token}"}
        self._session_time = datetime.datetime.now().timestamp()


    def run(self):
        # Calculate the time between each data request
        timesleep = DataSet.calculate_interval(configurations.get('frequency'))
        # Login to the server
        self._login()
        
        while not self._stop_event.is_set():
            # Check if the session has expired
            if (datetime.datetime.now().timestamp() - self._session_time) >= 3599:
                # If it has, login again
                self._login()
            self._job()
            time.sleep(timesleep)


def main():
    print("Starting CWReceiver...")
    # Get connection parameters
    connection_params = configurations.get('CWserver')
    # Get CW Houses file and turn it into a dictionary
    CWHouses = DataSet.get_schema(os.path.join('..', configurations.get('CWfile').get('path')))
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
