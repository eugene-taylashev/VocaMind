-- ----------------------------------------------------------------------------
-- Create table refs for storing references 
-- ----------------------------------------------------------------------------
CREATE TABLE refs (
        gid         varchar(50), 
        rid         varchar(100), 
        lang        varchar(2) DEFAULT 'en',  -- ISO 639-1 Language Code
        note        varchar,
        sort_order  INTEGER,
        PRIMARY KEY(gid,rid,lang)
        );

insert into refs (gid,rid,note) values
-- Special items
  ('ltype','ok','OK'),          
  ('ltype','error','Error'),  
  ('ltype','warn','Warning'), 

-- CSAT Score Tags
  ('csat_score','1','Very dissatisfied'),          
  ('csat_score','2','Dissatisfied'),  
  ('csat_score','3','Neutral'), 
  ('csat_score','4','Satisfied'), 
  ('csat_score','5','Very satisfied'), 

-- Customer sentiment categories
  ('cust_sentim','Neutral','No strong emotion is expressed; interaction is factual.'),
  ('cust_sentim','Satisfaction','Customer is pleased with the service or outcome.'),
  ('cust_sentim','Frustration','Customer expresses annoyance or irritation.'),
  ('cust_sentim','Confusion','Customer is unclear or doesn''t understand information provided.'),
  ('cust_sentim','Anger','Customer is upset or hostile.'),
  ('cust_sentim','Gratitude','Customer expresses thanks or appreciation.'),
  ('cust_sentim','Disappointment','Customer feels let down by service or expectations.');


-- ----------------------------------------------------------------------------
-- Create table agents for agent identity
-- ----------------------------------------------------------------------------
CREATE TABLE agents (
    agent_id serial PRIMARY KEY,  -- unique ID for cross-reference
    agent_name VARCHAR(255) NOT NULL,      -- agent name
    sample_audio_url VARCHAR  -- URL to sample audio for the agent
);

-- Test data
insert into agents (agent_name)
values 
('Ariana Grande'),
('Taylor Swift'),
('Bruno Mars');


-- ----------------------------------------------------------------------------
-- Create table calls to store call details
-- ----------------------------------------------------------------------------
CREATE table calls (
    cid             bigserial PRIMARY KEY,  -- Call ID for cross-reference
    call_id         VARCHAR(20) not NULL, -- human-readable unique identifier for the call
    agent_id        int,  -- foreign key to agents table
    audio_url       VARCHAR,
    duration        INT,   -- call duration in seconds
    transcript      jsonb,  -- call transcript as an array of JSON objects
    analysis        TEXT,   -- raw reply from LLM
    summary         TEXT,   -- call summary
    csat_score      smallint, -- Customer Satisfaction Score (CSAT)
    csat_notes      VARCHAR,  -- CSAT justification
    is_fcr          boolean,  -- first call resolution (FCR) indicator
    fcr_notes       VARCHAR,  -- FCR justification
    is_abuse        boolean,  -- Abuse indicator
    abuse_notes     VARCHAR,
    cust_sentiment  VARCHAR(40),  -- customer sentiment category id; See refs.gid='cust_sentim' for more details
    cstatus         smallint DEFAULT 50,    -- call status: 20 - unvisible; 50 - unprocessed / new, 40 - processed / normal. 
    created_at      bigint NOT NULL DEFAULT EXTRACT(EPOCH FROM current_timestamp),  -- when information has been updated (epoch),
    other           json,
    CONSTRAINT fk_agent FOREIGN KEY (agent_id) 
        REFERENCES agents(agent_id)
);

-- tst jsonb[],
-- [{"start": 0.0, "end": 7.0, "duration": 7.0, "speaker": "Unknown", "text": " Thank you for calling Coats and Gowns. My name is Sam. How can I help you?"}, {"start": 7.0, "end": 16.68, "duration": 9.68, "speaker": "Unknown", "text": " Yes, I bought a coat from you guys but I need to return it because it was the wrong size"}]

-- Test data
insert into calls (call_id, agent_id, audio_url, duration, transcript, analysis, csat_score, is_fcr, cust_sentiment)
values 
('call_001', 1, 'http://example.com/audio/call_001.mp3', 300,
'{"transcript": "Hello, how can I help you?"}',
'{"analysis": "positive"}', 5, true, 'Satisfaction'),
('call_002', 2, 'http://example.com/audio/call_002.mp3', 450,
'{"transcript": "I am not happy with the service."}',
'{"analysis": "negative"}', 2, false, 'Frustration'),
('call_003', 3, 'http://example.com/audio/call_003.mp3', 600,
'{"transcript": "Thank you for your help!"}',
'{"analysis": "positive"}', 4, true, 'Gratitude');


-- ----------------------------------------------------------------------------
-- Create table logs for call-specific internal messages (i.e. call is transcribed)
-- ----------------------------------------------------------------------------
CREATE TABLE logs (
    lid         bigserial PRIMARY KEY, -- unique ID for cross-reference
    cid         bigint DEFAULT 0,      -- call ID for cross-reference, 0 - call is not identified
    ltype       VARCHAR(10),           -- primary type 
    body        varchar,               -- log note / description
    level       smallint DEFAULT 1,    -- level of details 3 - debug; 2 - info; 1 - warning; 0 - error
    status      smallint DEFAULT 50,    -- alarm status: 20 - closed; 50 - new, 40 - known / normal. 
    created     timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP  -- when log was created
);


-- ----------------------------------------------------------------------------
-- Create procedure to delete old logs
-- ----------------------------------------------------------------------------
CREATE FUNCTION delete_old_logs() RETURNS trigger
    LANGUAGE plpgsql
    AS $$
DECLARE
  row_count int;
BEGIN
  DELETE FROM logs WHERE created < CURRENT_TIMESTAMP - INTERVAL '2 days';
  IF found THEN
    GET DIAGNOSTICS row_count = ROW_COUNT;
    RAISE NOTICE 'DELETEd % row(s) FROM logs', row_count;
  END IF;
  RETURN NULL;
END;
$$;


-- ----------------------------------------------------------------------------
-- Create a trigger to delete old logs
-- ----------------------------------------------------------------------------
CREATE TRIGGER trigger_delete_old_logs
    AFTER INSERT ON logs
    EXECUTE PROCEDURE delete_old_logs();


-- ----------------------------------------------------------------------------
-- Create table config for changabale configuration
-- ----------------------------------------------------------------------------
CREATE TABLE config (
    sid         bigserial PRIMARY KEY, -- unique ID for cross-reference
    parameter   VARCHAR(255) NOT NULL,  -- config parameter
    value       VARCHAR(255) NOT NULL,  -- config value
    description  VARCHAR,
    updated     bigint NOT NULL DEFAULT EXTRACT(EPOCH FROM current_timestamp)  -- when information has been updated (epoch)
);