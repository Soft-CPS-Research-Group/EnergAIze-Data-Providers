import pika
import os
import threading
import time
import sys
from pydoc import locate
from data import DataSet
from IManager import IManager

# Load configurations
configurations = DataSet.get_schema(os.path.join('..', 'runtimeConfigurations.json'))

class DataReceiver(threading.Thread):
    def __init__(self, house, devices, connection_params, manager_class: IManager, suffix):
        threading.Thread.__init__(self)
        self._house = house
        self._manager = manager_class(devices, house)
        self._suffix = suffix
        self._connection_params = pika.ConnectionParameters(host=connection_params.get('host'), port=connection_params.get('port'),heartbeat=660)
        self._connection = None
        self._channel = None
        self._stop_event = threading.Event()
        self._max_reconnect_attempts = 3

    def stop(self):
        self._manager.stop()
        self._stop_event.set()
        self._channel.stop_consuming()
        self._channel.close()
        self._connection.close()
        print(f"Thread {self._house} stopped.")

    def connect(self):
        self._connection = pika.BlockingConnection(self._connection_params)
        self._channel = self._connection.channel()
        queue_name = self._house + self._suffix
        self._channel.queue_declare(queue_name, durable=True)
        self._channel.basic_consume(queue=queue_name, on_message_callback=self._manager.newMessage, auto_ack=True)

    def run(self):
        error = False
        reconnect_attempts = 0
        while not self._stop_event.is_set() and reconnect_attempts < self._max_reconnect_attempts:
            try:
                self.connect()
                print(f"Thread {self._house} connected and consuming.")
                while not self._stop_event.is_set():
                    self._channel.connection.process_data_events(time_limit=1)  # Process events with a timeout
            except pika.exceptions.AMQPConnectionError:
                reconnect_attempts += 1
                print(f"Thread {self._house} lost connection, attempting to reconnect...")
                time.sleep(5)  # Wait before attempting to reconnect
                if reconnect_attempts >= self._max_reconnect_attempts:
                    print(f"Thread {self._house} reached maximum reconnection attempts. Stopping thread.")
                    error = True
            except Exception as e:
                print(f"Thread {self._house} encountered an error: {e}")
                error = True
                break

        if error:
            self._manager.stop()
            

def main(manager):
    managerClass = locate(manager)
    managerClassName = managerClass.__name__
    suffix = configurations['QueueSuffixes'].get(managerClassName)
    
    print(f"Starting Data Receiver... ({managerClassName})")
    connection_params = configurations['internalAMQPServer']
    
    houses = {}
    DataSet.process_json_files_in_folder(os.path.join('..', 'house_files/without_type/test4'), houses)
    threads = []
    try:
        for house in houses.keys():
            accumulator_thread = DataReceiver(house, houses[house], connection_params, managerClass, suffix)
            accumulator_thread.start()
            threads.append(accumulator_thread)

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
    if len(sys.argv) != 2:
        sys.exit(1)
    
    manager = sys.argv[1]
   
    main(manager)
