#-- Classes and Models
from pydantic import BaseModel, ValidationError


class Event(BaseModel):
    status: str="ok"
    msg: str="No event"
    lvl: int=1

class Call(BaseModel):
    id: int=None # optional
    call_id: str=None # optional
    audio_url: str=None # optional
    agent: str=None # optional
    duration: int=None # optional
    transcript: str=None # optional
    analysis: str=None # optional
    satisfaction: int=None # optional
    created_at: str=None # optional


