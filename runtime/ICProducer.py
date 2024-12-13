import pika
import datetime
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
    def __init__(self, house, devices_list, users_list, connection_params):
        threading.Thread.__init__(self)
        self._users_list = users_list
        self._devices_list = devices_list
        self._house = house
        self._connection_params = pika.ConnectionParameters(host=connection_params.get('host'), port=connection_params.get('port'),heartbeat=660)
        self._connection = None
        self._channel = None
        self._stop_event = threading.Event()
        self._max_reconnect_attempts = configurations.get('maxReconnectAttempts')


    def stop(self):
        print(f"Stopping thread {self._house}...")
        self._stop_event.set()
        self._channel.close()
        self._connection.close()
        print(f"Thread {self._house} stopped.")

    def connect(self):
        self._connection = pika.BlockingConnection(self._connection_params)
        self._channel = self._connection.channel()
        self._channel.exchange_declare(exchange=self._house, exchange_type='fanout')

    def run(self):
        
        reconnect_attempts = 0
        # Calculate the time between each data request
        timesleep = DataSet.calculate_interval(configurations.get('frequency'))        
        while not self._stop_event.is_set() and reconnect_attempts < self._max_reconnect_attempts:
            message_devices = []
            try: 
                self.connect()    
                while not self._stop_event.is_set():
                    for device in self._devices_list:
                        if device.get('label') == "ChargersSession":
                            userID = random.choice(self._users_list)
                            devicedata = {
                                    "id": random.randint(1, 1000),
                                    "serialnumber": device.get('serialNumber'),
                                    "user.id": userID,
                                    "card.id": "xxxx",
                                    "plug": device.get('plug'),
                                    "soc": random.randint(1, 100),
                                    "power": random.randint(1, 100)
                                }
                            message_devices.append(devicedata)

                        message = {
                                "time": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                                "battery.soc": random.randint(1, 100),
                                "pv.production": random.randint(1, 100),
                                "charging.session": message_devices,
                                "meter.values": [
                                    {
                                        "id": "PT",
                                        "l123": random.randint(0, 10)
                                    }
                                ] 
                            }
                    print(f"House: {self._house} {json.dumps(message, indent=2)}")
                    message_bytes = json.dumps(message).encode('utf-8')    
                    self._channel.basic_publish(exchange=self._house, routing_key='', body=message_bytes)
                    message_devices.clear()
                    time.sleep(timesleep) 
            except pika.exceptions.AMQPConnectionError: 
                reconnect_attempts += 1
                print(f"Thread {self._house} lost connection, attempting to reconnect...")
                time.sleep(5)  # Wait before attempting to reconnect
            except Exception as e:
                print(f"Thread {self._house} encountered an error: {e}")
                break
        
        if reconnect_attempts >= self._max_reconnect_attempts:
            print(f"Thread {self._house} reached maximum reconnection attempts. Stopping thread.")

    

def main():
    print("Starting ICProducer...")
    # Get connection parameters
    connection_params = configurations.get('ICserver')
    # Get CW Houses file and turn it into a dictionary
    ICHouses = DataSet.get_schema(os.path.join('..', configurations.get('ICfile').get('path')))
    # Get Users file and turn it into a dictionary
    users = DataSet.get_schema(os.path.join('..', configurations.get('Users').get('path')))
    # Remove provider key because it does not contain any useful information here
    ICHouses.pop('provider')
    
    threads = []
    
    try:
        for house in ICHouses.keys():
            users_list = list(users[house].keys())
            devices_list = ICHouses[house]
            producer_thread = ProducerThread(house, devices_list, users_list, connection_params)
            producer_thread.start()
            threads.append(producer_thread)

   
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
