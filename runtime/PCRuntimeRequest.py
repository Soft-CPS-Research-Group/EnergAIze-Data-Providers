import pika
import json
import uuid
import time
from utils.data import DataSet
from utils.config_loader import load_configurations

# Load configurations
configurations, logger = load_configurations('./configs/runtimeConfigurations.json',"pulsecharge")

class PCRuntimeRequest:
    def __init__(self, houses, frequency, connection_params):
        self._connection_params = pika.ConnectionParameters(host=connection_params.get('host'), port=connection_params.get('port'),credentials=pika.PlainCredentials(connection_params.get('credentials').get('username'), connection_params.get('credentials').get('password')), heartbeat=660)
        self._request_queue = connection_params.get('frequency_change').get('request')
        self._response_queue = connection_params.get('frequency_change').get('response')
        self._max_reconnect_attempts = configurations.get('maxReconnectAttempts')
        self._connection = None
        self._channel = None
        self._max_reconnect_attempts = configurations.get('maxReconnectAttempts')
        self._completed = False

        self._message = {
            {
                "frequency": frequency
            }
        }

    def init(self):
        self._message = json.dumps(self._message)

        self._send_message()

    def _connect(self):
        # Get connection parameters
        self._connection = pika.BlockingConnection(self._connection_params)
        self._channel = self._connection.channel()
        self._channel.queue_declare(queue=self._request_queue, durable=True)
        self._channel.queue_declare(queue=self._response_queue, exclusive=True)

    def _send_message(self):
        while self._max_reconnect_attempts > 0 and self._completed == False:
            try:
                self._connect()
                self._channel.basic_publish(
                    exchange='',
                    routing_key='RPC',
                    body=self._message,
                    properties=pika.BasicProperties(
                        message_id=str(uuid.uuid4())
                    )
                )

                self._channel.basic_consume(
                    queue=self._response_queue.method.queue,
                    on_message_callback=self._on_response,
                    auto_ack=True
                )

                # Start consuming
                self._channel.start_consuming()

                self._completed = True
            except pika.exceptions.AMQPConnectionError:
                if self._max_reconnect_attempts == 0:
                    print(f"Thread PCRuntimeRequest reached maximum reconnection attempts. Stopping thread.")
                else:
                    print(f"Thread PCRuntimeRequest lost connection, attempting to reconnect...")
                    time.sleep(5)

                self._max_reconnect_attempts -= 1
            except Exception as e:
                print(f"Thread PCRuntimeRequest encountered an error: {e}")



    def _on_response(self, ch, method, properties, body):
            print("Received response:", body.decode())
            ch.stop_consuming()
            ch.close()


def main():
    print("Starting PCRuntimeRequest...")
    connection_params = configurations.get('PCserver')
    # Get CW Houses file and turn it into a dictionary
    PCHouses = DataSet.get_schema(configurations.get('PCfile').get('path'))
    # Remove provider key because it does not contain any useful information here
    PCHouses.pop('provider')

    frequency = DataSet.calculate_interval(configurations.get('frequency'))

    PCRuntimeRequest(PCHouses, frequency, connection_params).init()


if __name__ == "__main__":
    main()
