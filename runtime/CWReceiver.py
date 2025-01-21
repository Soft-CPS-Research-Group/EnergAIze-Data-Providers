from threading import Thread, Timer, Event
import requests
import time
import datetime
import os
import sys
from CWTranslator import CWTranslator
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from data import DataSet
from cwlogin import CWLogin


# Load configurations
configurations = DataSet.get_schema(os.path.join('..', 'runtimeConfigurations.json'))

class CWReceiver(Thread):
    def __init__(self, house_name, tags_list, connection_params):
        Thread.__init__(self)
        self._house = house_name
        self._tags_list = tags_list

        self._time_interval = DataSet.calculate_interval(configurations.get('frequency'))
        self._connection_params = connection_params
        self._stop_event = Event()
        self._session_time = 0

    def stop(self):
        self._stop_event.set()
        self._timer.cancel()

    def _job(self):
        from_time = (datetime.datetime.now() - datetime.timedelta(seconds=self._time_interval)).isoformat()
        if not self._stop_event.is_set():

            if datetime.datetime.now().timestamp() - self._session_time > 3599:
                self._login()

            for tag in self._tags_list:
                try:
                    #url = f"{self._connection_params}{tag.get('id')}&from={from_time}"
                    url = f"https://ks.innov.cleanwatts.energy/api/2.0/data/lastvalue/Instant?from=2003-06-11&tags={tag.get('id')}"
                    response = requests.get(url, headers=self._header)
                    if response.status_code == 200:               
                        CWTranslator.translate(self._house, response.json())
                except Exception as e:
                    print(f"Error processing tag {tag.get('id')}: {e}")
            
            self._start_timer()
            
    def _login(self):
        try: 
            token = CWLogin.login() 
        except Exception as e:
            print(e)
            exit()
        self._header = {'Authorization': f"CW {token}"}
        self._session_time = datetime.datetime.now().timestamp()

    def _start_timer(self):
        self._timer=Timer(self._time_interval,self._job) 
        self._timer.start()

    def run(self):
        self._job()


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
