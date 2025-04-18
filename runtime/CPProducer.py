import paho.mqtt.client as mqtt
import threading
import time
import random
import json
from utils.data import DataSet

# Load configurations
configurations = DataSet.get_schema('./configs/runtimeConfigurations.json')

class ProducerThread(threading.Thread):
    def __init__(self, house_name, cars_list, connection_params):
        threading.Thread.__init__(self)
        self._cars_list = cars_list
        self._connection_params = connection_params
        self._client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
        self._stop_event = threading.Event()
        self._max_reconnect_attempts = configurations.get('maxReconnectAttempts')

        self._time_sleep = DataSet.calculate_interval(configurations.get('frequency'))      



    def stop(self):
        print(f"Stopping thread...")
        self._stop_event.set()
        self._client.disconnect()
        print(f"Thread stopped.")

    def connect(self):
        try:
            self._client.connect(self._connection_params.get('host'),self._connection_params.get('port'),self._time_sleep+20)
        except Exception as e:
            print(f"Failed to connect to broker: {e}")
            raise


    def run(self):
        reconnect_attempts = 0
        while not self._stop_event.is_set() and reconnect_attempts < self._max_reconnect_attempts:
            try: 
                self.connect()    
                while not self._stop_event.is_set():
                    for car in self._cars_list:
                        car_id = car.get('id')
                        battery_level = random.uniform(20.0, 100.0)  # Simulated battery level
                        latitude = random.uniform(-90.0, 90.0)
                        longitude = random.uniform(-180.0, 180.0)
                        topic = f"{car_id}/data"
                        payload = json.dumps({"stateOfCharge": battery_level,
                                              "coordinates": {"latitude": latitude, "longitude": longitude},
                                              "vin": car_id})
                        
                        self._client.publish(topic, payload)
                        print(f"Published {payload} to {topic}")
                    time.sleep(self._time_sleep)
            except Exception as e:
                print(f"Exception occurred: {e}")
                reconnect_attempts += 1
                time.sleep(2 ** reconnect_attempts)  # Exponential backoff
                if reconnect_attempts >= self._max_reconnect_attempts:
                    print("Max reconnect attempts reached, stopping thread.")
                    self._stop_event.set()
            
    

def main():
    print("Starting CPProducer...")
   # Get connection parameters
    connection_params = configurations.get('CPserver')
    # Get CW Houses file and turn it into a dictionary
    CPHouses = DataSet.get_schema(configurations.get('CPfile').get('path'))
    
    CPHouses.pop('provider')
    
    threads = []

    try:
        for house in CPHouses.keys():
            cars_list = CPHouses[house]
            receiver_thread = ProducerThread(house, cars_list, connection_params)
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
