import requests
from dotenv import dotenv_values
import time
import random

from scheduler import process_request

config_params = dotenv_values("triggers.env")
CHAT_DB_LINK = config_params["CHAT_DB_LINK"]

sent_prompts = {}

while True:
    phone_numbers = requests.get(CHAT_DB_LINK + '/chat/unreplied_chats/').json()
    random.shuffle(phone_numbers)
    for phone_number in phone_numbers:
        print("Sending unreplied request for ", phone_number)
        process_request.delay(phone_number = phone_number, trigger = "unreplied")
        time.sleep(6)

    print("Round finished")
