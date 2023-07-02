# uvicorn process:app --reload --port 8005
from fastapi import FastAPI, APIRouter, Body, Request, Response, HTTPException, status
import base64
from pydub import AudioSegment 
# also need to make sure ffmpeg is installed, linux: apt-get install ffmpeg libavcodec-extra
import openai
from dotenv import dotenv_values
import requests
import os
import time

config_params = dotenv_values("audio.env")

CHAT_DB_LINK = config_params["CHAT_DB_LINK"]

openai.api_key = "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"

app = FastAPI()


@app.post("/")
async def root(request: Request, body = Body({})):
    # we get decrypted_media from the body
    decrypted_media = body["decrypted_media"]
    # we want to get the part of the string in decrypted media that is the actual audio file
    decrypted_media_base64 = decrypted_media[decrypted_media.index("base64,") + 7:]
    # we then want to turn this string to an ogg audio bytes
    ogg_file = base64.b64decode(decrypted_media_base64)
    # safe the ogg file, turn it into wav, then load wav into openai
    file_name_prefix = str(time.time()) + "_" + body["phone_number"]

    with open(f"temp/{file_name_prefix}.ogg", "wb") as f:
        f.write(ogg_file)
    sound = AudioSegment.from_ogg(f"temp/{file_name_prefix}.ogg")
    sound.export(f"temp/{file_name_prefix}.wav", format="wav")

    with open(f"temp/{file_name_prefix}.wav", "rb") as f:
        # we then make a request to whisper api to get the text
        transcript = openai.Audio.transcribe("whisper-1", f)

    # we then delete the files we creates
    os.remove(f"temp/{file_name_prefix}.ogg")
    os.remove(f"temp/{file_name_prefix}.wav")


    # we print out the transcript
    print(transcript["text"])
    # we then want to add the transcript to the messages database
    params = {
        'user_name': body["user_name"],
        'phone_number': body["phone_number"],
        'content': transcript["text"],
        'from_us': False
    }

    r =requests.post(CHAT_DB_LINK + f'/chat/add_message/{body["phone_number"]}', json=params)
    print(r)
    print("added message to chat db: " + transcript["text"] + " from " + body["user_name"] + " (" + body["phone_number"] + ")")

    # get str_params for phone number
    str_params = requests.get(CHAT_DB_LINK + f'/chat/get_str_params/{body["phone_number"]}')
    if not ("(used_voice_message)" in str_params):
        params = {
            'str_param': "(used_voice_message)"
        }
        r =requests.put(CHAT_DB_LINK + f'/chat/add_str_param/{body["phone_number"]}', json=params)


    



