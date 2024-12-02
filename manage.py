import pika

credentials = pika.PlainCredentials('rmuser', 'rmpassword')
connection_params = pika.ConnectionParameters('localhost', credentials=credentials)

connection = pika.BlockingConnection(connection_params)
channel = connection.channel()

channel.queue_declare(queue="new_messages")
channel.queue_declare(queue="filtered_messages")
channel.queue_declare(queue="to_be_sent_messages")
