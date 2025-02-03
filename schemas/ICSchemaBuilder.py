import os
import sys
import time
import pika
import json
import uuid
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from utils.data import DataSet

configurations = DataSet.get_schema(os.path.join('..', 'historicConfigurations.json'))

class ICSchemaBuilder():
    def __init__(self, connection_params):
        self._connection_params = pika.ConnectionParameters(host=connection_params.get('host'), port=connection_params.get('port'),credentials=pika.PlainCredentials(connection_params.get('credentials').get('username'), connection_params.get('credentials').get('password')), heartbeat=660)
    
    def _connect(self):
        self._connection = pika.BlockingConnection(self._connection_params)
        self._channel = self._connection.channel()

    def run(self):   
            message = {
                "type": "installations",
                "value": {}
            }
            message_json = json.dumps(message)
            print(message_json)
            self._send_message(message_json)
            

    def _on_response(self, body):
        try:
            data = json.loads(body)
            self._schema_builder(data)
        except json.JSONDecodeError as e:
            print("Error decoding JSON response:", e)
        except Exception as e:
            print("Unexpected error while saving the JSON file:", e)
        
    def _schema_builder(self, data):
        print(data)
        houses_dict = {"provider":"i-charging"}
        for entry in data:
            installation = entry.get('installation')
            battery = entry.get('battery')
            meters = entry.get('meters')
            pv = entry.get('pv')
            chargers = entry.get('chargers')
            list = []
            if battery:
                dic = {
                    "label": "battery_charging_energy",
                    "id": battery.get('id')
                }
                list.append(dic)
            if pv:
                dic = {
                    "label": "solar_generation",
                    "id": pv.get('id')
                }
                list.append(dic)

            '''for meter in meters:
                dic = {
                    "label": "non_shiftable_load",
                    "id": meter.get('id')
                }
                list.append(dic)'''

            for charger in chargers:
                serial_number = charger.get('serialnumber')
                for plug in charger.get('plugs'):
                    plugId = plug.get('id')
                    dic = {
                        "id" : f"{serial_number}_{plugId}",
                        "label": "charging_sessions",
                        "serialNumber": serial_number,
                        "plug": plugId
                    }
                    list.append(dic)
            
            houses_dict[installation] = list

        self._to_file(houses_dict)

    def _to_file(self, data):
        try:
            with open('ICData.json', 'w') as file:
                json.dump(data, file, indent = 4)

        except Exception as e:
            print("Unexpected error while saving the CSV file:", e)

    def _send_message(self, message):
        returnQueueName = f"installations_request_{int(time.time())}"
        self._connect()
        self._channel.queue_declare(queue='RPC', durable=True)
        self._channel.queue_declare(queue=returnQueueName, exclusive=True)
        self._channel.basic_publish(
            exchange='',
            routing_key='RPC',
            body=message,
            properties=pika.BasicProperties(
                reply_to=returnQueueName,
                message_id=str(uuid.uuid4())
            )
        )

        while True:
            method_frame, header_frame, body = self._channel.basic_get(queue=returnQueueName)
            if method_frame:
                self._channel.basic_ack(method_frame.delivery_tag)
                self._on_response(body)
                break 

        self._connection.close()

   
def main():
    print("Starting ICSchemaBuilder...")

    connection_params = configurations.get('IChistoricalServer')

    historicData = ICSchemaBuilder(connection_params)
    historicData.run()

  
if __name__ == "__main__":  
    main()