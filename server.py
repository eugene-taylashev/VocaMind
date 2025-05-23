#===================================================================================
#-- FastAPI server for the VocaMind application
#===================================================================================
from fastapi import FastAPI, Form, File, UploadFile
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles

import stasks
#from db import get_call_details
#from models import Call, Event

#-- FastAPI
app = FastAPI()

#-----------------------------------------------------------------------------------
#-----------------------------------------------------------------------------------
@app.get("/")
async def root():
    """
    Root page for the VocaMind application
        Arguments:
            None
        Returns:
            content: HTML - HTML page for the client
    """
    content = stasks.out_index_page()
    return HTMLResponse(content=content)

#-- images and Javascript files
app.mount("/images", StaticFiles(directory="./images"), name="images")
#-- call files
app.mount("/audio", StaticFiles(directory="./data"), name="audio_files")


#-----------------------------------------------------------------------------------
#-----------------------------------------------------------------------------------
@app.get("/check_health")
async def check_health():
    """
    Check the health of external components like DB, LLM, etc.
        Arguments:
            None
        Returns:
            response: dict - health status
    """
    #-- check the components status
    events = stasks.check_component_status()
    return {"response": {"logs":events }}


#-----------------------------------------------------------------------------------
#-----------------------------------------------------------------------------------
@app.get("/calls")
async def get_call_list():
    """
    Get list of calls
        Arguments:
            None
        Returns:
            response: dict - list of call 
    """
    #-- get list of calls from the DB
    list, events = await stasks.get_call_list()
    if not list:
        return {"response": {"logs":[{"status":"error","msg":"No calls found"}] }}
    return {"response": {"logs":events,"call_list":list} }


#-----------------------------------------------------------------------------------
#-----------------------------------------------------------------------------------
@app.get("/calls/{call_id:int}")
async def get_call_details(call_id: int):
    """
    Get call details
        Arguments:
            call_id: int - call ID
        Returns:
            response: dict - call details
    """
    #-- get the call details from the DB
    call, events = await stasks.get_call_details(call_id)
    if not call:
        return {"response": {"logs":[{"status":"error","msg":"No call found"}] }}
    return {"response": {"logs":events,"call":call} }


#-----------------------------------------------------------------------------------
#-----------------------------------------------------------------------------------
@app.post("/calls/{call_id:int}/agent/{agent_id:int}")
async def update_agent_id(call_id: int, agent_id: int):
    """
    Update an agent for the call
        Arguments:
            call_id: int - call ID
            agent_id: int - agent ID from agents table
        Returns:
            response: dict - events
    """
    #-- get the call details from the DB
    events = await stasks.update_agent_id(call_id, agent_id)
    return {"response": {"logs":events} }

#-----------------------------------------------------------------------------------
#-----------------------------------------------------------------------------------
#curl -X POST -F "file=@/path/to/file.wav" 'http://localhost:8000/calls/upload'
@app.post("/calls/upload")
async def upload_file(file: UploadFile = File(...)):
    """
    Upload a call audio file
        Arguments:
            file: UploadFile - audio file from FormData
        Returns:
            response: dict - call details
    """
    #-- check if the file is empty
    if not file:
        return {"response": {"logs":[{"status":"error","msg":"No upload file sent"}] }}
    #-- process the file
    events = await stasks.upload_call_file(file)
    return {"response": {"logs":events}}


#-----------------------------------------------------------------------------------
#-----------------------------------------------------------------------------------
@app.post("/bot/ask")
async def ask_bot(question: str = Form(...), selected_model: str = Form(...)):
    """
    Ask the bot for a question
        Arguments:
            question: str - question to ask the bot
            selected_model: str - selected LLM model
        Returns:
            response: dict - bot answer and logs
    """
    #-- get the answer from the AI
    response, events = stasks.ask_bot(question, selected_model)
    return {"response": {"bot_answer": response, "logs":events}}


#-----------------------------------------------------------------------------------
#-----------------------------------------------------------------------------------
@app.get("/models")
async def get_models():
    """
    Return list of available LLM models
        Arguments:
            None
        Returns:
            response: dict - list of available LLM models
    """
    response, selected, events = stasks.enum_llm_models()
    return {"response": {"llm_models": response, "selected_model":selected, "logs":events}}


#-----------------------------------------------------------------------------------
#-----------------------------------------------------------------------------------
@app.get("/agents")
async def get_agents():
    """
    Return list of agents
        Arguments:
            None
        Returns:
            response: dict - list of agents from DB
    """
    agents, events = await stasks.get_agents()
    return {"response": {"agents": agents, "logs":events}}


#-----------------------------------------------------------------------------------
#-----------------------------------------------------------------------------------
@app.get("/refs")
async def get_references():
    """
    Return JSON with text references from table REFS
        Arguments:
            None
        Returns:
            response: dict - list of references from DB + events
    """
    refs, events = await stasks.get_refs()
    return {"response": {"refs": refs, "logs":events}}

#-----------------------------------------------------------------------------------
#-----------------------------------------------------------------------------------
@app.get("/stats")
async def get_stats():
    """
    Return JSON with application stats for the Dashboard
        Arguments:
            None
        Returns:
            response: dict - JSON with call stats from DB + events
    """
    stats, events = await stasks.get_stats()
    return {"response": {"dashboard_stats": stats, "logs":events}}
