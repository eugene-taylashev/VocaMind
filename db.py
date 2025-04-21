# Note: this project uses psycopg3, not psycopg2
import psycopg # type: ignore

import os

# importing necessary functions from dotenv library
from dotenv import load_dotenv


import tasks
from models import Call, Event


# loading variables from .env file
load_dotenv() 
DB_HOST=os.getenv("DB_HOST")
DB_NAME=os.getenv("DB_NAME")
DB_USER=os.getenv("DB_USER")
DB_PASS=os.getenv("DB_PASS")


#-----------------------------------------------------------------------------------
#-----------------------------------------------------------------------------------
def insert_log(event: Event):
    """
    insert a new log entry to the DB
    """
    with psycopg.connect(host=DB_HOST, dbname=DB_NAME, user=DB_USER, password=DB_PASS) as conn: 
        #-- Open a cursor to perform database operations
        cur = conn.cursor()

        cur.execute("INSERT INTO logs (ltype,body) VALUES(%s,%s);",
                    (event.status, event.msg))
        #-- commit the changes to the database
        conn.commit()

        cur.close()

#-----------------------------------------------------------------------------------
#-----------------------------------------------------------------------------------
def create_new_call(new_call: Call ):
    """
    create a new call in the DB, get the ID
    """
    events=[]

    with psycopg.connect(host=DB_HOST, dbname=DB_NAME, user=DB_USER, password=DB_PASS) as conn: 
        #-- Open a cursor to perform database operations
        cur = conn.cursor()

        cur.execute("INSERT INTO calls (call_id,audio_url) VALUES(%s,%s);",
                    (new_call.call_id, new_call.audio_url))
        #-- commit the changes to the database
        conn.commit()

        #-- get the ID of the new call
        cur.execute("SELECT id FROM calls WHERE call_id = %s;", (new_call.call_id,))
        new_call.id = cur.fetchone()[0]
        events.append(tasks.dlog({"msg":f"Created a new call record with ID={new_call.id} in the DB","lvl":2}))

        cur.close()
        return new_call, events


#-----------------------------------------------------------------------------------
#-----------------------------------------------------------------------------------
def update_call_transcript(new_call: Call):
    """
    Update the call transcript in the DB
    """
    events=[]

    with psycopg.connect(host=DB_HOST, dbname=DB_NAME, user=DB_USER, password=DB_PASS) as conn: 
        #-- Open a cursor to perform database operations
        cur = conn.cursor()

        cur.execute("UPDATE calls set transcript=%s WHERE call_id=%s",
                    (new_call.transcript, new_call.call_id))
        #-- commit the changes to the database
        conn.commit()

        cur.close()

        events.append(tasks.dlog({"msg":f"Updated a DB record with transcript for Call ID={new_call.call_id}"}))
        return new_call, events


#-----------------------------------------------------------------------------------
#-----------------------------------------------------------------------------------
def update_call_analysis(new_call: Call ):
    """
    Update call parameters in the DB
    More: https://www.squash.io/connecting-fastapi-with-postgresql-a-practical-approach/
    """
    events=[]

    with psycopg.connect(host=DB_HOST, dbname=DB_NAME, user=DB_USER, password=DB_PASS) as conn: 
        #-- Open a cursor to perform database operations
        cur = conn.cursor()

        cur.execute("UPDATE calls set analysis=%s,satisfaction=5 WHERE call_id=%s",
                    (new_call.analysis, new_call.call_id))

        #-- commit the changes to the database
        conn.commit()

        cur.close()

        events.append(tasks.dlog({"msg":f"Updated a DB record with analysis for Call ID={new_call.call_id}"}))
        return new_call, events

#-----------------------------------------------------------------------------------
#-----------------------------------------------------------------------------------
def update_call_duration(new_call: Call):
    """
    Update the call duration in the DB
    """
    events=[]

    with psycopg.connect(host=DB_HOST, dbname=DB_NAME, user=DB_USER, password=DB_PASS) as conn: 
        #-- Open a cursor to perform database operations
        cur = conn.cursor()

        cur.execute("UPDATE calls set duration=%s WHERE call_id=%s",
                    (new_call.duration, new_call.call_id))
        #-- commit the changes to the database
        conn.commit()

        cur.close()

        events.append(tasks.dlog({"msg":f"Updated a DB record with duration for Call ID={new_call.call_id}"}))
        return new_call, events

