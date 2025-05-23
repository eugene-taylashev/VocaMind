#==========================================================================
#-- API Server-specific tasks, run in real time
#   See btasks.py for background tasks
#==========================================================================
import os
import time
from datetime import datetime
import subprocess
import re

from fastapi import File
#from pydantic import BaseModel, ValidationError

from ollama import chat, ChatResponse # type: ignore

import db
import btasks
from models import Call, Event

# importing necessary functions from dotenv library
#from dotenv import load_dotenv


INDEX_PAGE="./index.htm"
CMD_LIST_LLM = "ollama list" #-- command to list available Ollama models
LLM_MODEL_DEFAULT = "ollama/llama3.2" #-- default model to use

# Basic color codes
RED = '\033[91m'
GREEN = '\033[92m'
YELLOW = '\033[93m'
BLUE = '\033[94m'
RESET = '\033[0m'  # This resets the color back to default

#-----------------------------------------------------------------------------------
#-----------------------------------------------------------------------------------
def out_index_page():
    """
    Return the index page
        Arguments:
            None
        Returns:
            page: str - index page as HTML + CSS + JS
    """
    with open(INDEX_PAGE, 'r') as f:
        page = f.read()
    return page

#-----------------------------------------------------------------------------------
#-----------------------------------------------------------------------------------
def print_event(e: Event):
    '''
    Output one Event with changing color for status
            e - Event object
        Returns:
            None
    '''
    result = ''
    if e.status == 'ok':
        result += f"[{GREEN}ok{RESET}] - "
    elif e.status == 'warn':
        result += f"[{YELLOW}warn{RESET}] - "
    else:
        result += f"[{RED}error{RESET}] - "
    result += e.msg
    print(result)



#-----------------------------------------------------------------------------------
#-----------------------------------------------------------------------------------
def dlog(event: dict):
    """
    Log message or error insert into DB, 
    out to the console and return to the client
        Arguments:
            event: dict - event to log
        Returns:
            res: Event - event object
    """
    res = Event(**event)    #-- create an Event object
    db.insert_log(res)      #-- log the event to DB
    print_event(res)              #-- print the event to the console  
    return(res)             #-- return the event


#-----------------------------------------------------------------------------------
#-----------------------------------------------------------------------------------
def check_component_status():
    """
    Check the status of the components
        Arguments:
            None
        Returns:
            events: list - list of component checks as Event object
    """
    events=[]
    log = Event(msg="check_component_status: Checking status of components",lvl=3)
    events.append(log)

    #-- check if the DB connection is working
    db_status = db.check_db_connection()
    if db_status == 'good':
        log = Event(msg="DB connection is good",lvl=1)
    else:
        log = Event(status="error",msg=f"DB connection error: {db_status}")
    events.append(log)

    #-- check if the RabbitMQ is active
    service2check="rabbitmq"
    try:
        subprocess.check_output(f"systemctl is-active {service2check}.service", shell=True, text=True)
        log = Event(msg="Message broker (RabbitMQ) service is active",lvl=1)
    except subprocess.CalledProcessError as e:
        log = Event(status="error",msg="Message broker (RabbitMQ) service is NOT active")
    events.append(log)

    #-- check if the Celery is active
    service2check="vocamind"
    try:
        subprocess.check_output(f"systemctl is-active {service2check}.service", shell=True, text=True)
        log = Event(msg="Background task (Celery) service is active",lvl=1)
    except subprocess.CalledProcessError as e:
        log = Event(status="error",msg="Background task (Celery) service is NOT active")
    events.append(log)

    #-- check if the LLM service is active
    service2check="ollama"
    try:
        subprocess.check_output(f"systemctl is-active {service2check}.service", shell=True, text=True)
        log = Event(msg="LLMs runner (Ollama) service is active",lvl=1)
    except subprocess.CalledProcessError as e:
        log = Event(status="error",msg="LLMs runner (Ollama) service is NOT active")
    events.append(log)

    return events


#-----------------------------------------------------------------------------------
#-----------------------------------------------------------------------------------
async def upload_call_file(file: File ):
    """
    Upload file
    More: https://www.geeksforgeeks.org/save-uploadfile-in-fastapi/
        Arguments:
            file: UploadFile - audio file from FormData
        Returns:
            events: list - list of events as Event object
    """
    events=[]
    events.append(dlog({"msg":f"upload_call_file: File to upload {file.filename}","lvl":3}))

    #== construct the file path
    #-- get right directory name
    dir_dst = os.getenv("DIR_AUDIO")

    #-- get current date as a directory name
    dir_date = datetime.today().strftime('%Y%m%d')
    #-- construct the destination directory + current date
    dir_dst = os.path.join(dir_dst, dir_date)

    #-- check if the directory exists
    if os.path.exists(dir_dst):
        events.append(dlog({"msg":f"Destination directory {dir_dst} exists","lvl":3}))
    else:
        os.makedirs(dir_dst)
        events.append(dlog({"msg":f"Created destination directory {dir_dst}","lvl":2}))

    #-- construct the file path    
    file_path = os.path.join(dir_dst, file.filename)

    #-- Save the file to the server
    with open(file_path, "wb") as f:
        f.write(await file.read())

    #-- verify the file was saved, perform more processing
    if os.path.exists(file_path):
        events.append(dlog({"msg":f"Uploaded {file_path} to the distination directory successfully"}))

        #-- get the call ID
        new_call = Call(audio_url = file_path)
        new_call.call_id = get_call_id(file_path)

        #-- create a new call row in the DB
        new_call, logs = db.create_new_call(new_call)
        events.append(logs)

        #-- run other tasks in a background mode with Celery
        btasks.calc_duration.delay(new_call.cid, new_call.audio_url)  #-- calculate the duration of the call file
        btasks.process_call.delay(new_call.cid, new_call.audio_url) 

    else:
        events.append(dlog({"status":"error","msg":f"upload_call_file: File {file_path} was NOT uploaded"}))
    return events


#-----------------------------------------------------------------------------------
#-----------------------------------------------------------------------------------
def get_call_id(file_path: str):
    """
    Get the call ID from the file name
    Assumption: the file name is unique and can serve as the call ID
        Arguments:
            file_path: str - path to the file
        Returns:
            Call_ID: str - call ID
    """
    #-- get call ID from the file name
    Call_ID = os.path.splitext(os.path.basename(file_path))[0]
    return Call_ID


#-----------------------------------------------------------------------------------
#-----------------------------------------------------------------------------------
def ask_bot(question: str, Model: str):
    """
    Ask the local bot a question
        Arguments:
            question: str - question to ask the bot
            Model: str - model to use
        Returns:
            answer: str - answer from the bot
            events: list - list of events as Event object
    """
    events=[]
    proc_start = time.time()

    events.append(dlog({"msg":f"ask_bot: Will ask the bot the question using model {Model}","lvl":3}))
    
    #== perform the analysis
    ai_response: ChatResponse = chat(model=Model, messages=[
        {
            'role': 'user',
            'content': question,
        },
    ])
    answer = ai_response.message.content # ['message']['content']
    #-- done with the analysis

    proc_duration = time.time() - proc_start
    events.append(dlog({"msg":f"ask_bot: Bot replied successfully in {proc_duration:.2f} seconds","lvl":2}))

    return answer, events


#-----------------------------------------------------------------------------------
#-----------------------------------------------------------------------------------
def enum_llm_models():
    """
    Construct the list of available local Ollam models, run it as a system command
        Arguments:
            None
        Returns:
            models: list - list of available models
            default_model: str - default model to use
            events: list - list of events as Event object
    """
    models = ['openai/gpt-4o-mini']
    events=[]
    try:
        result = subprocess.check_output(CMD_LIST_LLM, shell=True, text=True)
        for ln in result.splitlines():
            if re.search(r"^NAME", ln):
                next  # Skip the header
            else:
                x = re.search(r"^(.*?)\s+", ln)
                x = re.sub(r":latest", "", x.group(1))
                if x:
                    models.append('ollama/'+x)
        events.append(dlog({"msg":"Collected "+str(len(models))+" LLM models sucessfully","lvl":2}))
        return models, LLM_MODEL_DEFAULT, events

    except subprocess.CalledProcessError as e:
        events.append(dlog({"status":"error","msg":f"enum_llm_models: Error executing command: {e}"}))
        return models, LLM_MODEL_DEFAULT, events


#-----------------------------------------------------------------------------------
#-----------------------------------------------------------------------------------
async def get_call_details(cid: int):
    '''
    Get the call details from the DB
        Arguments:
            cid: int - call ID
        Returns:
            call: Call - call object
            events: list - list of events as Event object
    '''
    return db.get_call_details(cid)

#-----------------------------------------------------------------------------------
#-----------------------------------------------------------------------------------
async def get_call_list():
    '''
    Get the list of calls from the DB
        Arguments:
            None
        Returns:
            call_list: list - list of call objects  
            events: list - list of events as Event object
    '''
    return db.get_call_list()


#-----------------------------------------------------------------------------------
#-----------------------------------------------------------------------------------
async def get_agents():
    '''
    Get the list of agents from the DB
        Arguments:
            None
        Returns:
            agents: list - list of agents  
            events: list - list of events as Event object
    '''
    agents, events = db.get_agents()
    return agents, events


#-----------------------------------------------------------------------------------
#-----------------------------------------------------------------------------------
async def update_agent_id(call_id: int, agent_id: int):
    '''
    Update an agent for the call
        Arguments:
            call_id: int - call ID
            agent_id: int - agent ID from agents table
        Returns:
            response: dict - events
    '''
    return db.update_agent_id(call_id, agent_id)

#-----------------------------------------------------------------------------------
#-----------------------------------------------------------------------------------
async def get_refs():
    '''
    Return list of text references from table REFS
        Arguments:
            None
        Returns:
            refs: list - list of text references  
            events: list - list of events as Event object
    '''
    refs, events = db.get_refs()
    return refs, events


#-----------------------------------------------------------------------------------
#-----------------------------------------------------------------------------------
async def get_stats():
    '''
    Return JSON with application stats for the Dashboard
        Arguments:
            None
        Returns:
            stats: dict - JSON with call stats from DB
            events: list - list of events as Event object
    '''
    stats = dict()
    events = []
    calls_total, logs = db.get_calls_total()
    stats['calls_total'] = int(calls_total)
    events = events + logs
    csat_score, logs = db.get_csat_stats()
    stats = stats | csat_score
    events = events + logs
    fcr, logs = db.get_fcr_stats()
    stats = stats | fcr
    events = events + logs
    return stats, events

