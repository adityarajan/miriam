# docker run -d -p 5672:5672 rabbitmq
# celery -A chatAPI worker --loglevel=INFO --concurrency=1

from celery import Celery
import requests
from dotenv import dotenv_values
import random

config_params = dotenv_values("triggers.env")
CHAT_DB_LINK = config_params["CHAT_DB_LINK"]
INTRODUCTION_TO_CHATBOT_MESSAGE_SENT = config_params["INTRODUCTION_TO_CHATBOT_MESSAGE_SENT"]
INTRODUCTION_TO_CHATBOT_MESSAGE_STORED = config_params["INTRODUCTION_TO_CHATBOT_MESSAGE_STORED"]

CELERY_BROKER = config_params["CELERY_BROKER"]
app = Celery('tasks', broker=CELERY_BROKER)

from triggers_utils import check_trigger_valid, prompt_builder, make_request_to_local_ai_manager, check_valid_response, send_response

@app.task(time_limit=35)
def process_request(phone_number, trigger):
    try:
        print("Processing request for " + phone_number + " with trigger " + trigger)

        # check trigger is still valid
        print("Checking trigger is still valid")
        if check_trigger_valid(phone_number, trigger) == False:
            return None

        # get chat - for freezepoint check to see if chat updated later
        print("Getting chat")
        chat = requests.get(CHAT_DB_LINK + '/chat/get_chat/' + phone_number).json()

        # TODO: logic for last message being of some type (e.g. is first message and hello, or "are you free?" etc.)
        # get the messages in the chat
        messages = requests.get(CHAT_DB_LINK + '/chat/get_messages/' + phone_number).json()
        # get the length of the messages
        if len(messages) < 3:
            # and all the messages are not from us
            if all(message["from_us"] == False for message in messages):
                # message to send is INTRODUCTION_TO_CHATBOT_MESSAGE_SENT with Lucy replaced with user_name
                user_name = chat["prompt_params"]["user_name"]
                message_to_send = INTRODUCTION_TO_CHATBOT_MESSAGE_SENT.replace("Lucy", user_name)
                message_to_store = INTRODUCTION_TO_CHATBOT_MESSAGE_STORED.replace("Lucy", user_name)
                send_response(phone_number, message_to_send, message_to_store = message_to_store)
                return True

        # build prompt
        print("Building prompt")
        # copy trigger into sub_trigger

        sub_trigger = trigger +''
        if trigger == "unreplied":
            if len(messages) > 30 and trigger == "unreplied":
                sub_trigger = sub_trigger + "_old_user"
                
            mode = random.randint(1, 3)
            if mode == 3 and trigger == "unreplied":
                sub_trigger = sub_trigger + "_advice"

        
        prompt = prompt_builder(phone_number, sub_trigger)
            
        # print each element in list prompt on new line
        for message in prompt:
            print(message)
        # get response
        print("Making request to local AI manager \n")
        response = make_request_to_local_ai_manager(prompt)

        print("Response: " + response)

        # check chat has not been updated since request was made
        print("Checking chat has not been updated since request was made")
        check_chat = requests.get(CHAT_DB_LINK + '/chat/get_chat/' + phone_number).json()
        if chat != check_chat:
            print("Chat has been updated since request was made.")
            return None

        # check response is valid - we give phone nhumber for error management in check_valid_response
        print("Checking response is valid")
        response, validity, reason = check_valid_response(phone_number, response)
        # if valid, add response to chat
        if validity == True:
            print("Response is valid")
            send_response(phone_number, response)
            print(f"{phone_number} task has been handled")
            if len(response) > 400:
                if not ("(used_voice_message)" in chat["str_params"]) and not ("(informed_about_voice_message)" in chat["str_params"]):
                    print(f"{phone_number} reply was long, notifying user of voice messaging - for first and only time")
                    send_response(phone_number, "Also, I just wanted to add, feel free to reply to me with a voice message, I can understand it perfectly.", add_to_database=False)
                    params_voice_notified = {
                        'str_param': "(informed_about_voice_message)"
                    }
                    r =requests.put(CHAT_DB_LINK + f'/chat/add_str_param/{phone_number}', json=params_voice_notified)
                    print(r)
                if len(check_chat["messages"]) > 50 and not ("(suggested_sharing)" in check_chat["str_params"]):
                    print(f"Suggesting sharing Isa with a friend for {phone_number}")
                    sharing_message = "Also, as a side note, I just wanted to ask, if you have a friend who you think would benefit from talking to me, please share me with them. I'd love to help them too. (You can send them my contact or the link: isa.miriamtherapy.org)"
                    sharing_message_store = "Also, I just wanted to ask, if you have a friend who you think would benefit from talking to me, please share my contact with them. I'd love to be able to help them too."
                    send_response(phone_number, sharing_message, add_to_database=True, message_to_store=sharing_message_store)
                    params_sharing_suggested = {
                        'str_param': "(suggested_sharing)"
                    }
                    r =requests.put(CHAT_DB_LINK + f'/chat/add_str_param/{phone_number}', json=params_sharing_suggested)



            return True
        if validity == False:
            if reason == "(rollback_ai_prompt)":
                print(f"Response has repeated reference to machines, rolled back, {phone_number} task has been handled")
                return True

            print("Response is invalid: " + reason + " - " + response)
            print(f"{phone_number} task has been dropped for now, will be re triggered")
            return False

    except Exception as e:
        print(e)
        return None