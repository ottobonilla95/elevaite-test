CREATE TABLE IF NOT EXISTS chat_data_final (
    qid UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id UUID,
    sr_ticket_id VARCHAR(255),
    request TEXT,
    request_timestamp TIMESTAMP,
    response TEXT,
    user_id VARCHAR(255),
    response_timestamp TIMESTAMP,
    vote INTEGER DEFAULT 0, -- 1=thumbs up, -1=thumbs down, 0=no vote
    vote_timestamp TIMESTAMP,
    feedback TEXT DEFAULT '',
    feedback_timestamp TIMESTAMP,
    agent_flow_id UUID,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS agent_flow_data (
    agent_flow_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    session_id UUID,
    qid UUID,
    user_id VARCHAR(255),
    request TEXT,
    response TEXT,
    created_at TIMESTAMP DEFAULT NOW(),
    tries INTEGER DEFAULT 0,
    tool_calls TEXT,
    chat_history TEXT
);

CREATE INDEX IF NOT EXISTS idx_chat_data_session_id ON chat_data_final(session_id);
CREATE INDEX IF NOT EXISTS idx_chat_data_timestamp ON chat_data_final(request_timestamp);
CREATE INDEX IF NOT EXISTS idx_chat_data_user_id ON chat_data_final(user_id);
CREATE INDEX IF NOT EXISTS idx_chat_data_vote ON chat_data_final(vote);

COMMENT ON TABLE chat_data_final IS 'Chatbot conversation data for query analytics';
COMMENT ON TABLE agent_flow_data IS 'Agent flow data for chatbot interactions';