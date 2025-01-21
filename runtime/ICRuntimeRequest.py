import pika
import os
import json
import sys
import uuid
from ICTranslator import ICTranslator
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from data import DataSet

# Load configurations
configurations = DataSet.get_schema(os.path.join('..', 'runtimeConfigurations.json'))

    
def main():
    print("Starting ICRuntimeRequest...")
    # Get CW Houses file and turn it into a dictionary
    ICHouses = DataSet.get_schema(os.path.join('..', configurations.get('ICfile').get('path')))
    # Remove provider key because it does not contain any useful information here
    ICHouses.pop('provider')

    frequency = DataSet.calculate_interval(configurations.get('frequency'))        

    print(f"Houses: {list(ICHouses.keys())}")
    print(f"Frequency sent: {frequency}")

    message = {
        "type": "runtime",
        "value":{
            "installations": list(ICHouses.keys()),
            "frequency": frequency
        } 
    }

    _send_message(json.dumps(message))

def _send_message(message):
        # Get connection parameters
        connection_params = configurations.get('ICserver')
        connection_params = pika.ConnectionParameters(host=connection_params.get('host'), port=connection_params.get('port'),credentials=pika.PlainCredentials(connection_params.get('credentials').get('username'), connection_params.get('credentials').get('password')), heartbeat=660)
        connection = pika.BlockingConnection(connection_params)
        channel = connection.channel()
        channel.queue_declare(queue='RPC', durable=True)
        returnQueueName = channel.queue_declare(queue='', exclusive=True)
        
        channel.basic_publish(
            exchange='',
            routing_key='RPC',
            body=message,
            properties=pika.BasicProperties(
                reply_to=returnQueueName.method.queue,
                message_id=str(uuid.uuid4())
            )
        )

        channel.basic_consume(
            queue=returnQueueName.method.queue,
            on_message_callback=on_response,
            auto_ack=True
        )

        # Start consuming
        channel.start_consuming()

def on_response(ch, method, properties, body):
        print("Received response:", body.decode())
        ch.stop_consuming()
        ch.close()


if __name__ == "__main__":
    main()
