import json
import logging
import signal

from manage import channel

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


def callback(ch, method, properties, body):
    message = json.loads(body)
    logging.info(f"Screaming Service: Received message from {message.get('alias', 'unknown')}")
    message["text"] = message.get("text", "").upper()
    body = json.dumps(message)
    channel.basic_publish(exchange='',
                          routing_key='to_be_sent_messages',
                          body=body)


def signal_handler(sig, frame):
    logging.info("Shutting down gracefully...")
    exit(0)


def main():
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    logging.info('Waiting for messages...')
    channel.basic_consume(queue='filtered_messages',
                          on_message_callback=callback,
                          auto_ack=True)
    channel.start_consuming()


if __name__ == "__main__":
    main()
