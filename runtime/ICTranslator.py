import pika
import datetime
import json
import time
import copy
from utils.data import DataSet
from utils.config_loader import load_configurations

# Load configurations
configurations, logger = load_configurations('./configs/runtimeConfigurations.json',"icharging")

class ICTranslator:
    @staticmethod
    def translate(house_name, devices, message):
        # Load Internal AMQP Server configurations
        connection_params = configurations['internalAMQPServer']
        max_reconnect_attempts = configurations['maxReconnectAttempts']

        message = json.loads(message.decode('utf-8')).get('observation')
        #print(f"House: {house_name} {json.dumps(message, indent=2)}")
        while max_reconnect_attempts > 0:
            try:
                connection = pika.BlockingConnection(pika.ConnectionParameters(
                    host=connection_params.get('host'),
                    port=connection_params.get('port'), virtual_host=connection_params.get('vhost'), credentials=pika.PlainCredentials(connection_params.get('credentials').get('username'), connection_params.get('credentials').get('password'))
                ))
                channel = connection.channel()
                channel.queue_declare(queue=house_name, durable=True)

                message_ic = configurations['messageIC']
                for device in devices:
                    for pm in message_ic.keys():
                        if pm in message and device.get('label') == message_ic[pm]:
                            if pm == 'meter.values' and message[pm]:
                                for meter in message[pm]:
                                    if meter.get('id') == device.get('id'):
                                        value = meter.get('l123')
                            else:
                                value = message[pm]

                            new_message = {
                                "id": device.get('id'),
                                "value": value,
                                "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                            }
                            print(f"House: {house_name} {json.dumps(new_message, indent=2)}")
                            message_bytes = json.dumps(new_message).encode('utf-8')
                            #time.sleep(2)
                            channel.basic_publish(exchange='', routing_key=house_name, body=message_bytes)

                charger_session_format = configurations.get('ChargingSessionsFormat')
                chargers_session = message.get('charging.session')

                for charger_session in chargers_session:
                    cs = copy.deepcopy(charger_session_format)
                    # TODO futuramente criar algum mapeamento nas defenições ou assim para n ter de alterar aqui caso as coisas mudem de nome
                    charger_id = f"{charger_session.get('serialnumber')}_{charger_session.get('plug')}"
                    cs['charger_id'] = charger_id
                    cs['soc'] = charger_session.get('soc')
                    cs['power'] = charger_session.get('power')
                    cs['user_id'] = charger_session.get('user.id')
                    cs['flexibility'] = charger_session.get('flexibility')

                    new_message = {
                            "id": charger_id,
                            "value": cs,
                            "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        }
                  
                    message_bytes = json.dumps(new_message).encode('utf-8')
                    #time.sleep(2)
                    channel.basic_publish(exchange='', routing_key=house_name, body=message_bytes)
                    print(f"House: {house_name} {json.dumps(new_message, indent=2)}")
                break
            except pika.exceptions.AMQPConnectionError as e:
                max_reconnect_attempts -= 1  # Decrement the retry counter
                if max_reconnect_attempts == 0:
                    logger.error(f"ICTranslator: {house_name} translator reached maximum reconnection attempts. The message was not sent.")
                else:
                    logger.warning(f"ICTranslator: {house_name} translator lost connection, attempting to reconnect...")
                    time.sleep(5) 
            except Exception as e:
                logger.error(f"ICTranslator: An unexpected error occurred: {e}")
                break

# Em caso de erro corro o risco da mensagem ser enviada duas vezes, mas não é um problema
