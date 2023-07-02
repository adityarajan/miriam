# Begin by starting Whatsapp server: npx @open-wa/wa-automate --socket -p 8002 -k 'K6MEQJRV3trXMPZ5eQd1Jl8NaaaRZxqy'
from wa_automate_socket_client import SocketClient
import requests
from dotenv import dotenv_values

config_params = dotenv_values("whatsapp.env")

WHATSAPP_LINK = config_params["WHATSAPP_LINK"]
WHATSAPP_KEY = config_params["WHATSAPP_KEY"]
whatsApp_client = SocketClient(WHATSAPP_LINK, WHATSAPP_KEY)

CHAT_DB_LINK = config_params["CHAT_DB_LINK"]
TRANSCRIBER_LINK = "http://127.0.0.1:8005"

AI_NAME = "Isa"

import base64


def messageIn(whatsapp_message):
    print(whatsapp_message["data"]["type"])
    whatsapp_message_data = whatsapp_message['data']
    phone_number = whatsapp_message_data["from"] # the user number is treated as the chat_id
    message_content = whatsapp_message_data['body']
    print(message_content)
    print(phone_number)

    if whatsapp_message["data"]["type"] == 'ptt':
        decrypted_media = whatsApp_client.decryptMedia(whatsapp_message['data'])
        # we need to send the decrypted media to the transcriber
        params = {
            'decrypted_media': decrypted_media,
            'phone_number': phone_number
        }
        requests.post(TRANSCRIBER_LINK + '/', json=params)

    print(whatsapp_message)







    return True

whatsApp_client.onMessage(messageIn)

input()


# whatsApp_client.onMessage(messageIn)

# whatsApp_client.message