import os
import sys
import time
import pika
import json
import uuid

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from utils.data import DataSet

configurations = DataSet.get_schema(os.path.join('..', 'historicConfigurations.json'))

class ICInstallationsRequest():
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
            self._send_message(message_json)
            

    def _on_response(self, body):
        try:
            data = json.loads(body)
            print("Data received:", data)
            with open('installations.json', 'w', encoding='utf-8') as file:
                json.dump(data, file, indent=4, ensure_ascii=False)
            print("Data successfully saved to installations.json!")
        except json.JSONDecodeError as e:
            print("Error decoding JSON response:", e)
        except Exception as e:
            print("Unexpected error while saving the JSON file:", e)
        #ICHistoricDataTranslator.translate(house, self._houses.get(house), self._data.get(house), self._start_date, self._end_date, self._period)
        

    def _send_message(self, message):
        returnQueueName = f"installations_request_{int(time.time())}"
        print(f"Return queue name: {returnQueueName}")
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
    print("Starting ICInstallationsRequest...")

    connection_params = configurations.get('IChistoricalServer')

    historicData = ICInstallationsRequest(connection_params)
    historicData.run()

  
if __name__ == "__main__":  
    main()