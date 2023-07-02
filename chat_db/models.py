import uuid
from typing import List, Optional
from pydantic import BaseModel, Field
import time

class Message(BaseModel):
    from_us: bool = Field(default=False)
    time: int = Field(default=time.time())
    content: str = Field(default="")
    errors:list = Field(default=[])
    
    class Config:
        schema_extra = {
            "message_example": {
                "fromUs": False,
                "time": 1231341,
                "message": "Don Quixote is a Spanish novel by Miguel de Cervantes..."
            }
        }
    
class Reminder(BaseModel):
    time: int = Field(default=time.time())
    context: str = Field(default="")
    repeat: bool = Field(default=True)
    
    class Config:
        schema_extra = {
            "reminder_object": {
                "time": 1231341,
                "context": "Don Quixote is a Spanish novel by Miguel de Cervantes...",
                "repeat": False
            }
        }

class PromptParams(BaseModel):
    user_name: str = Field(default="Friend")
    ai_name: str = Field(default="Isa")
    interests: list = Field(default=[])
    facts: list = Field(default=[])
    summaries: list = Field(default=[])
    overall_summary: str = Field(default="")
    use_custom_user_desc_prompt: bool = Field(default = False)
    custom_user_desc_prompt: str = Field(default="")
    
    class Config:
        schema_extra = {
            "reminder_object": {
                "user_name": "Lucy",
                "ai_name": "Isa",
                "repeat": False
            }
        }


class Chat(BaseModel):
    phone_number: str = Field(...)
    messages: List[Message] = Field(default=[])
    deleted_messages: List[Message] = Field(default=[])
    str_params:list = Field(default=[])
    reminders: List[Reminder] = Field(default=[])
    time_till_reach_out: int = Field(48)
    # we create a prompt_details object that by default is a initialised PromptParams object
    prompt_params: PromptParams = Field(default=PromptParams())

    class Config:
        allow_population_by_field_name = True
        schema_extra = {
            "example": {
                "phone_number": "01234566as57",
                "messages": [],
                "errors" : [],
                "deleted_messages" : [],
                "str_params" : ["(do_not_reach_out)", ]
            }
        }