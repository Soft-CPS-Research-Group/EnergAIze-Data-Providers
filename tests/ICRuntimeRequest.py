import pika
import json

rabbitmq_config = {
    "host": "opevaisep.duckdns.org", 
    "port": 5672,
    "username": "softcps",
    "password": "softcpsmq",
}

def main():
    message = {
        "type": "runtime",
        "value":{
            "installations": ["Garage"],
            "frequency": 0
        } 
    }

    _send_message(json.dumps(message))

def _send_message(message):
        credentials = pika.PlainCredentials(rabbitmq_config["username"], rabbitmq_config["password"])
        connection_params = pika.ConnectionParameters(
            host=rabbitmq_config["host"],
            port=rabbitmq_config["port"],
            credentials=credentials,
            heartbeat=60
        )        
        connection = pika.BlockingConnection(connection_params)
        channel = connection.channel()

        channel.queue_declare(queue='RPC', durable=True)
        returnQueueName = channel.queue_declare(queue='', exclusive=True)
        
        channel.basic_publish(
            exchange='',
            routing_key='RPC',
            body=message,
            properties=pika.BasicProperties(
                reply_to=returnQueueName.method.queue
            )
        )

        channel.basic_consume(
            queue=returnQueueName.method.queue,
            on_message_callback=on_response,
            auto_ack=False
        )

        # Start consuming
        channel.start_consuming()

def on_response(ch, method, properties, body):
        print("Received response:", body.decode())
        ch.basic_ack(delivery_tag=method.delivery_tag)
  


if __name__ == "__main__":
    main()
