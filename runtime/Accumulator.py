import pika
import threading
import time
from runtime.Manager import Manager
from utils.data import DataSet
from utils.config_loader import load_configurations

# Load configurations
configurations, logger = load_configurations('./configs/runtimeConfigurations.json',"accumulator")

class Accumulator(threading.Thread):
    def __init__(self, house, devices, connection_params):
        threading.Thread.__init__(self)
        self._house = house
        self._manager = Manager(devices,house)
        self._connection_params = pika.ConnectionParameters(host=connection_params.get('host'), port=connection_params.get('port'),heartbeat=660)
        self._connection = None
        self._channel = None
        self._stop_event = threading.Event()
        self._max_reconnect_attempts = 3

    def stop(self):
        logger.info(f"Stopping thread {self._house}")
        self._stop_event.set()
    
    def _callback(self, ch, method, properties, body):
        if self._stop_event.is_set():
            self._manager.stop()
            self._channel.stop_consuming()
            self._channel.close()
            self._connection.close()
        else:
            if(self._manager.newMessage(body)):
                self._channel.basic_ack(delivery_tag=method.delivery_tag)
            else:
                self._channel.basic_nack(delivery_tag=method.delivery_tag)
                logger.warning("Error processing RabbitMQ message.")

    def _connect(self):
        self._connection = pika.BlockingConnection(self._connection_params)
        self._channel = self._connection.channel()
        self._channel.queue_declare(self._house, durable=True)
        self._channel.basic_consume(queue=self._house, on_message_callback=self._callback)
        self._channel.start_consuming()


    def run(self):

        reconnect_attempts = 0
        while not self._stop_event.is_set() and reconnect_attempts < self._max_reconnect_attempts:
            try:
                self._connect()                
            except pika.exceptions.AMQPConnectionError:
                reconnect_attempts += 1
                logger.warning(f"Thread {self._house} lost connection, attempting to reconnect...")
                time.sleep(5)  # Wait before attempting to reconnect
                if reconnect_attempts >= self._max_reconnect_attempts:
                    logger.error(f"Thread {self._house} reached maximum reconnection attempts. Stopping thread.")
            except KeyboardInterrupt:
                logger.info(f"Thread {self._house} RabbitMQ session manually closed.")
                self.stop()
            except Exception as e:
                logger.error(f"Thread {self._house} encountered an error: {e}")
                break
            

def main():
    print("Starting Accumulator...")
    connection_params = configurations['internalAMQPServer']
    
    houses = {}
    DataSet.process_json_files_in_folder('./house_files', houses)
    threads = []
    try:
        for house in houses.keys():
            accumulator_thread = Accumulator(house, houses[house], connection_params)
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
