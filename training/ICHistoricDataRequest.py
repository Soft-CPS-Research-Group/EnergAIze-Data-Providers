from datetime import timedelta, datetime
import os
import sys
import time
import pika
import json
from ICHistoricDataTranslator import ICHistoricDataTranslator
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from data import DataSet

configurations = DataSet.get_schema(os.path.join('..', 'historicConfigurations.json'))

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
        self._connection = pika.BlockingConnection(self._connection_params)
        self._channel = self._connection.channel()

    def run(self):   
        for house in self._houses.keys():
            print(house)
            date = self._start_date
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
                print(message_json)
                
                if (date == self._end_date):
                    print("olaa")
                    self._itsTheLastOne = True # Talvez precise de alguma proteção aqui
                date += timedelta(days=1)
                self._send_message(message_json, house)
            

    def _on_response(self, body):
        data = json.loads(body)
        observations = data.get('observation')
        house = data.get('installation')
        print(observations)

        if self._data.get(house) is None:
            self._data[house] = observations
        else:
            self._data[house].extend(observations)
        #print(f'{self._data[house]}\n\n')
        if self._itsTheLastOne:
            self._itsTheLastOne = False
            print("ola")
            with open(f'{house}_historicreal.json', 'w') as file:
                json.dump(self._data[house], file, indent=4)
            ICHistoricDataTranslator.translate(house, self._houses.get(house), self._data.get(house), self._start_date, self._end_date, self._period)
            

    def _send_message(self, message, house):
        returnQueueName = f"{house}_historic"
        self._connect()
        self._channel.queue_declare(queue='RPC', durable=True)
        self._channel.queue_declare(queue=returnQueueName, exclusive=True)
        self._channel.basic_publish(
            exchange='',
            routing_key='RPC',
            body=message,
            properties=pika.BasicProperties(
                reply_to=returnQueueName
            )
        )

        while True:
            method_frame, header_frame, body = self._channel.basic_get(queue=returnQueueName)
            if method_frame:
                self._channel.basic_ack(method_frame.delivery_tag)
                self._on_response(body)
                break 

        self._connection.close()

   
def main(start_date, end_date, period):
    print("Starting ICHistoricDataRequest...")

    connection_params = configurations.get('IChistoricalServer')

    '''schema = DataSet.get_schema(os.path.join('..',configurations.get('ICfile').get('path')))
    schema.pop('provider')'''
    schema = {'Garage':[]}
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