import os
import smtplib
import sys
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import json
import signal

from manage import channel

MAILING_LIST: list[str]

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

SMTP_SERVER = os.getenv('SMTP_SERVER', 'smtp.yandex.ru')
SMTP_PORT = int(os.getenv('SMTP_PORT', 587))
SMTP_USER = os.getenv('SMTP_USER')
SMTP_PASSWORD = os.getenv('SMTP_PASSWORD')

if not SMTP_USER or not SMTP_PASSWORD:
    raise ValueError("SMTP_USER and SMTP_PASSWORD environment variables must be set")

smtp_server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
smtp_server.starttls()
smtp_server.login(SMTP_USER, SMTP_PASSWORD)


def send_email(subject, body, to_addresses, message):
    msg = MIMEMultipart()
    msg['From'] = SMTP_USER
    msg['To'] = ", ".join(to_addresses)
    msg['Subject'] = subject

    msg.attach(MIMEText(body, 'plain'))

    logging.info(f"Emailing Service: Sending email to {to_addresses} for message from {message['alias']}")
    smtp_server.sendmail(SMTP_USER, to_addresses, msg.as_string())


def callback(ch, method, properties, body):
    message = json.loads(body)
    logging.info(f"Emailing Service: Received message from {message['alias']}")
    text = f"From user: {message['alias']}\nMessage: {message['text']}"
    if MAILING_LIST == ["-"]:
        logging.info("Emailing Service: Mailing list is empty, not sending email")
    else:
        send_email(f"Message from {message['alias']}", text, MAILING_LIST, message)


def signal_handler(sig, frame):
    logging.info("Shutting down gracefully...")
    smtp_server.quit()

    exit(0)


def main():
    if len(sys.argv) < 2:
        print("Usage: python emailing_service.py <email1> <email2> ...")
        sys.exit(1)

    global MAILING_LIST
    MAILING_LIST = sys.argv[1:]

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    logging.info('Waiting for messages...')
    channel.basic_consume(queue='to_be_sent_messages', on_message_callback=callback, auto_ack=True)
    channel.start_consuming()


if __name__ == "__main__":
    main()
