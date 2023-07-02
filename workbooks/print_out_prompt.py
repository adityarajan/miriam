# MOVE INTO triggers FOLDER THEN RUN

import sys
sys.path.insert(1, "")

import requests
from dotenv import dotenv_values
import time
from scheduler import process_request
from triggers_utils import reach_out_trigger
import openai

from triggers_utils import check_trigger_valid, prompt_builder, check_valid_response, send_response, make_request_to_local_ai_manager

config_params = dotenv_values("triggers.env")
CHAT_DB_LINK = config_params["CHAT_DB_LINK"]


phone_numbers = requests.get(CHAT_DB_LINK + '/chat/all/numbers/').json()
# suffle phone numbers
import random
random.shuffle(phone_numbers)
for phone_number in phone_numbers:
    chat = requests.get(CHAT_DB_LINK + '/chat/get_chat/' + phone_number).json()
    messages = chat["messages"]
    if len(messages) > 20:
        prompt = prompt_builder(phone_number, "unreplied")
        # remove the second to last element from prompt
        prompt = prompt[:-2] + [prompt[-1]]
        # print each element in list of prompt on new line
        print(*prompt, sep = "\n")
        response = make_request_to_local_ai_manager(prompt)
        print("Response: \n" + response)
        readln = input("Press enter to continue")