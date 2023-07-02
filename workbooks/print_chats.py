import sys
sys.path.insert(1, "")

import requests
from dotenv import dotenv_values


config_params = dotenv_values("triggers.env")
CHAT_DB_LINK = config_params["CHAT_DB_LINK"]


TIME_BETWEEN_DAY_CHECKS = 10000
TIME_BETWEEN_REQUESTS = 200

sent_prompts = {}
phone_numbers = requests.get(CHAT_DB_LINK + '/chat/all/numbers/').json()
number_thanks = 0
true_conversation = 0
for phone_number in phone_numbers:
    chat = requests.get(CHAT_DB_LINK + '/chat/get_chat/' + phone_number).json()
    # we get the messages from the chat
    messages = chat["messages"]
    if len(messages) > 0:
        true_conversation += 1
    messages_content = ""
    for message_object in messages:
        if message_object["from_us"] == False:
            if "thank" in message_object["content"].lower():
                number_thanks += 1
                print(phone_number, message_object["content"])
                break

print(len(phone_numbers))
print("Number of thanks: ", number_thanks)
print("Number of true conversations: ", true_conversation)