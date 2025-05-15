import threading
import pika
import os
import time
import socket
import json
from runtime.PCTranslator import PCTranslator
from utils.config_loader import load_configurations
from utils.data import DataSet

# Load configurations
configurations, logger = load_configurations('./configs/runtimeConfigurations.json',"pulsecharge")

class PCReceiver(threading.Thread):
    def __init__(self, house_name, cars, connection_params):
        threading.Thread.__init__(self)
        self._house = house_name
        self._cars = cars
        self._connection_params = pika.ConnectionParameters(host=connection_params.get('host'),
                                                            port=connection_params.get('port'),
                                                            credentials=pika.PlainCredentials(
                                                                connection_params.get('credentials').get('username'),
                                                                connection_params.get('credentials').get('password')),
                                                            heartbeat=660)

        self._connection = None
        self._channel = None
        self._max_reconnect_attempts = configurations.get('maxReconnectAttempts')
        self._stop_event = threading.Event()

    def stop(self):
        logger.info(f"PCReceiver: Stopping thread {self._house}...")
        self._stop_event.set()

    def _callback(self, ch, method, properties, body):
        if self._stop_event.is_set():
            self._channel.stop_consuming()
            self._channel.close()
            self._connection.close()
            logger.info(f"PCReceiver: Thread {self._house} stopped.")
        else:
            logger.info(f"PCReceiver: {body}")
            #PCTranslator.translate(self._house,body)
            self._channel.basic_ack(delivery_tag=method.delivery_tag)

    def _connect(self):
        self._connection = pika.BlockingConnection(self._connection_params)
        self._channel = self._connection.channel()
        try:
            self._channel.exchange_declare(exchange=self._house,passive=True)
            logger.debug(f"PCReceiver: Exchange {self._house} exists!")
            # If the exchange does not exist, this exception is raised.
        except pika.exceptions.ChannelClosedByBroker as e:
            logger.debug(f"PCReceiver: Exchange {self._house} does not exist")
            self._channel = self._connection.channel()
            self._channel.exchange_declare(self._house, durable=True, exchange_type='fanout')

        result = self._channel.queue_declare(queue='', exclusive=True)
        self._queue_name = result.method.queue

        self._channel.queue_bind(exchange=self._house, queue=self._queue_name)
        self._channel.basic_consume(queue=self._queue_name, on_message_callback=self._callback)
        self._channel.start_consuming()

    def run(self):
        while self._max_reconnect_attempts > 0 and not self._stop_event.is_set():
            try:
                self._connect()

            except pika.exceptions.AMQPConnectionError:
                if self._max_reconnect_attempts == 0:
                    logger.error(f"PCReceiver: Thread {self._house} reached maximum reconnection attempts. Stopping thread.")
                else:
                    logger.error(f"PCReceiver: Thread {self._house} lost connection, attempting to reconnect...")
                    time.sleep(5)

                self._max_reconnect_attempts -= 1
            except Exception as e:
                logger.error(f"PCReceiver: Thread {self._house} encountered an error: {e}")

def main():
    logger.info("PCReceiver: Starting PCReceiver...")
    # Get connection parameters
    connection_params = configurations.get('PCserver')
    # Get CW Houses file and turn it into a dictionary
    PCHouses = DataSet.get_schema(configurations.get('PCfile').get('path'))

    PCHouses.pop('provider')
    
    threads = []

    try:
        for house in PCHouses.keys():
            cars_list = PCHouses[house]
            receiver_thread = PCReceiver(house, cars_list, connection_params)
            receiver_thread.start()
            threads.append(receiver_thread)

        # Check if threads are alive, if not, remove them from the list and if all of them are dead, stop the program
        while threads:
            for thread in threads:
                if not thread.is_alive():
                    threads.remove(thread)
                time.sleep(0.1)

    except KeyboardInterrupt:
        logger.info("PCReceiver: [KeyboardInterrupt] Stopping threads...")
        for thread in threads:
            thread.stop()

        for thread in threads:
            thread.join()
        logger.info("PCReceiver: All threads stopped.")



if __name__ == "__main__":
    main()