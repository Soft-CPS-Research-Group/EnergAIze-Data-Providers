import pika
import os
import threading
import time
from training.HistoricDataManager import HistoricDataManager
from utils.data import DataSet
from utils.config_loader import load_configurations

configurations, logger = load_configurations('./configs/historicConfigurations.json',"accumulator")

class AcummulatorThread(threading.Thread):
    def __init__(self, house, house_specs, connection_params):
        threading.Thread.__init__(self)

        self._house = house
        self._connection_params = pika.ConnectionParameters(host=connection_params.get('host'), port=connection_params.get('port'),heartbeat=660)

        self._connection = None
        self._channel = None

        self._stop_event = threading.Event()
        self._manager = HistoricDataManager(house_specs,house,self._stop_event)

        self._max_reconnect_attempts = configurations.get('maxReconnectAttempts')
    
    def stop(self):
        self._stop_event.set()
        print(f"Thread {self._house} stopped.")

    def connect(self):
        self._connection = pika.BlockingConnection(self._connection_params)
        self._channel = self._connection.channel()
        self._channel.queue_declare(self._house, durable=True)
        self._channel.basic_consume(queue=self._house, on_message_callback=self._manager.newMessage, auto_ack=True)


    def run(self):
        reconnect_attempts = 0
        while not self._stop_event.is_set() and reconnect_attempts < self._max_reconnect_attempts:
            try:
                self.connect()
                print(f"Thread {self._house} connected and consuming.")
                while not self._stop_event.is_set():
                    self._channel.connection.process_data_events(time_limit=1)  # Process events with a timeout
                if self._stop_event.is_set():
                    self._channel.stop_consuming()
                    self._channel.close()
                    self._connection.close()
                    print(f"Thread {self._house} stopped.")

            except pika.exceptions.AMQPConnectionError:
                reconnect_attempts += 1
                print(f"Thread {self._house} lost connection, attempting to reconnect...")
                time.sleep(5)  # Wait before attempting to reconnect
                if reconnect_attempts >= self._max_reconnect_attempts:
                    print(f"Thread {self._house} reached maximum reconnection attempts. Stopping thread.")
            except Exception as e:
                print(f"Thread {self._house} encountered an error: {e}")
                break



def main():
    print("Starting Accumulator...")

    houses = {}
    DataSet.process_json_files_in_folder('./house_files', houses)
    connection_params = configurations.get('internalAMQPServer')
    
    threads = []
    try:
        for house in houses.keys():
            accumulator_thread = AcummulatorThread(house, houses[house],connection_params)
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
    main()

