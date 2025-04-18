import pika
import time
import datetime
import json
from utils.config_loader import load_configurations

# Load configurations
configurations, logger = load_configurations('./configs/runtimeConfigurations.json',"cleanwatts")

class CPTranslator():
    @staticmethod
    def translate(house_name,message):
        connection_params = configurations['internalAMQPServer']
        max_reconnect_attempts = configurations.get('maxReconnectAttempts')
        queue_name = house_name + configurations['QueueSuffixes']['MessageAggregator']

        while max_reconnect_attempts > 0:
            try:
                connection = pika.BlockingConnection(pika.ConnectionParameters(
                    host=connection_params.get('host'),
                    port=connection_params.get('port')
                ))
                channel = connection.channel()
                channel.queue_declare(queue=queue_name, durable=True)

                newmessage = {
                    "id": message['vin'],
                    "value": message,
                    "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                }
                message_bytes = json.dumps(newmessage).encode('utf-8')
                time.sleep(5)  
                channel.basic_publish(exchange='', routing_key=queue_name, body=message_bytes)
                print(f"Menssage {json.dumps(newmessage, indent=4)}")
                channel.close()
                connection.close()
                break  # Break out of the retry loop if successful

            except pika.exceptions.AMQPConnectionError as e:
                max_reconnect_attempts -= 1  # Decrement the retry counter
                if max_reconnect_attempts == 0:
                    print(f"{house_name} translator reached maximum reconnection attempts. The message was not sent.")
                else:
                    print(f"{house_name} translator lost connection, attempting to reconnect...")
                    time.sleep(5) 
            except Exception as e:
                print(f"An unexpected error occurred: {e} {house_name}")
                break
