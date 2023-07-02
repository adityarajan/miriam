from fastapi import APIRouter, Body, Request, Response, HTTPException, status
from fastapi.encoders import jsonable_encoder
from typing import List
import time
from dotenv import dotenv_values

config_params = dotenv_values("chat_db.env")

from models import Chat, Message, PromptParams, Reminder

router = APIRouter()

# create chat from database
@router.post("/create_chat", response_description="Create new user account if doesn't exist", status_code=status.HTTP_201_CREATED, response_model=Chat)
def create_chat(request: Request, body = Body({})):
    try:
        phone_number = body.get("phone_number")
        chat = Chat(phone_number=phone_number)

        name = body.get("name").split(" ")[0].capitalize()
        prompt_params = PromptParams(user_name=name)
        chat.prompt_params = prompt_params

        request.app.database["chats"].insert_one(chat.dict())

        return chat
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

# check if there is a chat with given phone number, if not then create, and add message from body
@router.post("/add_message/{phone_number}", response_description="Add message to chat", status_code=status.HTTP_201_CREATED, response_model=Message)
def add_message(request: Request, phone_number: str, body = Body({})):
    try:
        chat = request.app.database["chats"].find_one({"phone_number": phone_number})
        if not chat:
            chat = Chat(phone_number=phone_number)
            user_name = body.get("user_name").split(" ")[0].capitalize()

            prompt_params = PromptParams(user_name=user_name)
            chat.prompt_params = prompt_params

            request.app.database["chats"].insert_one(chat.dict())

        chat = request.app.database["chats"].find_one({"phone_number": phone_number})
        messages = chat["messages"]
        from_us = body.get("from_us")
        time_ = body.get("time", time.time())
        content = body.get("content")
        if len(content) > 0:
            message = Message(from_us=from_us, time=time_, content=content)

            messages.append(message.dict())
        

        request.app.database["chats"].update_one({"phone_number": phone_number}, {"$set": {"messages": messages}})
        try:
            if chat["user_name"] == "Friend":
                prompt_params = chat["prompt_params"]
                print("Prompt params", prompt_params)
                user_name = body.get("user_name").split(" ")[0].capitalize()
                print("username to update to ", user_name)
                prompt_params["user_name"] = user_name
                request.app.database["chats"].update_one({"phone_number": phone_number}, {"$set": {"prompt_params": prompt_params}})
        except:
            print("Something went wrong with updating user_name")

        return message
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

# read chat from database
@router.get("/get_chat/{phone_number}", response_description="Get chat from database", response_model=Chat)
def get_chat(request: Request, phone_number: str):
    try:
        chat = request.app.database["chats"].find_one({"phone_number": phone_number})
        if chat:
            return chat
        else:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Chat with phone number {phone_number} not found")

    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

# update chat from database
@router.put("/update_chat/{phone_number}", response_description="Update chat from database", response_model=Chat)
def update_chat(request: Request, phone_number: str, body = Body({})):
    try:
        chat = request.app.database["chats"].find_one({"phone_number": phone_number})
        if chat:
            change = body.dict()
            request.app.database["chats"].update_one({"phone_number": phone_number}, {"$set": change})
            return request.app.database["chats"].find_one({"phone_number": phone_number})
        else:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Chat with phone number {phone_number} not found")

    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

# delete chat from database
@router.delete("/delete_chat/{phone_number}", response_description="Delete chat from database")
def delete_chat(request: Request, phone_number: str):
    try:
        chat = request.app.database["chats"].find_one({"phone_number": phone_number})
        if chat:
            request.app.database["chats"].delete_one({"phone_number": phone_number})
            return Response(status_code=status.HTTP_204_NO_CONTENT)
        else:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Chat with phone number {phone_number} not found")
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

# add an error to last message in chat
@router.put("/add_error/{phone_number}", response_description="Add new error to message", status_code=status.HTTP_201_CREATED, response_model=Message)
def add_error(request: Request, phone_number: str, message_id: str, body = Body({})):
    try:
        chat = request.app.database["chats"].find_one({"phone_number": phone_number})
        if chat:
            messages = chat["messages"]
            last_message = messages[-1]
            errors = last_message["errors"]
            error = body.get("error")
            # add new error to errors, and update message
            errors.append(error)
            last_message["errors"] = errors
            request.app.database["chats"].update_one({"phone_number": phone_number}, {"$set": {"messages": messages}})
            return messages[-1]
        else:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Chat with phone number {phone_number} not found")
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

# for an error in a message, remove a single instances of a specific error
@router.put("/remove_single_instance_error/{phone_number}/{message_id}", response_description="Remove error from message", status_code=status.HTTP_201_CREATED, response_model=Message)
def remove_error(request: Request, phone_number: str, message_id: str, body = Body({})):
    try:
        chat = request.app.database["chats"].find_one({"phone_number": phone_number})
        if chat:
            messages = chat["messages"]
            for message in messages:
                if message["id"] == message_id:
                    errors = message["errors"]
                    error = body.get("error")
                    # remove a single instance of the error
                    errors.remove(error)
                    message["errors"] = errors
                    request.app.database["chats"].update_one({"phone_number": phone_number}, {"$set": {"messages": messages}})
                    return message
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Message with id {message_id} not found")
        else:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Chat with phone number {phone_number} not found")
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


# for an error in a message, remove all instances of a specific error
@router.put("/remove_all_instances_error/{phone_number}/{message_id}", response_description="Remove error from message", status_code=status.HTTP_201_CREATED, response_model=Message)
def remove_error(request: Request, phone_number: str, message_id: str, body = Body({})):
    try:
        chat = request.app.database["chats"].find_one({"phone_number": phone_number})
        if chat:
            messages = chat["messages"]
            for message in messages:
                if message["id"] == message_id:
                    errors = message["errors"]
                    error = body.get("error")
                    # remove all instances of error from errors, and update message
                    errors = [e for e in errors if e != error]
                    message["errors"] = errors
                    request.app.database["chats"].update_one({"phone_number": phone_number}, {"$set": {"messages": messages}})
                    return message
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Message with id {message_id} not found")
        else:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Chat with phone number {phone_number} not found")
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

# get the str_params of a chat
@router.get("/get_str_params/{phone_number}", response_description="Get str_params of chat", response_model=List[str])
def get_str_params(request: Request, phone_number: str):
    try:
        chat = request.app.database["chats"].find_one({"phone_number": phone_number})
        if chat:
            return chat["str_params"]
        else:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Chat with phone number {phone_number} not found")

    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


#  add an str_param to str_params in chat based on phone number
@router.put("/add_str_param/{phone_number}", response_description="Add new str_param to chat", status_code=status.HTTP_201_CREATED, response_model=List[str])
def add_str_param(request: Request, phone_number: str, body = Body({})):
    try:
        chat = request.app.database["chats"].find_one({"phone_number": phone_number})
        if chat:
            str_params = chat["str_params"]
            str_param = body.get("str_param")
            # add new str_param to str_params, and update chat
            str_params = str_params + [str_param]
            request.app.database["chats"].update_one({"phone_number": phone_number}, {"$set": {"str_params": str_params}})
            return str_params
        else:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Chat with phone number {phone_number} not found")
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

# from the str_params in a chat, remove all instances of a specific str_param
@router.put("/remove_str_param/{phone_number}", response_description="Remove str_param from chat", status_code=status.HTTP_201_CREATED, response_model=List[str])
def remove_str_param(request: Request, phone_number: str, body = Body({})):
    try:
        chat = request.app.database["chats"].find_one({"phone_number": phone_number})
        if chat:
            str_params = chat["str_params"]
            str_param = body.get("str_param")
            # remove all instances of str_param from str_params, and update chat
            str_params = [s for s in str_params if s != str_param]
            request.app.database["chats"].update_one({"phone_number": phone_number}, {"$set": {"str_params": str_params}})
            return str_params
        else:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Chat with phone number {phone_number} not found")
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

# update the list of Reminder objects in a chat based on phone number
@router.put("/update_reminders/{phone_number}", response_description="Update reminders in chat", response_model=List[Reminder])
def update_reminders(request: Request, phone_number: str, body = Body({})):
    try:
        chat = request.app.database["chats"].find_one({"phone_number": phone_number})
        if chat:
            time = body.get("time")
            context = body.get("context", "(generic)")
            repeat = body.get("repeat", False)

            new_reminder = Reminder(time=time, context=context, repeat=repeat)
            reminders = chat["reminders"]
            # remove all reminders with the same context as the new reminder
            reminders = [r for r in reminders if r.context != context]
            # add new reminder to reminders
            reminders.append(new_reminder)
            # update reminders in chat
            request.app.database["chats"].update_one({"phone_number": phone_number}, {"$set": {"reminders": reminders}})
            return reminders
        else:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Chat with phone number {phone_number} not found")
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

# delete a reminder from a chat based on phone number and context from body
@router.put("/delete_reminder/{phone_number}", response_description="Delete reminder from chat", response_model=List[Reminder])
def delete_reminder(request: Request, phone_number: str, body = Body({})):
    try:
        chat = request.app.database["chats"].find_one({"phone_number": phone_number})
        if chat:
            context = body.get("context")
            reminders = chat["reminders"]
            # remove all reminders with the same context as the new reminder
            reminders = [r for r in reminders if r.context != context]
            # update reminders in chat
            request.app.database["chats"].update_one({"phone_number": phone_number}, {"$set": {"reminders": reminders}})
            return reminders
        else:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Chat with phone number {phone_number} not found")
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
        
# from a chat, get the time_till_reach_out value
@router.get("/time_till_reach_out/{phone_number}", response_description="Get time_till_reach_out from chat", response_model=int)
def get_time_till_reach_out(request: Request, phone_number: str):
    try:
        chat = request.app.database["chats"].find_one({"phone_number": phone_number})
        if chat:
            time_till_reach_out = chat["time_till_reach_out"]
            return time_till_reach_out
        else:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Chat with phone number {phone_number} not found")
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

# update the chat value of time_till_reach_out in a chat based on phone number
@router.put("/update_time_till_reach_out/{phone_number}", response_description="Update time_till_reach_out in chat", response_model=int)
def update_time_till_reach_out(request: Request, phone_number: str, body = Body({})):
    try:
        chat = request.app.database["chats"].find_one({"phone_number": phone_number})
        if chat:
            time_till_reach_out = body.get("time_till_reach_out")
            # update time_till_reach_out in chat
            request.app.database["chats"].update_one({"phone_number": phone_number}, {"$set": {"time_till_reach_out": time_till_reach_out}})
            return time_till_reach_out
        else:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Chat with phone number {phone_number} not found")
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

# get messages from chat based on phone number
@router.get("/get_messages/{phone_number}", response_description="Get messages from chat", response_model=List[Message])
def get_messages(request: Request, phone_number: str):
    try:
        chat = request.app.database["chats"].find_one({"phone_number": phone_number})
        if chat:
            messages = chat["messages"]
            return messages
        else:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Chat with phone number {phone_number} not found")
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

# update messages from chat based on phone number
@router.put("/update_messages/{phone_number}", response_description="Update messages from chat", response_model=List[Message])
def update_messages(request: Request, phone_number: str, body = Body({})):
    try:
        chat = request.app.database["chats"].find_one({"phone_number": phone_number})
        if chat:
            messages = chat["messages"]
            change = body.dict()
            request.app.database["chats"].update_one({"phone_number": phone_number}, {"$set": change})
            return request.app.database["chats"].find_one({"phone_number": phone_number})["messages"]
        else:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Chat with phone number {phone_number} not found")
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

# delete messages from chat based on phone number
@router.delete("/delete_messages/{phone_number}", response_description="Delete messages from chat")
def delete_messages(request: Request, phone_number: str):
    try:
        chat = request.app.database["chats"].find_one({"phone_number": phone_number})
        if chat:
            # get the messages from the chat, and move them to deleted_messages
            messages = chat["messages"]
            deleted_messages = chat["deleted_messages"]

            request.app.database["chats"].update_one({"phone_number": phone_number}, {"$set": {"messages": [], "deleted_messages": messages}})

            return Response(status_code=status.HTTP_204_NO_CONTENT)
        else:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Chat with phone number {phone_number} not found")
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

# get the prompt params from chat based on phone number
@router.get("/get_prompt_params/{phone_number}", response_description="Get prompt params from chat", response_model=PromptParams)
def get_prompt_params(request: Request, phone_number: str):
    try:
        chat = request.app.database["chats"].find_one({"phone_number": phone_number})
        if chat:
            prompt_params = chat["prompt_params"]
            return prompt_params
        else:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Chat with phone number {phone_number} not found")
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

# update the prompt params in a chat based on phone number and using body
@router.put("/update_prompt_params/{phone_number}", response_description="Update prompt params in chat", response_model=PromptParams)
def update_prompt_params(request: Request, phone_number: str, body = Body({})):
    try:
        chat = request.app.database["chats"].find_one({"phone_number": phone_number})
        if chat:
            prompt_params = chat["prompt_params"]
            change = body.dict()
            request.app.database["chats"].update_one({"phone_number": phone_number}, {"$set": {"prompt_params": change}})
            return request.app.database["chats"].find_one({"phone_number": phone_number})["prompt_params"]
        else:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Chat with phone number {phone_number} not found")
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

#  online check
@router.get("/", response_description="Get main", response_model=List[Chat])
def check_online(request: Request):
    return "API for chatbot"

# get all chats
@router.get("/all/", response_description="List all chats", response_model=List[Chat])
def get_all_chats(request: Request):
    chats = list(request.app.database["chats"].find())
    return chats

# get all phone numbers
@router.get("/all/numbers", response_description="List all phone numbers", response_model=List[str])
def list_numbers(request: Request):
    chats = list(request.app.database["chats"].find({}, {"phone_number": 1, "_id": 0}))
    if chats[0]["phone_number"] == "1":
        return []
    return [chat["phone_number"] for chat in chats]

@router.get("/num_messages/{phone_number}", response_description="Get total number of messages in a chat", response_model=int)
def get_num_messages(phone_number: str, request: Request):
    if (chat := request.app.database["chats"].find_one({"phone_number": phone_number})) is not None:
        return len(chat["messages"])
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Chat with phone_number {phone_number} not found")

@router.get("/last_message/{phone_number}", response_description="Get last message in a chat", response_model=Message)
def get_last_message(phone_number: str, request: Request):
    try:
        projection = { "messages": { "$slice": -1 } }
        last_message = request.app.database["chats"].find_one({ "phone_number": phone_number }, projection)["messages"][0]
        if last_message is not None:
            return last_message
    except:
        print("No messages in chat")
        # TODO: NEED TO FIX THIS REASONING - because case when two day responder
        # But this should never really happen
        return Message(from_us=True, text="")
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Chat with phone_number {phone_number} not found")

@router.get("/unreplied_chats/", response_description="Get list of unreplied chat phone numbers")
def get_unreplied_chats(request: Request):
    try:
        pipeline = [
            { "$addFields": { "lastMessage": { "$arrayElemAt": [ "$messages", -1 ] } } },
            { "$match": { "lastMessage.from_us": False } },
            { "$project": { "_id": 0, "phone_number": 1 } }
        ]
        phone_numbers = [x["phone_number"] for x in list(request.app.database["chats"].aggregate(pipeline))]
        return phone_numbers
    except:
        print("Something went wrong")
        # TODO: NEED TO FIX THIS REASONING - because case when two day responder
        # But this should never really happen
        return []
@router.delete("/rollback_messages/{phone_number}", response_description="Rollback a chat")
def rollback_chat(phone_number: str, request: Request, response: Response):
    chat = request.app.database["chats"].find_one({"phone_number": phone_number})
    if chat is not None:
        messages = chat["messages"]
        if len(messages) == 0:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"No messages to rollback")
        if messages[-1]["from_us"] == True:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Last message was sent by us")
        deleted_messages = chat["deleted_messages"]
        # go through messages in reverse order of time, and delete until you find a message where from_us is True
        for i in range(len(messages)-1, -1, -1):
            if messages[i]["from_us"] == True:
                break
        change = {
            "messages" : messages[:i+1],
            "deleted_messages" : deleted_messages + messages[i+1:]
            }
        request.app.database["chats"].update_one({"phone_number": phone_number}, {"$set": change})
        chat = request.app.database["chats"].find_one({"phone_number": phone_number})
        if len(chat["messages"]) > 0:
            return chat["messages"][-1]
        else:
            return Message()
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Chat with phone_number {phone_number} not found")
