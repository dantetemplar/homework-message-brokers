from fastapi import FastAPI
from pydantic import BaseModel, Field
import logging
from starlette.requests import Request

from manage import channel

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

app = FastAPI()


class Message(BaseModel):
    text: str = Field(examples=["Hello, World!", "This is a message"])
    alias: str = Field(examples=["Alice", "Bob"])


@app.post("/messages/")
async def receive_message(message: Message, request: Request):
    # Publish the message to the queue
    client_host = request.client.host
    logging.info(f"API: Received message from {message.alias} at {client_host} on /messages/ endpoint")
    channel.basic_publish(exchange='',
                          routing_key='new_messages',
                          body=message.model_dump_json())

    return {"status": "Message received", "message": message}


if __name__ == '__main__':
    import uvicorn

    uvicorn.run(app)
