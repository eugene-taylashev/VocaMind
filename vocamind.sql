CREATE table calls (
    id bigserial PRIMARY KEY,
    call_id VARCHAR(20) not NULL, -- unique identifier for the call
    agent VARCHAR(255),
    audio_url VARCHAR,
    duration INT,
    transcript TEXT,
    analysis TEXT,
    satisfaction smallint,
    created_at bigint NOT NULL DEFAULT EXTRACT(EPOCH FROM current_timestamp),  -- when information has been updated (epoch),
    other json
);

-- Test data
insert into calls (call_id, agent, audio_url, duration, transcript, analysis, satisfaction, created_at, other)
values 
('call_001', 'agent_001', 'http://example.com/audio1.mp3', 120, 'Hello, how can I help you?', 'Positive', 5, 1690000000, '{"customer_id": "cust_001", "issue": "billing"}'),
('call_002', 'agent_002', 'http://example.com/audio2.mp3', 150, 'I need help with my order.', 'Neutral', 3, 1690000001, '{"customer_id": "cust_002", "issue": "order"}'),
('call_003', 'agent_003', 'http://example.com/audio3.mp3', 180, 'Thank you for your assistance.', 'Positive', 4, 1690000002, '{"customer_id": "cust_003", "issue": "technical"}');

CREATE TABLE logs (
    lid         bigserial PRIMARY KEY, -- unique ID for cross-reference
    ltype       VARCHAR(10),            -- primary type 
    body        varchar,           -- log note / description
    status      smallint DEFAULT 50,    -- alarm status: 20 - closed; 50 - new, 40 - known / normal. 
    updated     bigint NOT NULL DEFAULT EXTRACT(EPOCH FROM current_timestamp)  -- when information has been updated (epoch)
);
