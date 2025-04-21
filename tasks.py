import os
import time
from datetime import datetime
import threading
from fastapi import File
from pydantic import BaseModel, ValidationError

import whisper # type: ignore
from ollama import chat # type: ignore
from ollama import ChatResponse # type: ignore

import db
from models import Call, Event


INDEX_PAGE="./index.htm"
WHISPER_MODEL="turbo"


#-----------------------------------------------------------------------------------
#-----------------------------------------------------------------------------------
def out_index_page():
    """
    Return the index page
    """
    with open(INDEX_PAGE, 'r') as f:
        page = f.read()
    return page


#-----------------------------------------------------------------------------------
#-----------------------------------------------------------------------------------
def dlog(event: dict):
    """
    Log message or error insert into DB, 
    out to the console and return to the client
    """
    res = Event(**event)    #-- create an Event object
    db.insert_log(res)      #-- log the event to DB
    print(res)              #-- print the event to the console  
    return(res)             #-- return the event


#-----------------------------------------------------------------------------------
#-----------------------------------------------------------------------------------
async def upload_call_file(file: File ):
    """
    Upload file
    More: https://www.geeksforgeeks.org/save-uploadfile-in-fastapi/
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
        events.append(dlog({"msg":f"Uploaded {file_path} successfully"}))

        #-- get the call ID
        new_call = Call(audio_url = file_path)
        new_call.call_id = get_call_id(file_path)

        #-- create a new call row in the DB
        new_call.id, logs = db.create_new_call(new_call)
        events.append(logs)

        #-- run other tasks in a separate thread
        convert = threading.Thread(target=process_call, args=(new_call,))
        convert.start()

    else:
        events.append(dlog({"status":"error","msg":f"File {file_path} was not uploaded"}))
    return events


#-----------------------------------------------------------------------------------
#-----------------------------------------------------------------------------------
def get_call_id(file_path: str):
    """
    Get the call ID from the file name
    Assumption: the file name is unique and can serve as the call ID
    """
    #-- get call ID from the file name
    Call_ID = os.path.splitext(os.path.basename(file_path))[0]
    return Call_ID


#-----------------------------------------------------------------------------------
#-----------------------------------------------------------------------------------
def process_call(new_call: Call):
    """
    Main function to perform post-processing for the uploaded call file
    """
    events=[]
    proc_start = time.time()

    events.append(dlog({"msg":f"process_call: Process Call ID={new_call.call_id}","lvl":3}))

   #-- transcribe the call
    new_call, logs = transcribe_call(new_call)      
    events.append(logs)

    #-- analyse the call
    new_call, logs = analyse_call(new_call)        
    events.append(logs)

    #-- done with all processing
    proc_duration = time.time() - proc_start
    events.append(dlog({"msg":f"Processed all tasks for Call ID={new_call.call_id} successfully in {proc_duration:.2f} seconds","lvl":2}))
    return events


#-----------------------------------------------------------------------------------
#-----------------------------------------------------------------------------------
def transcribe_call(new_call: Call ):
    """
    Transcribe the audio file and update DB
    """
    events=[]
    proc_start = time.time()

    events.append(dlog({"msg":f"transcribe_call: Will transcribe Call ID={new_call.call_id}","lvl":3}))
    
    #== perform the transcription
    model = whisper.load_model(WHISPER_MODEL)
    result = model.transcribe(new_call.audio_url, task='transcribe', language='en', fp16=False)
    new_call.transcript = result["text"]

    #-- update the call record in the DB
    logs = db.update_call_transcript(new_call)
    events.append(logs)

    #-- done with the transcription
    proc_duration = time.time() - proc_start
    events.append(dlog({"msg":f"Transcribed Call ID={new_call.call_id} successfully in {proc_duration:.2f} seconds","lvl":2}))

    return new_call, events


#-----------------------------------------------------------------------------------
#-----------------------------------------------------------------------------------
def analyse_call(new_call: Call ):
    """
    Get additional analysis for the Call
    """
    events=[]
    proc_start = time.time()

    events.append(dlog({"msg":f"analyse_call: Will analyse Call ID={new_call.call_id}","lvl":3}))
    
    #== perform the analysis
    ai_response: ChatResponse = chat(model='llama3.2', messages=[
        {
            'role': 'user',
            'content': f"Summarize this file: {new_call.transcript}",
        },
    ])
    new_call.analysis = ai_response.message.content # ['message']['content']

    #-- update the call record in the DB
    logs = db.update_call_analysis(new_call) 
    events.append(logs)

    #-- done with the analysis
    proc_duration = time.time() - proc_start
    events.append(dlog({"msg":f"Analysed Call ID={new_call.call_id} successfully in {proc_duration:.2f} seconds","lvl":2}))

    return new_call, events

