#==========================================================================
#-- Background tasks, executed by Celary 
#   See:
#       stasks.py for real-time tasks
#       /etc/celery/vocamind.conf
#       /usr/lib/systemd/system/celery@.service
#==========================================================================
from celery import Celery   # type: ignore
from celery import signals  # type: ignore
import os
import time
import regex    # type: ignore
import json
import subprocess
from dotenv import load_dotenv

import whisper      # type: ignore
#import torch        # type: ignore
#from ollama import chat, ChatResponse # type: ignore
from litellm import completion  # type: ignore

import db
from models import Call, Event

# loading variables from .env file
load_dotenv() 
RABBITMQ_URL=os.getenv("BROKER_URL")
openai_api_key = os.getenv("OPENAI_API_KEY")
WHISPER_MODEL="tiny.en" #"turbo" "small.en"


#celery -A btasks status
#celery -A btasks inspect active

#-- Celery configuration
app = Celery('btasks', backend='rpc://', broker=RABBITMQ_URL )
app.conf.timezone = 'America/Toronto'
app.conf.broker_connection_retry_on_startup = True

#os.environ["PYTORCH_CUDA_ALLOC_CONF"]="max_split_size_mb:512,expandable_segments:True"

#-----------------------------------------------------------------------------------
#-----------------------------------------------------------------------------------
@signals.task_failure.connect
def handle_task_failure(sender=None, task_id=None, exception=None, **kwargs):
    '''
    Handle Celery task failure
        Arguments:
            sender: str - name of the task
            task_id: str - ID of the task
            exception: Exception - exception raised by the task
        Returns:
            None
    '''
    log = Event(msg=f"Celery: Task {task_id} failed: {str(exception)}",lvl=1,cid=0)
    db.insert_log(log)
    print(log.msg)  # Replace with logging/notifications


#-----------------------------------------------------------------------------------
#-----------------------------------------------------------------------------------
@app.task
def process_call(id: int, url: str):
    """
    Main function to perform post-processing for the uploaded call file
        Arguments:
            id: int - call ID
            url: str - call URL
        Returns:
            proc_duration: float - tasks processing duration in seconds
    """
    proc_start = time.time()
    #torch.cuda.empty_cache()
    log = Event(msg=f"process_call: Process Call ID={id}",lvl=3,cid=id)
    db.insert_log(log)
   
    transcript = transcribe_call(id, url)   #-- transcribe the call
    analyse_call(id, transcript)            #-- analyse the call

    #-- done with all processing
    proc_duration = time.time() - proc_start
    log = Event(msg=f"process_call: Processed all tasks for Call ID={id} successfully in {proc_duration:.2f} seconds",lvl=2,cid=id)
    db.insert_log(log)
    return proc_duration


#-----------------------------------------------------------------------------------
#-----------------------------------------------------------------------------------
@app.task
def calc_duration(id: int, url: str):
    """
    Calculate the duration of a call file in seconds using ffprobe, update DB
    Uses system call to ffprobe
        Arguments:
            id: int - call ID
            url: str - call URL
        Returns:
            Dur: int - call duration in seconds
    """ 
    command = f'ffprobe -i "{url}" -show_entries format=duration -v quiet -of csv="p=0"'
    result = subprocess.check_output(command, shell=True, text=True)
    Dur = round(float(result.strip()))
    db.update_call_duration(id, Dur)   #-- update the DB with the duration
    return Dur


#-----------------------------------------------------------------------------------
#-----------------------------------------------------------------------------------
def transcribe_call(id: int, url: str):
    """
    Transcribe the audio file and update DB
        Arguments:
            id: int - call ID
            url: str - call audio file URL
        Returns:
            transcript: list - transcript as list of segments
    """
    proc_start = time.time()
    log = Event(msg=f"transcribe_call: Will transcribe Call ID={id}",lvl=3,cid=id)
    db.insert_log(log)
    
    #== perform the transcription
    model = whisper.load_model(WHISPER_MODEL)
    result = model.transcribe(url, task='transcribe', language='en', fp16=False)

    segments = []
    for i in range(len(result["segments"])):
        start_time = round(result["segments"][i]["start"],2)
        end_time = round(result["segments"][i]["end"],2)
        duration = round(end_time - start_time,2)
        text = result["segments"][i]["text"]
        
        segments.append({
            "start": start_time,
            "end": end_time,
            "duration": duration,
            "speaker": "Unknown",
            "text": text
        })

    #-- update the call record in the DB if id is > 0
    if id > 0 :
        db.update_call_transcript(id,segments)

    #-- done with the transcription
    proc_duration = time.time() - proc_start
    log = Event(msg=f"transcribe_call: Transcribed Call ID={id} successfully in {proc_duration:.2f} seconds",lvl=2,cid=id)
    db.insert_log(log)

    return segments


#-----------------------------------------------------------------------------------
#-----------------------------------------------------------------------------------
def make_transcript_flat(transcript: list):
    """
    Convert the transcript to a string format
        Arguments:
            transcript: list - transcript as list of segments
        Returns:
            flat_transcript: str - flat transcript
    """
    flat_transcript = ""
    for segment in transcript:
        flat_transcript += f"- {segment['text']} \n"
    return flat_transcript


#-----------------------------------------------------------------------------------
#-----------------------------------------------------------------------------------
def analyse_call(id: int, transcript, Model: str="ollama/llama3.2" ):
    """
    Get additional analysis for the Call
        Arguments:
            id: int - call ID
            transcript: list - transcript as list of segments
            Model: str - which model to use as per LiteLLM notation
        Returns:
            analysis - text with analysis
            events - logs
    """
    proc_start = time.time()
    events=[]
    log = Event(msg=f"analyse_call: Will analyse Call ID={id}",lvl=3,cid=id)
    events.append(log)
    #db.insert_log(log)
    
    #== perform the analysis
    #-- convert the transcript to a string format
    if type(transcript) is list :
        to_analyze = make_transcript_flat(transcript)
    else:
        to_analyze = transcript

    prompt = """
You are the Customer Support Manager. Analyse the customer support call below for quality of service and include the following formatting as JSON:
* Summarise the conversation as {"Summary":""}
* Calculate Customer Satisfaction Score (CSAT) up to 5 as "CSAT":{"Score":"","Justification":""}
* Is this call resolved the issue (first call resolution indicator) as "FCR":{"Result":"","Reason":""}
* Are any signs of abuse as "Abuse":{"Is Abuse":"","Why Abuse":""}
* Provide customer sentiment category as {"Sentiment":""}
 - -    
Answer questions above based on the transcript of the customer support call:
"""
    prompt = prompt + to_analyze
    ai_response = completion(
        model=Model, 
        messages=[{ "content": prompt,"role": "user"}], 
        api_base="http://localhost:11434"
        )
    analysis = ai_response.choices[0].message.content

    #ai_response: ChatResponse = chat(
    #    model='llama3.2', 
    #    messages=[{'content': prompt,'role': 'user'}]
    #    )
    #analysis = ai_response.message.content # ['message']['content']

    #-- update the call record in the DB
    if id > 0 :
        db.update_call_analysis(id, analysis) 
        logs = extract_params(id, analysis, Model)
        events = events + logs 

    #-- done with the analysis
    proc_duration = time.time() - proc_start
    log = Event(msg=f"analyse_call: Analysed Call ID={id} successfully in {proc_duration:.2f} seconds",lvl=2,cid=id)
    events.append(log)
    #db.insert_log(log)

    return analysis, events


#-----------------------------------------------------------------------------------
#-----------------------------------------------------------------------------------
def get_CSAT_params_from_json(obj: dict, id:int=0):
    """
    Extract Customer Satisfaction Score (CSAT) parameters from JSON and insert them to the DB
        Arguments:
            obj: dict - JSON Object
            id: int - Call ID/cid
        Returns:
            events - logs
    """
    csat_score = obj.get('Score')
    csat_notes = obj.get('Justification')
    csat = {'Score':None,'Justification':None}
    events = []

    if csat_score:    # score is INT
        csat['Score'] = csat_score
        log = Event(msg=f"get_CSAT_params_from_json: got CSAT score={csat_score} from analysis",lvl=3,cid=id)
    else: 
        log = Event(msg="get_CSAT_params_from_json: no CSAT score from analysis",status='warn',lvl=3,cid=id)
    events.append(log)

    if csat_notes and csat_notes.strip():   
        csat['Justification'] = csat_notes
        log = Event(msg="get_CSAT_params_from_json: got CSAT justification from analysis",lvl=3,cid=id)
    else: 
        log = Event(msg="get_CSAT_params_from_json: no CSAT justification from analysis",status='warn',lvl=3,cid=id)
    events.append(log)
    log = db.update_call_CSAT(id,csat['Score'],csat['Justification'])
    events.append(log)
    return events


#-----------------------------------------------------------------------------------
#-----------------------------------------------------------------------------------
def get_FCR_params_from_json(obj: dict, id:int=0):
    """
    Extract first call resolution (FCR) parameters from JSON and insert them to the DB
        Arguments:
            obj: dict - JSON Object
            id: int - Call ID/cid
        Returns:
            events - logs
    """
    fcr_res = obj.get('Result')
    fcr_notes = obj.get('Reason')
    fcr = {'Result':None,'Reason':None}
    events = []

    if fcr_res and fcr_res.strip():   
        fcr['Result'] = fcr_res
        log = Event(msg=f"get_FCR_params_from_json: got FCR result={fcr_res} from analysis",lvl=3,cid=id)
    else: 
        log = Event(msg="get_FCR_params_from_json: no FCR result from analysis",status='warn',lvl=3,cid=id)
    events.append(log)

    if fcr_notes and fcr_notes.strip():   
        fcr['Reason'] = fcr_notes
        log = Event(msg="get_FCR_params_from_json: got FCR justification from analysis",lvl=3,cid=id)
    else: 
        log = Event(msg="get_FCR_params_from_json: no FCR justification from analysis",status='warn',lvl=3,cid=id)
    events.append(log)
    log = db.update_call_FCR(id, fcr['Result'], fcr['Reason'])
    events.append(log)
    return events


#-----------------------------------------------------------------------------------
#-----------------------------------------------------------------------------------
def get_Abuse_params_from_json(obj: dict, id:int=0):
    """
    Extract Abuse indicator from JSON and insert them to the DB
        Arguments:
            obj: dict - JSON Object
            id: int - Call ID/cid
        Returns:
            events - logs
    """
    abuse_res = obj.get('Is Abuse')
    abuse_notes = obj.get('Why Abuse')
    abuse = {'Is Abuse':None,'Why Abuse':None}
    events = []

    if abuse_res and abuse_res.strip():   
        abuse['Is Abuse'] = abuse_res
        log = Event(msg=f"get_Abuse_params_from_json: got Abuse indicator={abuse_res} from analysis",lvl=3,cid=id)
    else: 
        log = Event(msg="get_Abuse_params_from_json: no Abuse indicator from analysis",status='warn',lvl=3,cid=id)
    events.append(log)

    if abuse_notes and abuse_notes.strip():   
        abuse['Why Abuse'] = abuse_notes
        log = Event(msg="get_Abuse_params_from_json: got Abuse justification from analysis",lvl=3,cid=id)
    else: 
        log = Event(msg="get_Abuse_params_from_json: no Abuse justification from analysis",status='warn',lvl=3,cid=id)
    events.append(log)
    log = db.update_call_Abuse(id, abuse['Is Abuse'],abuse['Why Abuse'])
    events.append(log)
    return events


#-----------------------------------------------------------------------------------
#-----------------------------------------------------------------------------------
def get_Summary_from_json(obj: dict, txt:str, id:int=0):
    """
    Extract Summary from JSON and insert it to the DB
        Arguments:
            obj: dict - JSON Object
            txt:str - text with analysis
            id: int - Call ID/cid
        Returns:
            events - logs
    """
    res = None
    events = []
    res = obj.get('Summary')
    if res and res.strip():
        log = Event(msg="get_Summary_from_json: got Summary from analysis as JSON",lvl=1,cid=id)
        events.append(log)
        log = db.update_call_summary(id,res)
    else:
        #-- Try to find Summary as a text
        pattern= r"\"Summary\":\s*\".*?\""
        x = regex.search(pattern, txt, regex.DOTALL)

        if x :
            log = Event(msg="get_Summary_from_json: got Summary from analysis as string",lvl=1,cid=id)
            events.append(log)
            log = db.update_call_summary(id,x.group())
        else:
            log = Event(msg="get_Summary_from_json: no Summary from analysis",status='warn',lvl=1,cid=id)
    events.append(log)
    return events


#-----------------------------------------------------------------------------------
#-----------------------------------------------------------------------------------
def get_Sentiment_from_json(obj: dict, txt:str, id:int=0):
    """
    Extract Sentiment from JSON and insert it to the DB
        Arguments:
            obj: dict - JSON Object
            txt:str - text with analysis
            id: int - Call ID/cid
        Returns:
            events - logs
    """
    res = None
    events = []
    res = obj.get('Sentiment')
    if res and res.strip():
        log = Event(msg="get_Sentiment_from_json: got Sentiment from analysis as JSON",lvl=1,cid=id)
        events.append(log)
        log = db.update_call_sentiment(id,res)
    else:
        #-- Try to find Summary as a text
        pattern= r"\"Sentiment\":\s*\".*?\""
        x = regex.search(pattern, txt, regex.DOTALL)

        if x :
            log = Event(msg="get_Sentiment_from_json: got Sentiment from analysis as string",lvl=1,cid=id)
            events.append(log)
            log = db.update_call_sentiment(id,x.group())
        else:
            log = Event(msg="get_Sentiment_from_json: no Sentiment from analysis",status='warn',lvl=1,cid=id)
    events.append(log)
    return events


#-----------------------------------------------------------------------------------
#-----------------------------------------------------------------------------------
def extract_params(id: int, analysis: str, Model: str="ollama/llama3.2"  ):
    """
    Extract parameters such as CSAT and FCR from the analysis of the Call
        Arguments:
            id: int - call ID
            analysis: str - analysis from LLM
            Model: str - which model has been used as per LiteLLM notation
        Returns:
            events - logs
    """
    events=[]
    log = Event(msg=f"extract_params: Will get params for Call ID={id}",lvl=3,cid=id)
    events.append(log)
    
    #== Step 1: Remove lines starting with ###
    cleaned_text = "\n".join(
        line for line in analysis.splitlines() if not line.strip().startswith("###")
    )
    #-- remove \n
    cleaned_text = cleaned_text.strip().replace('\n', '')


    #== Step 2: Search for all simple JSON objects
    #    This recursive regex captures balanced curly braces 
    pattern = r"\{(?:[^{}]|(?R))*\}"
    matches = regex.findall(pattern, cleaned_text, regex.DOTALL)

    #== Step 3: Convert string matches to actual JSON objects
    result = {}
    for match in matches:
        try:
            obj = json.loads(match)
            result = result | obj
        except json.JSONDecodeError:
            continue  # Skip if not a valid JSON object

    #== Add to logs parameters and update the DB
    logs = get_Summary_from_json(result, cleaned_text, id)
    events = events + logs

    #-- get Customer Satisfaction Score (CSAT)
    tst1 = result.get('CSAT')
    if tst1  and tst1.strip():
        logs = get_CSAT_params_from_json(tst1, id)
    else:
        logs = get_CSAT_params_from_json(result, id)
    events = events + logs

    #-- get First Call Resolution (FCR)
    tst1 = result.get('FCR')
    if tst1  and tst1.strip():
        logs = get_FCR_params_from_json(tst1, id)
    else:
        logs = get_FCR_params_from_json(result, id)
    events = events + logs

    #-- get Signs of abuse "Abuse":{"Is Abuse":"","Justification":""}
    tst1 = result.get('Abuse')       
    if tst1  and tst1.strip():
        logs = get_Abuse_params_from_json(tst1, id)
    else:
        logs = get_Abuse_params_from_json(result, id)
    events = events + logs

    #-- Get Sentiment  {"Sentiment":""}
    logs = get_Sentiment_from_json(result, cleaned_text, id)
    events = events + logs

    #-- done with parameter extraction
    return events

