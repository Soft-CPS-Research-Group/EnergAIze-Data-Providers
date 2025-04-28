from datetime import timedelta, datetime
import sys
import pika
import threading
import uuid
import time
from pika.exceptions import ProbableAuthenticationError
import json
from training.ICHistoricDataTranslator import ICHistoricDataTranslator
from utils.data import DataSet

configurations = DataSet.get_schema('./configs/historicConfigurations.json')

class ICHistoricDataRequest():
    def __init__(self, houses_list, connection_params, start_date, end_date, period):
        self._connection_params = pika.ConnectionParameters(host=connection_params.get('host'), port=connection_params.get('port'),credentials=pika.PlainCredentials(connection_params.get('credentials').get('username'), connection_params.get('credentials').get('password')), heartbeat=660)
        self._tag_dict = {}

        self._period = period
        self._start_date = start_date
        self._end_date = end_date
        self._houses = houses_list
        self._data = {}
        self._itsTheLastOne = False
        

    def _stop(self):
        print(f"Stopping thread {self._house}...")
        self._channel.stop_consuming()
        self._channel.close()
        self._connection.close()
        print(f"Thread {self._house} stopped.")

    def _connect(self):
        try:
            self._connection = pika.BlockingConnection(self._connection_params)
            self._channel = self._connection.channel()
            self._channel.queue_declare(queue='RPC', durable=True)
        except ProbableAuthenticationError as e:
            print(f'Authentication Error: {e}')
            sys.exit(1)

    def run(self): 
        self._connect() 

        for house in self._houses.keys():
            print(house)

            returnQueueName = f"{house}_historic"
            threading.Thread(target=self._message_processor, args=(returnQueueName,)).start()
            date = self._start_date
            time.sleep(1)
            while date <= self._end_date:
                print(f'{date.isoformat()}\n')
                message = {
                    "type": "historic",
                    "value": {
                        "installation": house,
                        "date": date.isoformat()
                    }
                }
                message_json = json.dumps(message)
                
                date += timedelta(days=1)
                self._send_message(message_json, returnQueueName)

        self._connection.close()

    def _message_processor(self, returnQueueName):
        connection = pika.BlockingConnection(self._connection_params)
        newChannel = connection.channel()
        newChannel.queue_declare(queue=returnQueueName, exclusive=True)
        newChannel.basic_consume(queue=returnQueueName, on_message_callback=self._on_response, auto_ack=True)
        print(f'Waiting for messages in {returnQueueName}...\n')
        newChannel.start_consuming()
        print(f'Channel {returnQueueName} stopped.\n')
        connection.close()

    def _on_response(self, ch, method, properties, body):
        data = json.loads(body)
        if data.get('error') != 5:
            observations = data.get('observation')
            house = data.get('installation')
            print(data)
            if self._data.get(house) is None:
                self._data[house] = observations
            else:
                self._data[house].extend(observations)
            date = datetime.strptime(observations[0].get('time'), "%Y-%m-%dT%H:%M:%SZ").date()
            if date == self._end_date.date():
                print(self._data[house])
                #with open(f'{house}_historicreal.json', 'w') as file:
                    #json.dump(self._data[house], file, indent=4)
                #ICHistoricDataTranslator.translate(house, self._houses.get(house), self._data.get(house), self._start_date, self._end_date, self._period)
                ch.stop_consuming()
                ch.close()
        else:
            print(data.get('description'))

    def _send_message(self, message, returnQueueName):
        self._channel.basic_publish(
            exchange='',
            routing_key='RPC',
            body=message,
            properties=pika.BasicProperties(
                reply_to=returnQueueName,
                message_id=str(uuid.uuid4())
            )
        )
   
def main(start_date, end_date, period):
    print("Starting ICHistoricDataRequest...")

    connection_params = configurations.get('IChistoricalServer')

    schema = DataSet.get_schema(configurations.get('ICfile').get('path'))
    schema.pop('provider')
    print(schema)

    historicData = ICHistoricDataRequest(schema, connection_params, start_date, end_date, period)
    historicData.run()

  
if __name__ == "__main__":
    if len(sys.argv) != 4:
        print("python ICHistoricDataRequest.py <start date> <end date> <period>")
        sys.exit(1)
    
    start_date = datetime.strptime(sys.argv[1], "%Y-%m-%dT%H:%M:%S%z")
    end_date = datetime.strptime(sys.argv[2], "%Y-%m-%dT%H:%M:%S%z")
    period = int(sys.argv[3])
    
    if start_date > end_date:
        print("The start date must be before the end date.")
        sys.exit(1)
    
    main(start_date, end_date, period)