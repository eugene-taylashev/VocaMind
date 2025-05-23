#!/usr/bin/python
# /data/rag/bin/python3
#==========================================================================
#-- Communicate with the VocaMind application from the command line
#-- Plus some verification functions
#==========================================================================
import sys
import os.path
import re
import subprocess

import stasks
import db
from models import Call, Event
from btasks import transcribe_call, make_transcript_flat, analyse_call


#==========================================================================
#  Global Variables
#==========================================================================
DebugLevel=3    #-- Level of output details: 1=minimum -> 3=maximum
Call_CID=0
audioFile=''
transFile=''
gHelps = {}

gHelps['main'] = '''
Command line interface to the VocaMind application

Usage:
    vocamind-cli.py command [options]
    
Where:
    command is one of
        help       - output command specific help
        check      - check status of components
        list       - list different arrays
            models - list supported LLM models
            agents - list Customer support agents
        get        - Fetch a specific entry and field from the DB
            transcript - print a flatten transcript for a Call with cid
            analysis - print the LLM analysis for a Call with cid from the DB
        add        - add an element
            call   - add a new call to the DB
            agent  - add a new Customer Support agent to the DB
        transcribe - transcribe an audio file
        analyse    - analyse call transcript
        celery     - check status of background tasks

'''

gHelps['list'] = '''
List different internal arrays

Usage:
    vocamind-cli.py list sub-command [options]
Where:
    sub-command is one of
        models - list supported LLM models
        agents - list Customer support agents
        help   - see this help

'''

gHelps['add'] = '''
Add a new element to the DB

Usage:
    vocamind-cli.py add sub-command [options]
Where:
    sub-command is one of
        call --call_id=string --audio=/path  - add a new call with Call ID and path to the audio file
        help   - see this help
'''

gHelps['get']  = '''
Fetch a specific entry and field from the DB

Usage:
    vocamind-cli.py get transcript --cid=N   - print a flatten transcript for a Call with cid
    vocamind-cli.py get analysis --cid=N - print the LLM analysis for a Call with cid from the DB

'''

gHelps['transcribe']  = '''
Transcribe an audio from a file or DB

Usage:
    vocamind-cli.py transcribe --cid=N   - get audio path from DB by cid number and update the DB with the result
    vocamind-cli.py transcribe --audio=/path - transcribe the audio file and output results

'''

gHelps['analyse']  = '''
Analyse call transcript from file or DB, specify a LLM model

Usage:
    vocamind-cli.py analyse --cid=N  [option]     - analyse for specific call by CID and update the DB
    vocamind-cli.py analyse --file=/path [option] - get the transcript file and output analysed parameters

Where:
    option is
        --model=openai/gpt-4o-mini  - specify which model to use. List models with "list models" command
'''

gHelps['celery']  = '''
Check status of background tasks using Celery

Usage:
    vocamind-cli.py celery - get the list of workers and what the workers are currently doing
'''


#-----------------------------------------------------------------------------------
#-----------------------------------------------------------------------------------
def out(logs: list, level: int=DebugLevel):
    '''
    Output internal application messages based on level flag
        Arguments:
            logs - one or more Events
            level - level of details 0 - nothing, 3 - max
        Returns:
            None
    '''
    for e in logs:
        if e.lvl <= level :
            stasks.print_event(e)


#-----------------------------------------------------------------------------------
#-----------------------------------------------------------------------------------
def OutHelp(topic: str=''):
    '''
    Output all helps and quit the application
        Arguments:
            topic - string with command to provide help about
        Returns:
            None
    '''
    topic = topic.lower()
    if topic in gHelps:
        help =  gHelps[topic]
    else :
        help = gHelps['main']
    print(help)
    quit(0)


#==================================================================================
#  MAIN
#==================================================================================
# total arguments
argsLen = len(sys.argv)
out([Event(msg=f"Total arguments passed: {argsLen}",lvl=3)])

if argsLen < 2 :
    OutHelp()

#-- parse options from arguments
argumentList = sys.argv[2:] # Remove 1st argument from the list of command line arguments
for a in argumentList:
    if re.search(r"^--", a):
        x = re.search(r"^--\w+", a)
        if x :
            opt = x.group()
        else :
            next
        x = re.search(r"=.*$", a)
        if x :
            val = x.group()
            val = val[1:]
        else :
            next
        #print(f"opt={opt}; val={val}")
        match opt.lower():
            case '--debug':
                DebugLevel=int(val)    #-- Set new Debug Level
            case '--cid':
                Call_CID=int(val) 
                out([Event(msg=f"CID={Call_CID}",lvl=2)])            
            case '--call_id':
                call_ID=val
                out([Event(msg=f"Call ID={call_ID}",lvl=2)])            
            case '--audio':
                audioFile=str(val) 
                out([Event(msg=f"Audio file path={audioFile}",lvl=2)])            
            case '--file':
                transFile=str(val) 
                out([Event(msg=f"Transcript file path={transFile}",lvl=2)])            

#-- Get the command
argCommand = sys.argv[1]
out([Event(msg=f"Command: {argCommand}",lvl=3)])
argSubCommand = ''

#-- Main switch of tasks
match argCommand.lower():
    case 'help':
        if argsLen >= 3 :
            argSubCommand = sys.argv[2] #-- get sub-command
            if argSubCommand.lower() in gHelps:
                OutHelp(argSubCommand.lower())
            else:
                OutHelp('main')
        else:
            OutHelp('main')

    case 'check':
        events = stasks.check_component_status()
        out(events)

    case 'list':
        if argsLen >= 3 :
            argSubCommand = sys.argv[2] #-- get sub-command
        match argSubCommand.lower():
            case 'models':
                models, default_model, events= stasks.enum_llm_models()
                #-- output models
                for m in models:
                    res = m
                    if m == default_model :
                        res += ' (default)'
                    print(res)

            case 'agents':
                agents, events = db.get_agents()
                #-- output agents
                out(events)
                for a in agents:
                    print(f"{a['agent_id']}: {a['agent_name']}")

            case 'refs':
                refs, events = db.get_refs()
                print(refs)

            case 'help':
                OutHelp('list')

            case _:
                out([Event(status='error',msg=f"Invalid sub-command: {argSubCommand}",lvl=0)])
                OutHelp('list')

    case 'add':
        if argsLen >= 3 :
            argSubCommand = sys.argv[2] #-- get sub-command
        match argSubCommand.lower():
            case 'call':
                new_call = Call(call_id=call_ID, audio_url = audioFile)
                #-- create a new call row in the DB
                new_call, logs = db.create_new_call(new_call)
                out(logs)

            case 'help':
                OutHelp('add')

            case _:
                out([Event(status='error',msg=f"Invalid sub-command: {argSubCommand}",lvl=0)])
                OutHelp('add')

    case 'get':
        if argsLen >= 3 :
            argSubCommand = sys.argv[2] #-- get sub-command
        match argSubCommand.lower():
            case 'transcript':
                call_details, log = db.get_call_details(Call_CID)
                out([log])
                print( make_transcript_flat(call_details["transcript"]))
                

            case 'analysis':
                call_details, log = db.get_call_details(Call_CID)
                out([log])
                print( call_details["analysis"])

            case 'help':
                OutHelp('get')

            case _:
                out([Event(status='error',msg=f"Invalid sub-command: {argSubCommand}",lvl=0)])
                OutHelp('get')

    case 'transcribe':
        if argsLen >= 3 :
            argSubCommand = sys.argv[2] #-- get sub-command
        out([Event(msg=f"cid={Call_CID}, audio_file={audioFile}",lvl=3)]) 

        if argSubCommand.lower() == 'help' :
            OutHelp('transcribe')

        elif Call_CID > 0 :
            #Case: transcribe --cid=N   - get audio path from DB by cid number and update the DB with the result
            path, logs = db.get_audio_file(Call_CID)
            out(logs)
            transcribe_call(Call_CID,path)

        elif os.path.isfile(audioFile) :
            #Case: transcribe --audio=/path - transcribe the audio file and output results
            segments = transcribe_call(0,audioFile)
            print( make_transcript_flat(segments))

        else :
            out([Event(msg='Unclear command parameters or file does not exist',status='error',lvl=0)])


    case 'analyse':
        if argsLen >= 3 :
            argSubCommand = sys.argv[2] #-- get sub-command
        out([Event(msg=f"cid={Call_CID}, trans_file={transFile}",lvl=3)]) 

        if argSubCommand.lower() == 'help' :
            OutHelp('analyse')

        elif Call_CID > 0 :
            #Case: analyse --cid=N  [option]     - analyse for specific call by CID and update the DB
            details, log = db.get_call_details(Call_CID)
            out([log])
            #events.append(logs)
            analysis, logs = analyse_call(Call_CID, details['transcript'])
            out(logs)
            #db.update_call_analysis( Call_CID, analysis)

        elif os.path.isfile(transFile) :
            #Case: analyse --file=/path [option] - get the transcript file and output analysed parameters
            with open(transFile, 'r') as f:
                transcript = f.read()
            analysis, logs = analyse_call(0,transcript)
            out(logs)
            print( analysis )

        else :
            out([Event(msg='Unclear command parameters or file does not exist',status='error',lvl=0)])

    case 'celery':
        # Assumption: the Celery app (btasks.py) is in the same directory as this scipt
        out([Event(msg='Check Celery status',lvl=2)])
        #-- get current scipt path. 
        script_path = file_path = os.path.realpath(__file__)
        #-- run status command
        try:
            command = f'/data/rag/bin/python /usr/bin/celery -A btasks inspect active'
            result = subprocess.check_output(command, shell=True, text=True)
            print(result)
        except subprocess.CalledProcessError as e:
            log = Event(status="error",msg="Celery service is NOT active")
            out([log])
        #celery -A btasks status
        #celery -A btasks inspect active

    case _:
        out([Event(status='error',msg=f"Invalid command: {argCommand}",lvl=0)])
        OutHelp('main')


