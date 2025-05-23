# Note: this project uses psycopg3, not psycopg2
import psycopg # type: ignore
import json
import os

# importing necessary functions from dotenv library
from dotenv import load_dotenv
from models import Call, Event


# loading variables from .env file
load_dotenv() 
DB_HOST=os.getenv("DB_HOST")
DB_NAME=os.getenv("DB_NAME")
DB_USER=os.getenv("DB_USER")
DB_PASS=os.getenv("DB_PASS")


#-----------------------------------------------------------------------------------
#-----------------------------------------------------------------------------------
def check_db_connection():
    """
    Check if the DB connection is working
        Arguments:
            None
        Returns:
            string - good  if successful, error description if not
    """
    try:
        conn = psycopg.connect(host=DB_HOST, dbname=DB_NAME, user=DB_USER, password=DB_PASS)
        conn.close()
        return 'good'
    except psycopg.Error as e:
        print(f"check_db_connection: Error connecting to DB: {e}")
        return e


#-----------------------------------------------------------------------------------
#-----------------------------------------------------------------------------------
def insert_log(event: Event):
    """
    Insert a new log entry to the DB
        Arguments:
            event: Event - event to log
        Returns:
            None
    """
    try:
        conn = psycopg.connect(host=DB_HOST, dbname=DB_NAME, user=DB_USER, password=DB_PASS)
        cur = conn.cursor()     #-- Open a cursor to perform database operations
        cur.execute("INSERT INTO logs (ltype,body,cid,level) VALUES(%s,%s,%s,%s);",
                    (event.status, event.msg, event.cid, event.lvl))
        conn.commit()             #-- commit the changes to the database
        cur.close()
    except psycopg.Error as e:
        print(f"insert_log: Error inserting log: {e}")


#-----------------------------------------------------------------------------------
#-----------------------------------------------------------------------------------
def create_new_call(new_call: Call ):
    """
    Create a new call in the DB, get the ID
        Arguments:
            new_call: Call - call object to create
        Returns:
            new_call: Call - updated call object with ID
            events: list - list of events
    """
    events=[]
    try:
        conn = psycopg.connect(host=DB_HOST, dbname=DB_NAME, user=DB_USER, password=DB_PASS)
        cur = conn.cursor()             #-- Open a cursor to perform database operations
        cur.execute("INSERT INTO calls (call_id,audio_url) VALUES(%s,%s) RETURNING cid;",
                    (new_call.call_id, new_call.audio_url))
        new_call.cid = cur.fetchone()[0] #-- get the ID of the new call
        conn.commit()                   #-- commit the changes to the database

        log = Event(msg=f"Created a new call {new_call.audio_url} with ID={new_call.cid}",lvl=2, cid=new_call.cid)
        insert_log(log)                 #-- log the event to DB
        events.append(log)

        cur.close()
        return new_call, events
    except psycopg.Error as e:
        log = Event(msg=f"create_new_call: Error creating new call: {e}",status="error",lvl=1, cid=new_call.cid)
        insert_log(log)            #-- log the event to DB
        print(log)
        return None, events


#-----------------------------------------------------------------------------------
#-----------------------------------------------------------------------------------
def update_call_duration(id: int, duration: int):
    """
    Update the call duration in the DB
        Arguments:
            id: int - call ID
            duration: int - call duration in seconds
        Returns:
            bool - True if successful, False if not
    """
    try:
        conn = psycopg.connect(host=DB_HOST, dbname=DB_NAME, user=DB_USER, password=DB_PASS) 
        cur = conn.cursor()        #-- Open a cursor to perform database operations
        cur.execute("UPDATE calls set duration=%s WHERE cid=%s",
                    (duration, id))
        conn.commit()              #-- commit the changes to the database
        cur.close()
        log = Event(msg=f"Updated duration={duration} seconds for Call ID={id}",lvl=2,cid=id)
        insert_log(log)            #-- log the event to DB
        return True
    except psycopg.Error as e:
        log = Event(msg=f"update_call_duration: Error updating call duration: {e}",status="error",lvl=1,cid=id)
        insert_log(log)            #-- log the event to DB
        print(log)
        return False


#-----------------------------------------------------------------------------------
#-----------------------------------------------------------------------------------
def update_call_transcript(id: int, transcript: list):
    """
    Update the call transcript in the DB
        Arguments:
            id: int - call ID
            transcript: dict - call transcript as JSON
        Returns:
            bool - True if successful, False if not
    """
    try:
        conn = psycopg.connect(host=DB_HOST, dbname=DB_NAME, user=DB_USER, password=DB_PASS) 
        cur = conn.cursor()         #-- Open a cursor to perform database operations
        to_add = json.dumps(transcript) #-- convert the transcript to JSON
        cur.execute("UPDATE calls set transcript=%s WHERE cid=%s",
                    (to_add, id))
        conn.commit()       #-- commit the changes to the database

        cur.close()
        log = Event(msg=f"Updated transcript for Call ID={id}",lvl=2,cid=id)
        insert_log(log)            #-- log the event to DB
        return True
    except psycopg.Error as e:
        log = Event(msg=f"update_call_transcript: Error updating call transcript: {e}",status="error",lvl=1,cid=id)
        insert_log(log)            #-- log the event to DB
        print(log)
        return False


#-----------------------------------------------------------------------------------
#-----------------------------------------------------------------------------------
def update_call_analysis(id: int, analysis: str ):
    """
    Update call parameters in the DB
        Arguments:
            id: int - call ID (cid)
            analysis: str - text to insert/update
        Returns:
            bool - True if successful, False if not
    """
    try:
        conn = psycopg.connect(host=DB_HOST, dbname=DB_NAME, user=DB_USER, password=DB_PASS) 
        cur = conn.cursor()     #-- Open a cursor to perform database operations

        cur.execute("UPDATE calls set analysis=%s WHERE cid=%s",
                    (analysis, id))

        conn.commit()        #-- commit the changes to the database

        cur.close()
        log = Event(msg=f"Updated analysis for Call ID={id}",lvl=2,cid=id)
        insert_log(log)            #-- log the event to DB
        return True
    except psycopg.Error as e:
        log = Event(msg=f"update_call_analysis: Error updating call analysis: {e}",status="error",lvl=1,cid=id)
        insert_log(log)            #-- log the event to DB
        print(log)
        return False


#-----------------------------------------------------------------------------------
#-----------------------------------------------------------------------------------
def update_call_summary(id: int, summary: str):
    """
    Update the call summary in the DB
        Arguments:
            id: int - call ID
            summary: str - call summary performed by LLM
        Returns:
            log - Event
    """
    try:
        conn = psycopg.connect(host=DB_HOST, dbname=DB_NAME, user=DB_USER, password=DB_PASS) 
        cur = conn.cursor()        #-- Open a cursor to perform database operations
        cur.execute("UPDATE calls set summary=%s WHERE cid=%s",
                    (summary, id))
        conn.commit()              #-- commit the changes to the database
        cur.close()
        log = Event(msg=f"Updated summary for Call ID={id}",lvl=2,cid=id)
        insert_log(log)            #-- log the event to DB
        return log
    except psycopg.Error as e:
        log = Event(msg=f"update_call_summary: Error updating call summary: {e}",status="error",lvl=1,cid=id)
        insert_log(log)            #-- log the event to DB
        #print(log)
        return log


#-----------------------------------------------------------------------------------
#-----------------------------------------------------------------------------------
def update_call_CSAT(id: int, score: str, reason: str=''):
    """
    Update the call Customer Satisfaction Score params in the DB
        Arguments:
            id: int - call ID
            score: str - CSAT score as a digit
            reason: str - justification
        Returns:
            log - Event
    """
    try:
        conn = psycopg.connect(host=DB_HOST, dbname=DB_NAME, user=DB_USER, password=DB_PASS) 
        cur = conn.cursor()        #-- Open a cursor to perform database operations
        cur.execute("UPDATE calls set csat_score=%s,csat_notes=%s WHERE cid=%s",
                    (score, reason, id))
        conn.commit()              #-- commit the changes to the database
        cur.close()
        log = Event(msg=f"Updated CSAT for Call ID={id}",lvl=2,cid=id)
        insert_log(log)            #-- log the event to DB
        return log
    except psycopg.Error as e:
        log = Event(msg=f"update_call_CSAT: Error updating call CSAT: {e}",status="error",lvl=1,cid=id)
        insert_log(log)            #-- log the event to DB
        #print(log)
        return log

#-----------------------------------------------------------------------------------
#-----------------------------------------------------------------------------------
def str2bool(txt:str):
    '''
    Convert string to bool
        Arguments:
            txt: string with Yes or No
        Returns:
            True/False/None
    '''
    if not txt:
        return None
    if txt.lower() == 'yes':
        return True
    elif txt.lower() == 'true':
        return True
    else :
        return False

#-----------------------------------------------------------------------------------
#-----------------------------------------------------------------------------------
def update_call_FCR(id: int, is_fcr: str, reason: str=''):
    """
    Update the call First Call Resolution (FCR) params in the DB
        Arguments:
            id: int - call ID
            is_fcr: str - Yes/No
            reason: str - justification
        Returns:
            log - Event
    """
    try:
        conn = psycopg.connect(host=DB_HOST, dbname=DB_NAME, user=DB_USER, password=DB_PASS) 
        cur = conn.cursor()        #-- Open a cursor to perform database operations
        cur.execute("UPDATE calls set is_fcr=%s,fcr_notes=%s WHERE cid=%s",
                    (str2bool(is_fcr), reason, id))
        conn.commit()              #-- commit the changes to the database
        cur.close()
        log = Event(msg=f"Updated FCR for Call ID={id}",lvl=2,cid=id)
        insert_log(log)            #-- log the event to DB
        return log
    except psycopg.Error as e:
        log = Event(msg=f"update_call_FCR: Error updating call FCR: {e}",status="error",lvl=1,cid=id)
        insert_log(log)            #-- log the event to DB
        #print(log)
        return log


#-----------------------------------------------------------------------------------
#-----------------------------------------------------------------------------------
def update_call_Abuse(id: int, is_abuse: str, reason: str=''):
    """
    Update the call Abuse indicator params in the DB
        Arguments:
            id: int - call ID
            is_abuse: str - Yes/No
            reason: str - justification
        Returns:
            log - Event
    """
    try:
        conn = psycopg.connect(host=DB_HOST, dbname=DB_NAME, user=DB_USER, password=DB_PASS) 
        cur = conn.cursor()        #-- Open a cursor to perform database operations
        cur.execute("UPDATE calls set is_abuse=%s,abuse_notes=%s WHERE cid=%s",
                    (str2bool(is_abuse), reason, id))
        conn.commit()              #-- commit the changes to the database
        cur.close()
        log = Event(msg=f"Updated Abuse indicator for Call ID={id}",lvl=2,cid=id)
        insert_log(log)            #-- log the event to DB
        return log
    except psycopg.Error as e:
        log = Event(msg=f"update_call_Abuse: Error updating call Abuse indicator: {e}",status="error",lvl=1,cid=id)
        insert_log(log)            #-- log the event to DB
        #print(log)
        return log


#-----------------------------------------------------------------------------------
#-----------------------------------------------------------------------------------
def update_call_sentiment(id: int, Sentiment: str):
    """
    Update the call Sentiment in the DB
        Arguments:
            id: int - call ID
            Sentiment: str - call Sentiment identified by LLM
        Returns:
            log - Event
    """
    try:
        conn = psycopg.connect(host=DB_HOST, dbname=DB_NAME, user=DB_USER, password=DB_PASS) 
        cur = conn.cursor()        #-- Open a cursor to perform database operations
        cur.execute("UPDATE calls set cust_sentiment=%s WHERE cid=%s",
                    (Sentiment, id))
        conn.commit()              #-- commit the changes to the database
        cur.close()
        log = Event(msg=f"Updated Sentiment for Call ID={id}",lvl=2,cid=id)
        insert_log(log)            #-- log the event to DB
        return log
    except psycopg.Error as e:
        log = Event(msg=f"update_call_sentiment: Error updating call Sentiment: {e}",status="error",lvl=1,cid=id)
        insert_log(log)            #-- log the event to DB
        #print(log)
        return log


#-----------------------------------------------------------------------------------
#-----------------------------------------------------------------------------------
def get_call_details(id: int):
    """
    Get call details from the DB
        Arguments:
            id: int - call ID
        Returns:
            call - call details as dict
            events - list of events
    """
    try:
        conn = psycopg.connect(host=DB_HOST, dbname=DB_NAME, user=DB_USER, password=DB_PASS) 
        cur = conn.cursor()        #-- Open a cursor to perform database operations
        cur.execute("SELECT cid,call_id,agent_id,duration,transcript,"+
                    "REGEXP_REPLACE(audio_url,'/srv/vocamind/data','/audio') as audio_url,summary,"+
                    "csat_score,is_fcr,is_abuse,cust_sentiment,fcr_notes,csat_notes,abuse_notes,"+
                    "to_timestamp(created_at) as created_at,analysis FROM calls WHERE cid=%s",(id,))
        result = cur.fetchone() #-- get the call details
        cur.close()
        if result:
            call = {"cid":result[0], "call_id":result[1], "agent_id":result[2],"duration":result[3], 
                        "transcript":result[4], "audio_url":result[5], "summary":result[6],
                        "csat_score":result[7], "is_fcr":result[8], "is_abuse":result[9],
                        "cust_sentiment":result[10], "fcr_notes":result[11],"csat_notes":result[12],
                         "abuse_notes":result[13], "created_at":result[14], "analysis":result[15]}
            log = Event(msg=f"Retrieved call details for Call ID={id}",lvl=2,cid=id)
            #insert_log(log)            #-- log the event to DB
            return call, log
        else:
            log = Event(msg=f"get_call_details: No call found with ID={id}",lvl=1,cid=id)
            print(log)
            return Call(), log
    except psycopg.Error as e:
        log = Event(msg=f"get_call_details: Error obtaining call details: {e}",status="error",lvl=1,cid=id)
        print(log)
        return Call(), log


#-----------------------------------------------------------------------------------
#-----------------------------------------------------------------------------------
def get_call_list():
    '''
    Get the list of calls from the DB
        Arguments:
            None
        Returns:
            call_list: list - list of calls as dict 
            events: list - list of events as Event object
    '''
    try:
        conn = psycopg.connect(host=DB_HOST, dbname=DB_NAME, user=DB_USER, password=DB_PASS) 
        cur = conn.cursor()        #-- Open a cursor to perform database operations
        cur.execute("SELECT cid, call_id, to_timestamp(created_at)::date, agent_name, audio_url, "+
                    "duration, CASE WHEN transcript IS NULL THEN 'Empty' ELSE 'Text' END AS is_transcript, "+
                    "CASE WHEN analysis IS NULL THEN 'Empty' ELSE 'Text' END AS is_analysis, "+
                    " csat_score, is_fcr, is_abuse, cust_sentiment "+
                    " FROM calls LEFT JOIN agents using(agent_id) ORDER BY created_at DESC")
        result = cur.fetchall() #-- get the call list
        cur.close()
        call_list = []
        events=[]
        for row in result:
            call = {"cid":row[0], "call_id":row[1], "created_at":row[2], "agent_name":row[3], 
                    "audio_url":row[4], "duration":row[5], "is_transcript":row[6], "is_analysis":row[7],
                    "csat_score":row[8], "is_fcr":row[9], "is_abuse":row[10], "cust_sentiment":row[11]}
            call_list.append(call)
        log = Event(msg=f"Retrieved list of calls with {len(call_list)} members",lvl=2,cid=row[0])
        events.append(log)
        return call_list, events
    except psycopg.Error as e:
        log = Event(msg=f"get_call_list: Error obtaining call list: {e}",status="error",lvl=1)
        print(log)
        return [], events.append(log)


#-----------------------------------------------------------------------------------
#-----------------------------------------------------------------------------------
def get_agents():
    '''
    Get the list of agents from the DB
        Arguments:
            None
        Returns:
            agents: list - list of agents  
            events: list - list of events as Event object
    '''
    try:
        conn = psycopg.connect(host=DB_HOST, dbname=DB_NAME, user=DB_USER, password=DB_PASS) 
        cur = conn.cursor()        #-- Open a cursor to perform database operations
        cur.execute("SELECT agent_id, agent_name FROM agents")
        result = cur.fetchall() #-- get the list
        cur.close()
        agents=[]
        events=[]
        for row in result:
            agent = {"agent_id":row[0], "agent_name":row[1]}
            agents.append(agent)
        #print(agents)
        log = Event(msg=f"Retrieved list of agents with {len(agents)} members",lvl=2,cid=row[0])
        events.append(log)
        return agents, events
    except psycopg.Error as e:
        log = Event(msg=f"get_agents: Error obtaining list of agents: {e}",status="error",lvl=1)
        print(log)
        return [], events.append(log)


#-----------------------------------------------------------------------------------
#-----------------------------------------------------------------------------------
def update_agent_id(cid: int, agent_id: int):
    '''
    Update an agent for the call
        Arguments:
            call_id: int - call ID
            agent_id: int - agent ID from agents table
        Returns:
            response: dict - events
    '''
    try:
        events=[]
        conn = psycopg.connect(host=DB_HOST, dbname=DB_NAME, user=DB_USER, password=DB_PASS) 
        cur = conn.cursor()        #-- Open a cursor to perform database operations
        cur.execute("UPDATE calls set agent_id=%s WHERE cid=%s",
                    (agent_id, cid))
        conn.commit()       #-- commit the changes to the database

        cur.close()
        log = Event(msg=f"Updated agent ID to {agent_id} for the call with ID={cid}",lvl=2,cid=cid)
        events.append(log)
        return events
    except psycopg.Error as e:
        log = Event(msg=f"update_agent_id: Error updating agent ID for the call: {e}",status="error",lvl=1,cid=cid)
        events.append(log)
        return events


#-----------------------------------------------------------------------------------
#-----------------------------------------------------------------------------------
def get_audio_file(id: int):
    """
    Get call specific path to the audio file from the DB
        Arguments:
            id: int - call ID
        Returns:
            path - audio file path as string
            events - list of events
    """
    try:
        conn = psycopg.connect(host=DB_HOST, dbname=DB_NAME, user=DB_USER, password=DB_PASS) 
        cur = conn.cursor()        #-- Open a cursor to perform database operations
        cur.execute("SELECT audio_url "+
                    " FROM calls WHERE cid=%s",(id,))
        result = cur.fetchone() #-- get the result
        cur.close()
        if result:
            log = Event(msg=f"Got audio file path for Call ID={id}",lvl=2,cid=id)
            return result[0], [log]
        else:
            log = Event(status='warn',msg=f"get_audio_file: No call found with ID={id}",lvl=1,cid=id)
            #print_db_event(log)
            return '', [log]
    except psycopg.Error as e:
        log = Event(msg=f"get_audio_file: Error obtaining call details: {e}",status="error",lvl=1,cid=id)
        #print_db_event(log)
        return '', [log]


#-----------------------------------------------------------------------------------
#-----------------------------------------------------------------------------------
def get_calls_total():
    '''
    Get number of calls with normal status from the DB
        Arguments:
            None
        Returns:
            total_number: int - stat  
            events: list - list of events as Event object
    '''
    try:
        conn = psycopg.connect(host=DB_HOST, dbname=DB_NAME, user=DB_USER, password=DB_PASS) 
        cur = conn.cursor()        #-- Open a cursor to perform database operations
        cur.execute("select count(*) as num from calls where cstatus >= 40;")
        result = cur.fetchone()[0] #-- get the number
        cur.close()
        log = Event(msg=f"Retrieved total number of calls={result}",lvl=2)
        return result, [log]
    except psycopg.Error as e:
        log = Event(msg=f"get_calls_total: Error getting total number of calls: {e}",status="error",lvl=1)
        print(log)
        return [], [log]


#-----------------------------------------------------------------------------------
#-----------------------------------------------------------------------------------
def get_csat_stats():
    '''
    Get number of calls with specific CSAT score from the DB
        Arguments:
            None
        Returns:
            stats: dict - "stats":{"csat_score_x":count}
            events: list - list of events as Event object
    '''
    try:
        conn = psycopg.connect(host=DB_HOST, dbname=DB_NAME, user=DB_USER, password=DB_PASS) 
        cur = conn.cursor()        #-- Open a cursor to perform database operations
        cur.execute("select rid as csat_score, (select count(*) from calls c where c.csat_score=(rid)::smallint and "+
                    " c.csat_score is not null) as num  from refs where gid='csat_score';")
        #-- old SQL: select csat_score,count(*) as num from calls group by csat_score order by csat_score;
        result = cur.fetchall() #-- get the list
        cur.close()
        log = Event(msg="Retrieved CSAT stats",lvl=2)
        stats = {}
        for row in result:
            stats['csat_stat_'+str(row[0])] = row[1]
        return stats, [log]
    except psycopg.Error as e:
        log = Event(msg=f"get_csat_stats: Error getting CSAT stats: {e}",status="error",lvl=1)
        print(log)
        return [], [log]


#-----------------------------------------------------------------------------------
#-----------------------------------------------------------------------------------
def get_fcr_stats():
    '''
    Get number of calls with first call resolution (FCR) flag from the DB
        Arguments:
            None
        Returns:
            stats: dict - "stats":{"fcr_False":count,"fcr_True":count}
            events: list - list of events as Event object
    '''
    try:
        conn = psycopg.connect(host=DB_HOST, dbname=DB_NAME, user=DB_USER, password=DB_PASS) 
        cur = conn.cursor()        #-- Open a cursor to perform database operations
        cur.execute("select is_fcr,count(*) as num from calls where is_fcr is not null group by is_fcr;")
        result = cur.fetchall() #-- get the list
        cur.close()
        log = Event(msg="Retrieved FCR stats",lvl=2)
        stats = {}
        for row in result:
            stats['fcr_'+str(row[0])] = row[1]
        return stats, [log]
    except psycopg.Error as e:
        log = Event(msg=f"get_fcr_stats: Error getting FCR stats: {e}",status="error",lvl=1)
        print(log)
        return [], [log]


#-----------------------------------------------------------------------------------
#-----------------------------------------------------------------------------------
def get_refs():
    '''
    Return list of text references from table REFS
        Arguments:
            None
        Returns:
            refs: list - list of text references  
            events: list - list of events as Event object
    '''
    try:
        conn = psycopg.connect(host=DB_HOST, dbname=DB_NAME, user=DB_USER, password=DB_PASS) 
        cur = conn.cursor()        #-- Open a cursor to perform database operations
        cur.execute("select gid,rid,note,sort_order from refs order by gid,rid,sort_order;")
        result = cur.fetchall() #-- get the list
        cur.close()
        events=[]
        refs=dict()
        gid=result[0][0]
        refs[gid] = dict()
        for row in result:
            if gid != row[0]:
                gid = row[0]
                refs[gid] = dict()
            rid = row[1]
            refs[gid][rid] = row[2]

        log = Event(msg=f"Retrieved list of text references with {len(result)} members",lvl=2)
        events.append(log)
        return refs, events
    except psycopg.Error as e:
        log = Event(msg=f"get_refs: Error obtaining text references: {e}",status="error",lvl=1)
        print(log)
        return [], events.append(log)

