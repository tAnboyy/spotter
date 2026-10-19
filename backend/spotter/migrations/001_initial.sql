CREATE TABLE IF NOT EXISTS sessions (id TEXT PRIMARY KEY, token_hash TEXT NOT NULL, state TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS events (session_id TEXT NOT NULL, event_id TEXT NOT NULL, request TEXT NOT NULL, result TEXT NOT NULL, PRIMARY KEY(session_id,event_id));
CREATE TABLE IF NOT EXISTS users (
    id TEXT PRIMARY KEY,
    google_sub TEXT NOT NULL UNIQUE,
    email TEXT,
    name TEXT NOT NULL,
    token_hash TEXT NOT NULL,
    preferences TEXT NOT NULL,
    muscle_group_ids TEXT NOT NULL,
    plan TEXT
);
CREATE TABLE IF NOT EXISTS user_schedules (user_id TEXT PRIMARY KEY, schedule TEXT NOT NULL);
