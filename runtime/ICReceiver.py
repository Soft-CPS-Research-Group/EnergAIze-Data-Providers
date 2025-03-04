import pika
import threading
import time
from runtime.ICTranslator import ICTranslator
from utils.data import DataSet
from utils.config_loader import load_configurations

# Load configurations
configurations, logger = load_configurations('./configs/runtimeConfigurations.json',"icharging")


class ICReceiver(threading.Thread):
    def __init__(self, house_name, devices, connection_params):
        threading.Thread.__init__(self)
        self._devices = devices
        self._house = house_name
        self._connection_params = pika.ConnectionParameters(host=connection_params.get('host'), port=connection_params.get('port'),credentials=pika.PlainCredentials(connection_params.get('credentials').get('username'), connection_params.get('credentials').get('password')), heartbeat=660)
        self._connection = None
        self._channel = None
        self._max_reconnect_attempts = configurations.get('maxReconnectAttempts')
        self._stop_event = threading.Event()
 
    def stop(self):
        print(f"Stopping thread {self._house}...")
        self._stop_event.set()

    def _callback(self, ch, method, properties, body):
        if self._stop_event.is_set():
            self._channel.stop_consuming()
            self._channel.close()
            self._connection.close()
            print(f"Thread {self._house} stopped.")
        else:
            ICTranslator.translate(self._house,self._devices,body)
            self._channel.basic_ack(delivery_tag=method.delivery_tag)

    def _connect(self):
        self._connection = pika.BlockingConnection(self._connection_params)
        self._channel = self._connection.channel()
        self._channel.exchange_declare(exchange=self._house, exchange_type='fanout')

        result = self._channel.queue_declare(queue='', exclusive=True)
        self._queue_name = result.method.queue

        print(f"Queue name: {self._queue_name}")
        self._channel.queue_bind(exchange=self._house, queue=self._queue_name)
        self._channel.basic_consume(queue=self._queue_name, on_message_callback=self._callback)
        self._channel.start_consuming()
        
    def run(self):
        while self._max_reconnect_attempts > 0 and not self._stop_event.is_set():
            try:
                self._connect()
                
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
    logger.info("Starting ICReceiver...")
    # Get connection parameters
    connection_params = configurations.get('ICserver')
    # Get CW Houses file and turn it into a dictionary
    ICHouses = DataSet.get_schema(configurations.get('ICfile').get('path'))
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
