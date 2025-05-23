#-- Classes and Models
from pydantic import BaseModel, ValidationError


class Event(BaseModel):
    status: str="ok" #-- status of the event
    msg: str="No event"
    lvl: int=1
    cid: int=0 #-- call ID, optional

class Call(BaseModel):
    cid: int=None # optional
    call_id: str=None # optional
    agent_id: int=None # optional
    audio_url: str=None # optional
    duration: int=None # optional
    transcript: dict=None # optional
    analysis: str=None # optional
    cust_satis: int=None # optional
    is_fcr: bool=None # optional
    is_abuse: bool=None # optional
    cust_sentiment: str=None # optional
    created_at: str=None # optional
    other: dict=None # optional

