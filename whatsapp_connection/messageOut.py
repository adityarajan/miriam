# Begin by starting Whatsapp server: npx @open-wa/wa-automate --socket -p 8002 -k 'K6MEQJRV3trXMPZ5eQd1Jl8NaaaRZxqy'
from wa_automate_socket_client import SocketClient
import requests
from dotenv import dotenv_values

config_params = dotenv_values("whatsapp.env")

WHATSAPP_LINK = config_params["WHATSAPP_LINK"]
WHATSAPP_KEY = config_params["WHATSAPP_KEY"]
whatsApp_client = SocketClient(WHATSAPP_LINK, WHATSAPP_KEY)

CHAT_DB_LINK = config_params["CHAT_DB_LINK"]

message = """[Sys: 
Hi there!

We saw that your account has been messaging Isa recently and we'd love to get your feedback.

We'd be incredibly grateful if you could fill out the below form so we can integrate your suggestions and improve Isa!
 https://forms.gle/9kLypLXJAfhyUhmZ9.

Miriam team]"""

own_numbers = ["447510448215@c.us", "447810161994@c.us"]

phone_numbers = ["918218110327@c.us", "6591710989@c.us", "6597933764@c.us", "5511943052488@c.us", "16122574741@c.us", "85253331528@c.us", "447462807020@c.us", "6588752675@c.us", "5216674816990@c.us", "19163427263@c.us", "447915384208@c.us"] #requests.get(CHAT_DB_LINK + '/chat/all/numbers/').json()

for phone_number in own_numbers:
    whatsApp_client.sendText(phone_number, message)

confirm = input('Confirm you want to send to all users?')

for phone_number in phone_numbers:
    # get the chat of the phone number
    chat = requests.get(CHAT_DB_LINK + '/chat/get_chat/' + phone_number).json()
    #  check there are messages
    if len(chat["messages"]) > 0:
        print("Sending message to ", phone_number)
        whatsApp_client.sendText(phone_number, message)

# disconnect from whatsapp
whatsApp_client.disconnect()