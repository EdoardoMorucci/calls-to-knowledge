-- Eseguire nel Supabase SQL Editor (https://supabase.com/dashboard/project/<id>/sql)

CREATE TABLE projects (
    id bigserial PRIMARY KEY,
    name text NOT NULL,
    description text,
    created_at timestamptz DEFAULT now()
);

CREATE TABLE calls (
    id bigserial PRIMARY KEY,
    project_id bigint REFERENCES projects(id) ON DELETE SET NULL,
    title text,
    source_app text NOT NULL,
    started_at timestamptz NOT NULL DEFAULT now(),
    ended_at timestamptz,
    duration_sec integer,
    audio_path text,
    status text NOT NULL DEFAULT 'recording',
    participants jsonb DEFAULT '[]',
    recording_trigger text NOT NULL DEFAULT 'auto',
    updated_at timestamptz DEFAULT now()
);

CREATE TABLE transcripts (
    id bigserial PRIMARY KEY,
    call_id bigint NOT NULL REFERENCES calls(id) ON DELETE CASCADE,
    full_text text NOT NULL,
    segments jsonb DEFAULT '[]',
    language text,
    created_at timestamptz DEFAULT now()
);

CREATE TABLE summaries (
    id bigserial PRIMARY KEY,
    call_id bigint NOT NULL REFERENCES calls(id) ON DELETE CASCADE,
    summary text,
    key_points jsonb DEFAULT '[]',
    next_steps jsonb DEFAULT '[]',
    decisions jsonb DEFAULT '[]',
    created_at timestamptz DEFAULT now()
);

-- Disabilita RLS (accesso solo dal backend con service_role_key)
ALTER TABLE projects DISABLE ROW LEVEL SECURITY;
ALTER TABLE calls DISABLE ROW LEVEL SECURITY;
ALTER TABLE transcripts DISABLE ROW LEVEL SECURITY;
ALTER TABLE summaries DISABLE ROW LEVEL SECURITY;
