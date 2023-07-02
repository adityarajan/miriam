# Begin by starting Whatsapp server: npx @open-wa/wa-automate --socket -p 8002 -k 'K6MEQJRV3trXMPZ5eQd1Jl8NaaaRZxqy'
from wa_automate_socket_client import SocketClient
import requests
from dotenv import dotenv_values

config_params = dotenv_values("whatsapp.env")

WHATSAPP_LINK = config_params["WHATSAPP_LINK"]
WHATSAPP_KEY = config_params["WHATSAPP_KEY"]
whatsApp_client = SocketClient(WHATSAPP_LINK, WHATSAPP_KEY)

CHAT_DB_LINK = config_params["CHAT_DB_LINK"]
TRANSCRIBER_LINK = config_params["TRANSCRIBER_LINK"]

AI_NAME = "Isa"

def handle_command(phone_number, message_content):
    if message_content == "/reset":
        r = requests.delete(CHAT_DB_LINK + f'/chat/delete_messages/{phone_number}')
        whatsApp_client.sendText(phone_number, "[Sys: Messages reset]")
        print(r)
        return True
    
    if message_content == "/safe":
        params = {
                'str_param': "(stop_reaching_out)"
            }
            
        r =requests.put(CHAT_DB_LINK + '/chat/add_str_param/' + phone_number, json=params)
        whatsApp_client.sendText(phone_number, f"[Sys: {AI_NAME} won't reach out anymore]")
        print(r)
        return True

    if message_content.startswith("/9j"):
        whatsApp_client.sendText(phone_number, f"[Sys: {AI_NAME} can't do images yet]")
        return True
    
    return False
    
def messageIn(whatsapp_message):
    print("Message incoming")

    # We get the message and the user who sent it
    whatsapp_message_data = whatsapp_message['data']
    phone_number = whatsapp_message_data["from"] # the user number is treated as the chat_id
    message_content = whatsapp_message_data['body']

    try:
        message_push_name = whatsapp_message_data["sender"]["pushname"]
    except:
        message_push_name = "Friend"

    params = {
        'user_name': message_push_name,
        'phone_number': phone_number,
        'content': message_content,
        'from_us': False
    }

    # if message contant starts with /, when its a command, or when its and image, as well as the error case of an empty message
    if message_content.startswith("/"):
        return handle_command(phone_number, message_content)
    
    
    if whatsapp_message["data"]["type"] == 'ptt':
        print("Message is an audio message")
        decrypted_media = whatsApp_client.decryptMedia(whatsapp_message['data'])
        # we need to send the decrypted media to the transcriber
        params = {
            'decrypted_media': decrypted_media,
            'user_name': message_push_name,
            'phone_number': phone_number
        }
        requests.post(TRANSCRIBER_LINK + '/', json=params)

        return True

    r =requests.post(CHAT_DB_LINK + f'/chat/add_message/{phone_number}', json=params)
    print(r)
    print("added message to chat db: " + message_content + " from " + message_push_name + " (" + phone_number + ")")

    config_params = dotenv_values("whatsapp.env")
    ERROR_STATE = config_params["ERROR_STATE"]
    ERROR_MESSAGE = config_params["ERROR_MESSAGE"]
    if ERROR_STATE == True:
        whatsApp_client.sendText(phone_number, ERROR_MESSAGE)
        return False

    return True

whatsApp_client.onMessage(messageIn)

