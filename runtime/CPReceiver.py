import threading
import paho.mqtt.client as mqtt
import os
import time
import socket
import json
import ssl

from utils.data import DataSet

# Load configurations
configurations = DataSet.get_schema('./configs/runtimeConfigurations.json')

class CPReceiver(threading.Thread):
    def __init__(self, house_name, cars_list, connection_params, subtopic):  #perceber onde meter este subtopico
        threading.Thread.__init__(self)
        print(house_name)
        self._house_name = house_name
        self._client = mqtt.Client()
        self._subtopic = subtopic
        self._cars_list = cars_list
        self._connection_params = connection_params
        self._client.username_pw_set(
            self._connection_params.get('credentials').get('username'),
            self._connection_params.get('credentials').get('password')
        )
        self._client.tls_set("C:/Users/clari/Documents/EnergAIze_Data_Providers/runtime/tls.ca", tls_version=ssl.PROTOCOL_TLSv1_2)
        self._client.tls_insecure_set(True)
        self._max_reconnect_attempts = configurations.get('maxReconnectAttempts')
        self._stop_connection = threading.Event()
        self._time_sleep = DataSet.calculate_interval(configurations.get('frequency'))
        
    def _on_message(self, client, userdata, msg):
        try:
            message = msg.payload.decode()  
            print(f"Message received! Topic: {msg.topic} Message: {message}")
            json_message = json.loads(message) 
            #secalhar abrir thread aqui
            #CPTranslator.translate(self._house_name, json_message)
        except json.JSONDecodeError as e:
            print("Failed to decode JSON. Error:", e)
        except Exception as e:
            print("An unexpected error occurred:", e)
    
    def stop(self):
        self._stop_connection.set()
        self._client.loop_stop()
        self._client.disconnect()

    def run(self):
        self._client.on_message = self._on_message
        reconnect_attempts = 0

        while reconnect_attempts < self._max_reconnect_attempts and not self._stop_connection.is_set():
            try: 
                self._client.connect(
                    self._connection_params.get('host'),
                    self._connection_params.get('port'),
                    self._time_sleep + 20
                )
                for car in self._cars_list:
                    print(f"Subscribing to topic: {car.get('id')}/{self._subtopic}")
                    self._client.subscribe(f"{car.get('id')}/{self._subtopic}")
                self._client.loop_start()

                # Wait for the message to be received
                self._stop_connection.wait()

                break

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

        if reconnect_attempts >= self._max_reconnect_attempts:
            print("Max reconnect attempts reached! It was not possible to subscribe to the topic.")

def main():
    print("Starting CPReceiver...")
    # Get connection parameters
    connection_params = configurations.get('CPserver')
    # Get CW Houses file and turn it into a dictionary
    CPHouses = DataSet.get_schema(os.path.join('..', configurations.get('CPfile').get('path')))
    print(CPHouses)
    CPHouses.pop('provider')
    
    threads = []

    try:
        for house in CPHouses.keys():
            cars_list = CPHouses[house]
            receiver_thread = CPReceiver(house, cars_list, connection_params, "data")
            receiver_thread.start()
            threads.append(receiver_thread)

        # Check if threads are alive, if not, remove them from the list and if all of them are dead, stop the program
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



#https://pypi.org/project/paho-mqtt/#callbacks