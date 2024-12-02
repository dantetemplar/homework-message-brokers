import json
import signal
import logging

from manage import channel

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

STOP_WORDS = {"bird-watching", "ailurophobia", "mango"}


def callback(ch, method, properties, body):
    message = json.loads(body)
    logging.info(f"Filter Service: Received message from {message.get('alias', 'unknown')} with content: {message.get('text', '')}")
    text = message.get("text", "")

    if not any(stop_word in text for stop_word in STOP_WORDS):
        logging.info(f"Filter Service: Message from {message.get('alias', 'unknown')} does not contain stop words, forwarding to next service")
        channel.basic_publish(exchange='',
                              routing_key='filtered_messages',
                              body=body)
    else:
        logging.info(f"Filter Service: Message from {message.get('alias', 'unknown')} contains stop words, rejecting")


def signal_handler(sig, frame):
    logging.info("Shutting down gracefully...")
    exit(0)


def main():
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    logging.info('Waiting for messages...')
    channel.basic_consume(queue="new_messages", on_message_callback=callback, auto_ack=True)
    channel.start_consuming()


if __name__ == "__main__":
    main()
