import threading
import paho.mqtt.client as mqtt
import os
import time
import socket
from data import DataSet
from pydoc import locate

# Load configurations
configurations = DataSet.get_schema(os.path.join('..', 'runtimeConfigurations.json'))

class CarSpecsReceiver:
    def __init__(self):
        self._translators = configurations.get('CarSpecsTranslators')
        self._client = mqtt.Client()
        self._connection_params = configurations.get('CarSpecsserver')
        self._max_reconnect_attempts = configurations.get('maxReconnectAttempts')
        self._message = None
        self._message_event = threading.Event()

    def on_message(self, client, userdata, msg):
        print("Message received from topic:", msg.topic)
        self._message = msg.payload.decode()
        translator = self._translators[self._subtopic]
        locate(translator).translate(self._message)
        print("Message received and callback executed. Disconnecting...")
        client.loop_stop()
        client.disconnect()
        self._message_event.set()

    def subscribe_to_car_topic(self, car_id, subtopic):
        self._client.on_message = self.on_message
        self._subtopic = subtopic
        reconnect_attempts = 0

        while reconnect_attempts < self._max_reconnect_attempts:
            try: 
                self._client.connect(self._connection_params.get('host'))
                self._client.subscribe(f"{car_id}/{subtopic}")
                self._client.loop_start()

                # Wait for the message to be received
                self._message_event.wait()
                
                # Return the received message
                return self._message

            except ConnectionRefusedError:
                print("Connection refused. Retrying...")
                reconnect_attempts += 1
                time.sleep(2 ** reconnect_attempts)

            except TimeoutError:
                print("Connection timeout. Retrying...")
                reconnect_attempts += 1
                time.sleep(2 ** reconnect_attempts)

            except socket.error as e:
                print(f"Socket error occurred: {e}. Retrying...")
                reconnect_attempts += 1
                time.sleep(2 ** reconnect_attempts)

            except Exception as e:
                print(f"An unexpected error occurred: {e}. Retrying...")
                reconnect_attempts += 1
                time.sleep(2 ** reconnect_attempts)

        if reconnect_attempts >= self.max_reconnect_attempts:
            print("Max reconnect attempts reached! It was not possible to subscribe to the topic.")

teste = CarSpecsReceiver()
teste.subscribe_to_car_topic("1", "soc")


#https://pypi.org/project/paho-mqtt/#callbacks