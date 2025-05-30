import pika
import json
import datetime
import time
from utils.config_loader import load_configurations

# Load configurations
configurations, logger = load_configurations('./configs/runtimeConfigurations.json',"cleanwatts")

class CWTranslator:
    @staticmethod
    def translate(house_name, message):
        connection_params = configurations['internalAMQPServer']
        max_reconnect_attempts = configurations.get('maxReconnectAttempts')
      
        while max_reconnect_attempts > 0:
            try:
                connection = pika.BlockingConnection(pika.ConnectionParameters(
                    host=connection_params.get('host'),
                    port=connection_params.get('port'), virtual_host=connection_params.get('vhost'), credentials=pika.PlainCredentials(connection_params.get('credentials').get('username'), connection_params.get('credentials').get('password'))
                ))
                channel = connection.channel()
                channel.queue_declare(queue=house_name, durable=True)
                if len(message) == 0:
                    print(f"There is no data for one of the {house_name} tags.")
                    break

                id = message[0]['TagId']
                value = 0

                for msg in message:
                    value+=msg['Read']

                newmessage = {
                    "id": id,
                    "value": value,
                    "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                }
                message_bytes = json.dumps(newmessage).encode('utf-8')

                channel.basic_publish(exchange='', routing_key=house_name, body=message_bytes)
                #print(f"Mensagem antiga: {json.dumps(message, indent=4)}\nMensagem nova: {json.dumps(newmessage, indent=4)}")
                channel.close()
                connection.close()
                break  # Break out of the retry loop if successful

            except pika.exceptions.AMQPConnectionError as e:
                max_reconnect_attempts -= 1  # Decrement the retry counter
                if max_reconnect_attempts == 0:
                    logger.error(f"CWTranslator: {house_name} translator reached maximum reconnection attempts. The message was not sent.")
                else:
                    logger.warning(f"CWTranslator: {house_name} translator lost connection, attempting to reconnect...")
                    time.sleep(5) 
            except Exception as e:
                logger.error(f"CWTranslator: An unexpected error occurred: {e} {house_name}")
                break
   
        logger.info(f"CWTranslator: Translating {house_name} successfully!")