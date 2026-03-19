from pydantic import BaseModel, Field, validator
from typing import Optional, List, Dict, Any
from datetime import datetime

class User(BaseModel):
    user_id: int
    first_name: str
    last_name: Optional[str] = None
    username: Optional[str] = None
    is_bot: bool
    last_activity_time: Optional[int] = None
    name: Optional[str] = None

class Recipient(BaseModel):
    chat_id: Optional[int] = None
    chat_type: Optional[str] = None
    user_id: Optional[int] = None

class MessageBody(BaseModel):
    mid: str
    seq: int
    text: Optional[str] = None
    attachments: Optional[List[Dict[str, Any]]] = None

class Message(BaseModel):
    recipient: Recipient
    timestamp: int
    body: MessageBody
    sender: User

class Callback(BaseModel):
    timestamp: int
    callback_id: str
    user: User
    payload: str

class WebhookUpdate(BaseModel):
    update_type: str
    timestamp: int
    chat_id: Optional[int] = None
    user: Optional[User] = None
    user_locale: Optional[str] = None
    user_id: Optional[int] = None
    message: Optional[Message] = None
    callback: Optional[Callback] = None

    @validator('update_type')
    def validate_type(cls, v):
        allowed = {'message_created', 'bot_started', 'message_callback'}
        if v not in allowed:
            raise ValueError(f'Invalid update_type: {v}')
        return v