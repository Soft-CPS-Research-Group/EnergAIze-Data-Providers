import pika

# Carregar configurações básicas
rabbitmq_config = {
    "host": "opevaisep.duckdns.org",  # Substitui pelo endereço do servidor RabbitMQ
    "port": 5672,
    "username": "softcps",
    "password": "softcpsmq",
    "exchange": "Garage"
}

def main():
    try:
        # Configurar as credenciais e parâmetros de conexão
        credentials = pika.PlainCredentials(rabbitmq_config["username"], rabbitmq_config["password"])
        connection_params = pika.ConnectionParameters(
            host=rabbitmq_config["host"],
            port=rabbitmq_config["port"],
            credentials=credentials,
            heartbeat=60
        )

        # Conectar ao RabbitMQ
        connection = pika.BlockingConnection(connection_params)
        channel = connection.channel()

        # Declarar a exchange e a fila temporária
        channel.exchange_declare(exchange=rabbitmq_config["exchange"], exchange_type='fanout')
        result = channel.queue_declare(queue='', exclusive=True)
        queue_name = result.method.queue

        # Associar a fila à exchange
        channel.queue_bind(exchange=rabbitmq_config["exchange"], queue=queue_name)

        print(f"Aguardando mensagens na fila: {queue_name}. Pressiona Ctrl+C para sair.")

        # Callback para imprimir mensagens recebidas
        def callback(ch, method, properties, body):
            print(f"Mensagem recebida: {body.decode('utf-8')}")

        # Consumir mensagens
        channel.basic_consume(queue=queue_name, on_message_callback=callback, auto_ack=True)
        channel.start_consuming()

    except KeyboardInterrupt:
        print("\nEncerrando...")
    except Exception as e:
        print(f"Erro: {e}")
    finally:
        try:
            connection.close()
        except:
            pass

if __name__ == "__main__":
    main()
