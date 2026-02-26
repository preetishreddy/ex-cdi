-- Onboarding_AI Database Schema
-- Version: 1.0
-- Description: Schema for storing git commits, meeting transcripts, Jira tickets, and Confluence pages

-- Enable UUID extension for generating unique IDs
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ============================================
-- TABLE: git_commits
-- ============================================
CREATE TABLE git_commits (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    sha VARCHAR(40) NOT NULL UNIQUE,
    author_name VARCHAR(255) NOT NULL,
    author_email VARCHAR(255) NOT NULL,
    commit_date TIMESTAMP WITH TIME ZONE NOT NULL,
    message TEXT NOT NULL,
    related_tickets TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_git_commits_author_email ON git_commits(author_email);
CREATE INDEX idx_git_commits_commit_date ON git_commits(commit_date);

-- ============================================
-- TABLE: git_commit_files
-- ============================================
CREATE TABLE git_commit_files (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    commit_id UUID NOT NULL REFERENCES git_commits(id) ON DELETE CASCADE,
    filename VARCHAR(500) NOT NULL,
    additions INTEGER DEFAULT 0,
    deletions INTEGER DEFAULT 0,
    status VARCHAR(50) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_git_commit_files_commit_id ON git_commit_files(commit_id);
CREATE INDEX idx_git_commit_files_filename ON git_commit_files(filename);

-- ============================================
-- TABLE: meetings
-- ============================================
CREATE TABLE meetings (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    title VARCHAR(500),
    meeting_date TIMESTAMP WITH TIME ZONE,
    raw_vtt_content TEXT NOT NULL,
    summary TEXT,
    key_decisions TEXT,
    action_items TEXT,
    participants TEXT,
    duration_seconds INTEGER,
    source_filename VARCHAR(255),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_meetings_meeting_date ON meetings(meeting_date);

-- ============================================
-- TABLE: jira_tickets
-- ============================================
CREATE TABLE jira_tickets (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    issue_key VARCHAR(50) NOT NULL UNIQUE,
    issue_type VARCHAR(50) NOT NULL,
    summary VARCHAR(500) NOT NULL,
    description TEXT,
    status VARCHAR(50) NOT NULL,
    priority VARCHAR(50),
    assignee VARCHAR(255),
    reporter VARCHAR(255),
    created_date TIMESTAMP WITH TIME ZONE,
    updated_date TIMESTAMP WITH TIME ZONE,
    resolved_date TIMESTAMP WITH TIME ZONE,
    labels TEXT,
    epic_link VARCHAR(50),
    sprint VARCHAR(100),
    story_points INTEGER,
    comments TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_jira_tickets_issue_key ON jira_tickets(issue_key);
CREATE INDEX idx_jira_tickets_status ON jira_tickets(status);
CREATE INDEX idx_jira_tickets_assignee ON jira_tickets(assignee);
CREATE INDEX idx_jira_tickets_epic_link ON jira_tickets(epic_link);
CREATE INDEX idx_jira_tickets_created_date ON jira_tickets(created_date);

-- ============================================
-- TABLE: confluence_pages
-- ============================================
CREATE TABLE confluence_pages (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    title VARCHAR(500) NOT NULL,
    space VARCHAR(255),
    author VARCHAR(255),
    content TEXT NOT NULL,
    labels TEXT[],
    version INTEGER DEFAULT 1,
    page_created_date TIMESTAMP WITH TIME ZONE,
    page_updated_date TIMESTAMP WITH TIME ZONE,
    source_filename VARCHAR(255),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_confluence_pages_space ON confluence_pages(space);
CREATE INDEX idx_confluence_pages_author ON confluence_pages(author);
CREATE INDEX idx_confluence_pages_labels ON confluence_pages USING GIN(labels);

-- ============================================
-- TABLE: entity_references
-- ============================================
CREATE TABLE entity_references (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    source_type VARCHAR(50) NOT NULL,
    source_id UUID NOT NULL,
    reference_type VARCHAR(50) NOT NULL,
    reference_id VARCHAR(100) NOT NULL,
    extraction_method VARCHAR(50),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(source_type, source_id, reference_type, reference_id)
);

CREATE INDEX idx_entity_references_source ON entity_references(source_type, source_id);
CREATE INDEX idx_entity_references_reference ON entity_references(reference_type, reference_id);

-- ============================================
-- VIEW: unified_timeline
-- ============================================
CREATE VIEW unified_timeline AS
SELECT 
    'commit' as entity_type,
    id as entity_id,
    commit_date as event_date,
    message as title,
    author_name as actor,
    related_tickets as context
FROM git_commits
UNION ALL
SELECT 
    'meeting' as entity_type,
    id as entity_id,
    meeting_date as event_date,
    title,
    NULL as actor,
    participants as context
FROM meetings
UNION ALL
SELECT 
    'jira_ticket' as entity_type,
    id as entity_id,
    created_date as event_date,
    summary as title,
    assignee as actor,
    issue_key as context
FROM jira_tickets
UNION ALL
SELECT 
    'confluence' as entity_type,
    id as entity_id,
    page_created_date as event_date,
    title,
    author as actor,
    space as context
FROM confluence_pages
ORDER BY event_date DESC;

-- ============================================
-- FUNCTION: Update timestamp trigger
-- ============================================
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_git_commits_updated_at BEFORE UPDATE ON git_commits
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_meetings_updated_at BEFORE UPDATE ON meetings
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_jira_tickets_updated_at BEFORE UPDATE ON jira_tickets
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_confluence_pages_updated_at BEFORE UPDATE ON confluence_pages
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();