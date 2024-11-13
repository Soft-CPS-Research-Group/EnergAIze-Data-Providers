import pika
import json

# Global variable to indicate whether a response has been received
response_received = False
response_body = None  # Variable to store the response

# Definindo a conexão com o servidor RabbitMQ
connection = pika.BlockingConnection(pika.ConnectionParameters(host='localhost'))
channel = connection.channel()

# Declarando a fila "Request"
channel.queue_declare(queue='Request', durable=True)

# Mensagem a ser enviada
installation_name = "House1"
message = {
    "type": "historic",
    "value": {
        "installation": installation_name,
        "date": "04-11-2024 00:00:00"
    }
}
message_json = json.dumps(message)  # Convertendo a mensagem para JSON

# Cria uma fila temporária para receber a resposta
result = channel.queue_declare(queue='', exclusive=True)
callback_queue = result.method.queue

# Função de callback para processar a resposta
def on_response(ch, method, properties, body):
    global response_received, response_body
    response_received = True  # Set the flag to True
    response_body = body.decode()  # Store the response body

# Consumindo mensagens da fila de resposta
channel.basic_consume(queue=callback_queue, on_message_callback=on_response, auto_ack=True)

# Enviando a mensagem para a fila com a propriedade reply_to
channel.basic_publish(
    exchange='',
    routing_key='Request',
    body=message_json,
    properties=pika.BasicProperties(
        reply_to=callback_queue  # Define a fila de resposta como a fila temporária
    )
)

print("Mensagem enviada:", message_json)

# Espera a resposta
print("Esperando resposta...")
while not response_received:
    connection.process_data_events()  # Process any incoming messages

# Print the response after it is received
print("Resposta recebida:", response_body)

# Fechando a conexão
connection.close()
