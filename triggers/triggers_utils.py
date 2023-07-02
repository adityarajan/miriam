import requests
from dotenv import dotenv_values
import time
import openai
import re
import random

from transformers import GPT2TokenizerFast
tokenizer = GPT2TokenizerFast.from_pretrained("gpt2")

from dotenv import dotenv_values

config_params = dotenv_values("triggers.env")
CHAT_DB_LINK = config_params["CHAT_DB_LINK"]

from wa_automate_socket_client import SocketClient
WHATSAPP_LINK = config_params["WHATSAPP_LINK"]
WHATSAPP_KEY = config_params["WHATSAPP_KEY"]


def reach_out_trigger(phone_number):
    #  we check if the chat is unreplied
    last_message_in_chat = requests.get(CHAT_DB_LINK + '/chat/last_message/' + phone_number).json()
    if last_message_in_chat["content"]:
        if last_message_in_chat["from_us"] == True and abs(time.time()-last_message_in_chat["time"])>3600*24*10:
            # we get the messages in the chat
            chat = requests.get(CHAT_DB_LINK + '/chat/get_chat/' + phone_number).json()
            # we make sure the chat has had enough messages for the user to be properly engaged
            if len(chat["messages"])<10:
                return False

            # we make sure the last two messages aren't from us
            if chat["messages"][-2]["from_us"] == True and chat["messages"][-1]["from_us"] == True:
                return False
            
            messages = chat["messages"]
            
            # we get the times of the messages not sent by us
            times = [message["time"] for message in messages if message["from_us"] == False]
            # we take the modulo with the number of seconds in a day to get seconds into the day the message was sent
            times = [msg_time % (24 * 3600) for msg_time in times]
            # we return the median msg_time in times
            median_time = sorted(times)[len(times)//2]
            # we get the current time
            current_time = time.time() % (24 * 3600)
            print("CANDIDATE : phone_number: ", phone_number, " median_time: ", median_time, " current_time: ", current_time, " last_message_time: ", last_message_in_chat["time"])
            if abs(median_time-current_time)<3600:
                print("CANDIDATE within 1 hour")
                return True
            return False


def unreplied_chats_trigger(phone_number):
    # we check if the chat is unreplied
    last_message_in_chat = requests.get(CHAT_DB_LINK + '/chat/last_message/' + phone_number).json()

    if last_message_in_chat["content"]:
        if last_message_in_chat["from_us"] == False:
            return True
    return False

def build_messages_body_prompt(phone_number, max_tokens_length = 2000):
    print("building messages body prompt")
    # we get the chat from the database
    chat = requests.get(CHAT_DB_LINK + '/chat/get_chat/' + phone_number).json()
    # we get the messages from the chat
    messages = chat["messages"]
    # we get the user_name and ai_name from the prompt_params of the chat
    user_name = chat["prompt_params"]["user_name"]
    # filter username keeping alphanumeric characters only
    pattern = r'[^a-zA-Z0-9_-]'
    user_name = re.sub(pattern, '', user_name)

    ai_name = "Isa" # chat["prompt_params"]["ai_name"]

    def get_last_messages(messages, tokens_length = max_tokens_length):
        # going backwords from the last message, we get the messages until we have 600 words
        total_tokens = 0
        messages_to_send = []
        reversed_messages = messages[::-1]
        for message_object in reversed_messages:
            tokens_length = len(tokenizer(message_object["content"])['input_ids'])
            total_tokens += tokens_length
            if total_tokens > max_tokens_length:
                print("Message not appending, total tokens is now: ", total_tokens)
                break
            messages_to_send.append(message_object)

        # we reverse the messages to send so that they are in the correct order again
        messages_to_send = messages_to_send[::-1]
        return messages_to_send

    messages_to_send = get_last_messages(messages)

    # {"role": "user", "content": "Who won the world series in 2020?"},
    # {"role": "assistant", "content": "The Los Angeles Dodgers won the World Series in 2020."},
    messages_body_prompt = []
    previous_message_sender = -1
    for i in range(len(messages_to_send)):
        message = messages_to_send[i]
        if len(message["content"]) == 0:
            continue

        if message["from_us"] == previous_message_sender:
            messages_body_prompt[-1] = {"role": messages_body_prompt[-1]["role"], "content": messages_body_prompt[-1]["content"] + ", " + message["content"]}
        else:
            if message["from_us"] == True:
                messages_body_prompt.append({"role": "assistant", "content": message["content"], "name": ai_name})
                previous_message_sender = True
            else:
                if len(user_name) == 0:
                    messages_body_prompt.append({"role": "user", "content": message["content"]})
                else:
                    messages_body_prompt.append({"role": "user", "content": message["content"], "name": user_name})
                previous_message_sender = False
    
    return messages_body_prompt


def prompt_builder(phone_number, trigger):
    config_params = dotenv_values("triggers.env")
    
    prompt_params = requests.get(CHAT_DB_LINK + '/chat/get_prompt_params/' + phone_number).json()
    user_name = prompt_params["user_name"]
    ai_name = "Isa" # prompt_params["ai_name"]

    if trigger == "reach_out" or trigger == "unreplied" or trigger == "unreplied_advice" or trigger == "unreplied_old_user" or trigger == "unreplied_old_user_advice":
        print(f"building prompt for {trigger}")
        sys_msg = config_params[f"{trigger}_sys_msg"]

        sys_msg = sys_msg.replace("Lucy", user_name)
        sys_msg = sys_msg.replace("Isa", ai_name)

        end_sys_message =config_params[f"{trigger}_end_sys_msg"]

        end_sys_message = end_sys_message.replace("Lucy", user_name)
        end_sys_message = end_sys_message.replace("Isa", ai_name)

    else:
        print(f"{trigger} is invalid")
        return None

    if prompt_params["use_custom_user_desc_prompt"]:
        custom_user_desc_prompt = prompt_params["custom_user_desc_prompt"]
        custom_user_desc_prompt = custom_user_desc_prompt.replace("Lucy", user_name)
        custom_user_desc_prompt = custom_user_desc_prompt.replace("Isa", ai_name)
        sys_msg = custom_user_desc_prompt
        # Q : Can each user have a custom end_sys_message?
    
    # we build the chat section of the prompt
    messages_body_prompt = build_messages_body_prompt(phone_number)
    sys_prompt = [{"role": "system", "content": sys_msg}]

    end_sys_prompt = [{"role": "system", "content": end_sys_message}]
    prompt = sys_prompt + messages_body_prompt + end_sys_prompt
    
    return prompt


def check_trigger_valid(phone_number, trigger):
    if trigger == "reach_out":
        if reach_out_trigger(phone_number) == True:
            print(f"{trigger} trigger is valid")
        else:
            print("Trigger is no longer valid")
            return False
        return True
    elif trigger == "unreplied":
        if unreplied_chats_trigger(phone_number) == True:
            print(f"{trigger} trigger is valid")
            return True
        else:
            print("Trigger is no longer valid")
            return False
    # if trigger starts with "rewrite"
    elif trigger.startswith("rewrite"):
        # check still unreplied
        if unreplied_chats_trigger(phone_number) == True:
            print(f"{trigger} trigger - chat still unreplied")
            return True
    else:
        print(f"{trigger} is invalid")
        return False


def make_request_to_local_ai_manager(prompt):
    API_KEY = config_params["API_KEY"]
    REPETITION_PENALTY = float(config_params["REPETITION_PENALTY"])
    # TODO: LOGIT_BIAS = config_params["LOGIT_BIAS"]
    LOGIT_BIAS = {16676: -10, 39443: -50, 25: -90, 10814:-30, 17250: -30}

    response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                api_key=API_KEY,
                messages=prompt,
                frequency_penalty = REPETITION_PENALTY,
                logit_bias = LOGIT_BIAS,
                )["choices"][0]["message"]["content"]
    
    print("Response received from local AI manager ", response)
    return response


def whatsapp_send_message(phone_number, message):
    whatsApp_client = SocketClient(WHATSAPP_LINK, WHATSAPP_KEY)
    whatsApp_client.sendText(phone_number, message)
    whatsApp_client.disconnect()
    return True

def check_valid_response(phone_number, response):
    chat = requests.get(CHAT_DB_LINK + '/chat/get_chat/' + phone_number).json()
    user_name = chat["prompt_params"]["user_name"]
    ai_name = "Isa" # chat["prompt_params"]["ai_name"]

    if response == None:
        return (response, False, "(response_none)")

    if len(response) == 0:
        return (response, False, "(response_length_0)")
    
    if len(response) > 4000:
        return (response, False, "(response_too_long)")

    if response.startswith("[Isa]:"):
        response = response[6:]
    
    if response.startswith("Isa:"):
        response = response[4:]

    if response.startswith("Isa: "):
        response = response[5:]
    
    if response.startswith("Isa\n"):
        response = response[3:]

    if response.startswith("Isa"):
        response = response[3:]


    # we replace problematic parts in response with alternatives
    replacements = [
        ("chatGPT", "deep learning model"),
        ("ChatGPT", "Deep Learning models"),
        ("OpenAI", "Miriam"),
        ("openAI", "Miriam"),
        ("Assistant", "Friend"),
        ("assistant", "friend"),
        ("Generative Pre-trained Transformer", "Deep Learning model")
    ]
    for word, replacement in replacements:
        response = response.replace(word, replacement)

    # if the response is in quote marks, remove the quote marks
    if response[0] == '"' and response[-1] == '"':
        response = response[1:-1]

    if ":" in response[:10]:
        return (response, False, "(response_contains_:_early)")
    
    if f"[{user_name}]" in response or f"[{ai_name}]" in response:
        return (response ,False, "(response_contains_[name])")
    if f"[{user_name}]" in response or f"[{user_name}]" in response:
        return (response ,False, "(response_contains_[name])")

    if f"[{user_name}]" in response or f"{ai_name}:" in response:
        return (response ,False, "(response_contains_[name])")
    if f"[{user_name}]" in response or f"{user_name}:" in response:
        return (response ,False, "(response_contains_[name])")

    print("Response is valid : ", response)
    return (response, True, "all good")

def send_response(phone_number, response, add_to_database=True, message_to_store = None):
    if message_to_store == None:
            message_to_store = response

    params = {
        'phone_number': phone_number,
        'content': message_to_store,
        'from_us': True
    }

    if add_to_database:
        # add the response to the database
        r =requests.post(CHAT_DB_LINK + '/chat/add_message/' + phone_number, json=params)
        print("Added message to chat ", r.json())

    # send off the response on whatsapp
    whatsapp_send_message(phone_number, response)
    print("Sent message on whatsapp")

    return (response, True, "all good")