import paho.mqtt.client as mqtt
import threading
import time
import random
import json
import os
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from data import DataSet

# Load configurations
configurations = DataSet.get_schema(os.path.join('..', 'runtimeConfigurations.json'))

class ProducerThread(threading.Thread):
    def __init__(self, cars, connection_params, clientName):
        threading.Thread.__init__(self)
        self._cars = cars
        self._connection_params = connection_params
        self._client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION1, clientName)
        self._stop_event = threading.Event()
        self._max_reconnect_attempts = configurations.get('maxReconnectAttempts')


    def stop(self):
        print(f"Stopping thread...")
        self._stop_event.set()
        self._client.disconnect()
        print(f"Thread stopped.")

    def connect(self):
        try:
            self._client.connect(self._connection_params.get('host'))
        except Exception as e:
            print(f"Failed to connect to broker: {e}")
            raise


    def run(self):
        reconnect_attempts = 0
        timesleep = 10      
        while not self._stop_event.is_set() and reconnect_attempts < self._max_reconnect_attempts:
            try: 
                self.connect()    
                while not self._stop_event.is_set():
                    for car in self._cars:
                        car_id = car.get('id')
                        battery_level = random.uniform(20.0, 100.0)  # Simulated battery level
                        topic = f"{car_id}/soc"
                        payload = json.dumps({"State of Charge": battery_level})
                        self._client.publish(topic, payload)
                        print(f"Published {payload} to {topic}")
                    time.sleep(timesleep)
            except Exception as e:
                print(f"Exception occurred: {e}")
                reconnect_attempts += 1
                time.sleep(2 ** reconnect_attempts)  # Exponential backoff
                if reconnect_attempts >= self._max_reconnect_attempts:
                    print("Max reconnect attempts reached, stopping thread.")
                    self._stop_event.set()
            
    

def main():
    print("Starting ICProducer...")
    # Get connection parameters
    connection_params = configurations.get('CarSpecsserver')
    # Get CW Houses file and turn it into a dictionary
    cars = DataSet.get_schema(os.path.join('..', configurations.get('Cars').get('path')))
     
    
    try:
        producer_thread = ProducerThread(cars, connection_params, "SOCProducer")
        producer_thread.start()

        while producer_thread.is_alive():
            time.sleep(0.1)

    except KeyboardInterrupt:
        print("KeyboardInterrupt: Stopping thread...")

        producer_thread.stop()

        print("Thread stopped.")

if __name__ == "__main__":
    main()
