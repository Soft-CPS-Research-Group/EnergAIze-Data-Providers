from threading import Thread, Event
from apscheduler.schedulers.background import BlockingScheduler
import requests
import time
import datetime
from runtime.CWTranslator import CWTranslator
from utils.data import DataSet
from utils.config_loader import load_configurations
from utils.cwlogin import CWLogin

# Load configurations
configurations, logger = load_configurations('./configs/runtimeConfigurations.json',"cleanwatts")
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
        print(f"Job Execution Time: {datetime.datetime.now()} House: {self._house}")
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
                    logger.info(f"CWReceiver: Tag {tag.get('id')} successfully retrieved!")
                    CWTranslator.translate(self._house, response.json())
                else:
                    logger.warning(f"CWReceiver: Error getting data from tag {tag.get('id')}: {response.status_code}")
            except requests.exceptions.Timeout:
                logger.error("CWReceiver: Connection timeout.")
            except requests.exceptions.ConnectionError as e:
                logger.error(f"CWReceiver: {e}")
            except requests.exceptions.RequestException as e:
                logger.error(f"CWReceiver: Unexpected error - {e}")

            
    def _login(self):
        try: 
            token = CWLogin.login() 
        except Exception as e:
            print(e)
            exit()
        self._header = {'Authorization': f"CW {token}"}
        if token is not None:
            self._session_time = datetime.datetime.now().timestamp()

    def run(self):
        self._scheduler = BlockingScheduler()
        self._scheduler.add_job(self._job, 'interval', seconds=self._time_interval, misfire_grace_time=10, coalesce=True)

        self._job()
        self._scheduler.start()


def main():
    logger.info("Starting CWReceiver...")
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
