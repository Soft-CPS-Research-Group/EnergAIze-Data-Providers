import pika
import threading
import time
import os
import sys
from ICTranslator import ICTranslator
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from data import DataSet

# Load configurations
configurations = DataSet.get_schema(os.path.join('..', 'runtimeConfigurations.json'))

class ICReceiver(threading.Thread):
    def __init__(self, house_name, devices, connection_params):
        threading.Thread.__init__(self)
        self._devices = devices
        self._house = house_name
        self._connection_params = pika.ConnectionParameters(host=connection_params.get('host'), port=connection_params.get('port'),credentials=pika.PlainCredentials(connection_params.get('credentials').get('username'), connection_params.get('credentials').get('password')), heartbeat=660)
        self._connection = None
        self._channel = None
        self._stop_event = threading.Event()
        self._max_reconnect_attempts = configurations.get('maxReconnectAttempts')
 
    def stop(self):
        print(f"Stopping thread {self._house}...")
        self._stop_event.set()
        self._channel.stop_consuming()
        self._channel.close()
        self._connection.close()
        print(f"Thread {self._house} stopped.")

    def connect(self):
        self._connection = pika.BlockingConnection(self._connection_params)
        self._channel = self._connection.channel()
        self._channel.exchange_declare(exchange=self._house, exchange_type='fanout')
        result = self._channel.queue_declare(queue='', exclusive=True)
        self._queue_name = result.method.queue
        print(f"Queue name: {self._queue_name}")
        self._channel.queue_bind(exchange=self._house, queue=self._queue_name)
        self._channel.basic_consume(queue=self._queue_name, on_message_callback=lambda ch, method, properties, body:ICTranslator.translate(self._house,self._devices,body), auto_ack=True)
        self._channel.start_consuming()
        
    def run(self):
        while not self._stop_event.is_set() and self._max_reconnect_attempts > 0:
            try:
                self.connect()
                '''print(f"Thread {self._house} connected and consuming.")
                for message in self._channel.consume(self._queue_name, inactivity_timeout=1):
                    if self._stop_event.is_set():
                        break
                    if not all(message):
                        continue
                    method, properties, body = message
                    ICTranslator.translate(self._house, self._devices, body)
                while not self._stop_event.is_set():
                    self._channel.connection.process_data_events(time_limit=1)'''  # Process events with a timeout
            except pika.exceptions.AMQPConnectionError:
                if self._max_reconnect_attempts == 0:
                    print(f"Thread {self._house} reached maximum reconnection attempts. Stopping thread.")
                else:
                    print(f"Thread {self._house} lost connection, attempting to reconnect...")
                    time.sleep(5)  

                self._max_reconnect_attempts -= 1
            except Exception as e:
                print(f"Thread {self._house} encountered an error: {e}")
                break

        
def main():
    print("Starting ICReceiver...")
    # Get connection parameters
    connection_params = configurations.get('ICserver')
    # Get CW Houses file and turn it into a dictionary
    ICHouses = DataSet.get_schema(os.path.join('..', configurations.get('ICfile').get('path')))
    # Remove provider key because it does not contain any useful information here
    ICHouses.pop('provider')

    threads = []

    try:
        for house in ICHouses.keys():
            devices = ICHouses[house]
            receiver_thread = ICReceiver(house, devices, connection_params)
            receiver_thread.start()
            threads.append(receiver_thread)

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
