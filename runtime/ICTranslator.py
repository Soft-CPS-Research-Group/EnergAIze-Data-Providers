import pika
import datetime
import json
import os
import time
import copy
from data import DataSet

# Load configurations
configurations = DataSet.get_schema(os.path.join('..', 'runtimeConfigurations.json'))

class ICTranslator:
    @staticmethod
    def translate(house_name, devices, message):
        # Load Internal AMQP Server configurations
        connection_params = configurations['internalAMQPServer']
        max_reconnect_attempts = configurations['maxReconnectAttempts']
        # Define the queue name
        queue_name = house_name + configurations['QueueSuffixes']['MessageAggregator']
      
        message = json.loads(message.decode('utf-8'))

        while max_reconnect_attempts > 0:
            try:
                connection = pika.BlockingConnection(pika.ConnectionParameters(
                    host=connection_params.get('host'),
                    port=connection_params.get('port')
                ))
                channel = connection.channel()
                channel.queue_declare(queue=queue_name, durable=True)

                messageIC = configurations['messageIC']
                for device in devices:
                    for pm in messageIC.keys():
                        if pm in message and device.get('label') == messageIC[pm]:
                            newmessage = {
                                "id": device.get('id'),
                                "value": message[pm],
                                "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                            }
                            print(f"House: {house_name} {json.dumps(newmessage, indent=2)}")
                            message_bytes = json.dumps(newmessage).encode('utf-8')   
                            time.sleep(5)
                            channel.basic_publish(exchange='', routing_key=queue_name, body=message_bytes)

                users = DataSet.get_schema(os.path.join('..', configurations.get('Users').get('path')))[house_name]

                chargerSessionFormat = configurations.get('ChargersSessionFormat')
                chargersSession = message.get('charging.session')
            
                for chargerSession in chargersSession:
                    cs = copy.deepcopy(chargerSessionFormat)
                    chargerId = f"{chargerSession.get('serialnumber')}_{chargerSession.get('plug')}"
                    cs['Charger Id'] = chargerId
                    if chargerSession.get('user.id') != None:
                        userPreferences = users.get(chargerSession.get('user.id'))
                        for key in userPreferences.keys():
                            if key in cs.keys():
                                cs[key] = userPreferences[key]
                        
                        cs['EsocA'] = -1
                        cs['soc'] = chargerSession.get('soc')
                        cs['power'] = chargerSession.get('power')
                    newmessage = {
                            "id": chargerId,
                            "value": cs,
                            "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        }
                  
                    message_bytes = json.dumps(newmessage).encode('utf-8')   
                    time.sleep(5)
                    channel.basic_publish(exchange='', routing_key=queue_name, body=message_bytes)
                
                print(f"House: {house_name} {json.dumps(message, indent=2)}")
                break
            except pika.exceptions.AMQPConnectionError as e:
                max_reconnect_attempts -= 1  # Decrement the retry counter
                if max_reconnect_attempts == 0:
                    print(f"{house_name} translator reached maximum reconnection attempts. The message was not sent.")
                else:
                    print(f"{house_name} translator lost connection, attempting to reconnect...")
                    time.sleep(5) 
            except Exception as e:
                print(f"An unexpected error occurred: {e}")
                break

# Em caso de erro corro o risco da mensagem ser enviada duas vezes, mas não é um problema
