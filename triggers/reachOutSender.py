import sys
sys.path.insert(1, "")

import requests
from dotenv import dotenv_values
import time
from scheduler import process_request
from triggers_utils import reach_out_trigger

config_params = dotenv_values("triggers.env")
CHAT_DB_LINK = config_params["CHAT_DB_LINK"]


TIME_BETWEEN_REQUESTS = 60
TIME_BETWEEN_CHECKS = 60

sent_prompts = {}
while True:
    phone_numbers = requests.get(CHAT_DB_LINK + '/chat/all/numbers/').json()

    for phone_number in phone_numbers:
        print("Checking if we need to reach out to ", phone_number)
        # we check if we need to reach out
        if reach_out_trigger(phone_number):
            print("Sending reach out request for ", phone_number)
            process_request.delay(phone_number = phone_number, trigger = ("reach_out"))
            time.sleep(TIME_BETWEEN_REQUESTS)

    print("Round finished")
    time.sleep(TIME_BETWEEN_CHECKS)