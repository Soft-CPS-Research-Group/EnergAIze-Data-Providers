import pika
import datetime
import time
import random
import json
import os
import sys
from datetime import datetime, timedelta 
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from data import DataSet

# Load configurations
configurations = DataSet.get_schema(os.path.join('..', 'historicConfigurations.json'))

class HistoricDataProducer():
    def __init__(self, connection_params, houses):
        self.delete_house_json_files(houses)
        self._connection_params = pika.ConnectionParameters(host=connection_params.get('host'), port=connection_params.get('port'),credentials=pika.PlainCredentials(connection_params.get('credentials').get('username'), connection_params.get('credentials').get('password')), heartbeat=660)
        self._connection = None
        self._channel = None
        self._max_reconnect_attempts = configurations.get('maxReconnectAttempts')
    
    def delete_house_json_files(self, houses):
        for house_dir in houses:
            file_path = os.path.join(house_dir, "house.json")
            if os.path.isfile(file_path):
                os.remove(file_path)
                print(f"Deleted: {file_path}")
            else:
                print(f"No house.json file found in: {house_dir}")

    def connect(self):
        self._connection = pika.BlockingConnection(self._connection_params) #Just processes one message at a time
        self._channel = self._connection.channel()
        self._channel.queue_declare("Request", durable=True)

    def on_request(self, ch, method, properties, body):
        
        try:
            # Decode the message
            message = json.loads(body)
            message_type = message.get("type")
            message_value = message.get("value")
            if message_type == "historic":
                # Process the "historic" type request
                response_data = self.process_historic_data(message_value)

                # Send response to the 'reply_to' queue specified in message properties
                ch.basic_publish(
                    exchange='',
                    routing_key=properties.reply_to,
                    body=json.dumps(response_data),
                    properties=pika.BasicProperties(correlation_id=properties.correlation_id)
                )
                        
            ch.basic_ack(delivery_tag=method.delivery_tag)
        
        except Exception as e:
            print(f"Error processing request: {e}")
            ch.basic_nack(delivery_tag=method.delivery_tag)
    
    def process_historic_data(self, value):
        house = value.get("installation")
        date = datetime.strptime(value.get("date"), "%Y-%m-%d %H:%M:%S%z")
        
        observations = [self.generate_random_observation(date + timedelta(minutes=i)) for i in range(1440)]
        
        # Estrutura do JSON a ser salvo
        data = {
            "installation": house,
            "observations": observations
        }

        filename = f'{house}.json'
        with open(filename, 'w') as f:
            json.dump(observations, f, indent=4)

        return data
    

    def generate_random_observation(self,date):
        # Gerando valores aleatórios para as observações
        observation = {
            "time": date.isoformat(), 
            "battery.soc": random.randint(0, 100),  # Estado de carga aleatório
            "pv.production": random.randint(0, 100),  # Produção de PV aleatória
            "charging.session": [{
                "id": f"session_{random.randint(1, 1000)}", 
                "serialnumber": f"SN{random.randint(1000, 9999)}", 
                "user.id": f"user{random.randint(1, 100)}@mail.com", 
                "card.id": f"{random.randint(1000, 9999)}", 
                "plug": random.randint(0, 1), 
                "soc": random.randint(0, 100), 
                "power": random.randint(0, 50), 
                "flexibility": {
                    "arrival.time": "09:00:00",
                    "departure.time": "18:00:00", 
                    "vehicle.model": f"Model_{random.randint(1, 10)}",
                    "energy.min": random.randint(0, 10),
                    "energy.total": random.randint(10, 100),
                    "prioritary": random.choice([True, False]),
                    "optimization": random.choice([True, False]),
                    "departure.soc": random.randint(80, 100)
                }
            }],
            "meter.values": [{
                "id": f"meter_{random.randint(1, 10)}", 
                "l1": random.randint(0, 10), 
                "l2": random.randint(0, 10), 
                "l3": random.randint(0, 10), 
                "l123": random.randint(0, 30)
            }]
        }
        return observation

    def run(self):
        reconnect_attempts = 0
        while reconnect_attempts < self._max_reconnect_attempts:
            #try:
            self.connect()
            reconnect_attempts = 0  # Reset on successful connection
            
            # Start consuming messages from the "Request" queue
            self._channel.basic_consume(queue="Request", on_message_callback=self.on_request)
            self._channel.start_consuming()
                
            ''' except pika.exceptions.AMQPConnectionError:
                reconnect_attempts += 1
                print(f"Lost connection, attempting to reconnect... Attempt {reconnect_attempts}")
                time.sleep(5)
            except Exception as e:
                print(f"Encountered an error: {e}")
                break'''

        if reconnect_attempts >= self._max_reconnect_attempts:
            print("Reached maximum reconnection attempts. Stopping.")
        
        if reconnect_attempts >= self._max_reconnect_attempts:
            print(f"Thread {self._house} reached maximum reconnection attempts. Stopping thread.")

    

def main():
    print("Starting ICHistoricDataProducer...")
    # Get connection parameters
    connection_params = configurations.get('IChistoricalServer')
    ICHouses = DataSet.get_schema(os.path.join('..', configurations.get('ICfile').get('path')))

    producer = HistoricDataProducer(connection_params, ICHouses)
    producer.run()



if __name__ == "__main__":
    main()
