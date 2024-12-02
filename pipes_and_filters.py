import os
import logging
import smtplib
import sys
from fastapi import FastAPI
from pydantic import BaseModel, Field
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from multiprocessing import Process, Pipe

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

STOP_WORDS = {"bird-watching", "ailurophobia", "mango"}

SMTP_SERVER = os.getenv('SMTP_SERVER', 'smtp.yandex.ru')
SMTP_PORT = int(os.getenv('SMTP_PORT', 587))
SMTP_USER = os.getenv('SMTP_USER')
SMTP_PASSWORD = os.getenv('SMTP_PASSWORD')

if not SMTP_USER or not SMTP_PASSWORD:
    raise ValueError("SMTP_USER and SMTP_PASSWORD environment variables must be set")

MAILING_LIST = []  # This will be populated from command-line arguments

app = FastAPI()

parent_conn1, child_conn1 = Pipe()  # For API to Filter
parent_conn2, child_conn2 = Pipe()  # For Filter to Screaming
parent_conn3, child_conn3 = Pipe()  # For Screaming to Emailing


class Message(BaseModel):
    text: str = Field(examples=["Hello, World!", "This is a message"])
    alias: str = Field(examples=["Alice", "Bob"])


@app.post("/messages/")
async def receive_message(message: Message):
    # Simulate receiving a message
    logging.info(f"API: Received message from {message.alias}")
    parent_conn1.send(message.model_dump())  # Send from API to Filter
    return {"status": "Message received", "message": message}


def filter_service(input_pipe, output_pipe):
    while True:
        message = input_pipe.recv()
        logging.info(f"Filter Service: Filtering message from {message['alias']}")
        if not any(stop_word in message['text'] for stop_word in STOP_WORDS):
            output_pipe.send(message)


def screaming_service(input_pipe, output_pipe):
    while True:
        message = input_pipe.recv()
        message['text'] = message['text'].upper()
        logging.info(f"Screaming Service: Converting message to uppercase: {message}")
        output_pipe.send(message)


def emailing_service(input_pipe):
    smtp_server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
    smtp_server.starttls()
    smtp_server.login(SMTP_USER, SMTP_PASSWORD)

    while True:
        message = input_pipe.recv()
        if MAILING_LIST == ["-"]:
            logging.info("Emailing Service: Mailing list is empty, not sending email")
        else:
            text = f"From user: {message['alias']}\nMessage: {message['text']}"
            msg = MIMEMultipart()
            msg['From'] = SMTP_USER
            msg['To'] = ", ".join(MAILING_LIST)
            msg['Subject'] = f"Message from {message['alias']}"
            msg.attach(MIMEText(text, 'plain'))
            logging.info(f"Emailing Service: Sending email to {MAILING_LIST} for message from {message['alias']}")
            smtp_server.sendmail(SMTP_USER, MAILING_LIST, msg.as_string())

    smtp_server.quit()


def main():
    if len(sys.argv) < 2:
        print("Usage: python pipes_and_filters.py <email1> <email2> ...")
        sys.exit(1)

    global MAILING_LIST
    MAILING_LIST = sys.argv[1:]
    filter_proc = Process(target=filter_service, args=(child_conn1, parent_conn2))  # Filter to Screaming
    screaming_proc = Process(target=screaming_service, args=(child_conn2, parent_conn3))  # Screaming to Emailing
    emailing_proc = Process(target=emailing_service, args=(child_conn3,))  # Final output

    logging.info("Starting filter, screaming, and emailing processes")
    filter_proc.start()
    screaming_proc.start()
    emailing_proc.start()

    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)


if __name__ == "__main__":
    main()
