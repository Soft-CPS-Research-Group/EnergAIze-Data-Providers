import pika
import threading
import time
from runtime.Manager import Manager
from utils.data import DataSet
from utils.config_loader import load_configurations

# Load configurations
configurations, logger = load_configurations('./configs/runtimeConfigurations.json',"accumulator")

class Accumulator(threading.Thread):
    def __init__(self, house, house_specs, connection_params):
        threading.Thread.__init__(self)
        logger.info(f"Accumulator: thread for house {house} started with success!")
        self._house = house
        self._manager = Manager(house_specs,house)
        self._connection_params = pika.ConnectionParameters(host=connection_params.get('host'), port=connection_params.get('port'), virtual_host=connection_params.get('vhost'), credentials=pika.PlainCredentials(connection_params.get('credentials').get('username'), connection_params.get('credentials').get('password')), heartbeat=660)
        self._connection = None
        self._channel = None
        self._stop_event = threading.Event()

    def stop(self):
        logger.info(f"Accumulator: Stopping thread {self._house}")
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
                logger.warning("Accumulator: Error processing RabbitMQ message.")

    def _connect(self):
        self._connection = pika.BlockingConnection(self._connection_params)
        self._channel = self._connection.channel()
        self._channel.queue_declare(self._house, durable=True)
        self._channel.basic_consume(queue=self._house, on_message_callback=self._callback)
        self._channel.start_consuming()


    def run(self):
        wait_time = 1
        while not self._stop_event.is_set():
            try:
                self._connect()
            except pika.exceptions.AMQPConnectionError as e:
                logger.warning(f"Accumulator: Thread {self._house} lost connection. Error: {e}. Waiting {wait_time} seconds before attempting to reconnect...")
                time.sleep(wait_time)
                wait_time *= 2
            except KeyboardInterrupt:
                logger.info(f"Accumulator: Thread {self._house} RabbitMQ session manually closed.")
                self.stop()
            except Exception as e:
                logger.error(f"Accumulator: Thread {self._house} encountered an error: {e}")
                break
            

def main():
    logger.info("Starting Accumulator...")
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
