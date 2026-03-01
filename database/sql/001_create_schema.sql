-- ============================================
-- COMPLETE DATABASE SCHEMA
-- Employee Onboarding Portal Project
-- ============================================

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ============================================
-- FUNCTION: update_updated_at_column
-- Auto-updates updated_at timestamp on row changes
-- ============================================
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- ============================================
-- TABLE: employees
-- ============================================
CREATE TABLE employees (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(255) NOT NULL UNIQUE,
    email VARCHAR(255),
    role VARCHAR(100),
    department VARCHAR(100),
    source VARCHAR(50),
    jira_account_id VARCHAR(255),
    github_username VARCHAR(255),
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_employees_name ON employees(name);
CREATE INDEX idx_employees_department ON employees(department);

CREATE TRIGGER update_employees_updated_at BEFORE UPDATE ON employees
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

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

CREATE TRIGGER update_git_commits_updated_at BEFORE UPDATE ON git_commits
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

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

CREATE TRIGGER update_meetings_updated_at BEFORE UPDATE ON meetings
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

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

CREATE TRIGGER update_jira_tickets_updated_at BEFORE UPDATE ON jira_tickets
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

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

CREATE TRIGGER update_confluence_pages_updated_at BEFORE UPDATE ON confluence_pages
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

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
-- TABLE: projects
-- ============================================
CREATE TABLE projects (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(255) NOT NULL,
    description TEXT,
    status VARCHAR(50) DEFAULT 'active',
    epic_key VARCHAR(50),
    jira_project_key VARCHAR(20),
    github_repo VARCHAR(255),
    confluence_space_key VARCHAR(50),
    start_date DATE,
    target_end_date DATE,
    actual_end_date DATE,
    owner VARCHAR(255),
    team_members TEXT,
    tags TEXT[],
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_projects_status ON projects(status);
CREATE INDEX idx_projects_epic_key ON projects(epic_key);
CREATE INDEX idx_projects_github_repo ON projects(github_repo);
CREATE INDEX idx_projects_tags ON projects USING GIN(tags);

CREATE TRIGGER update_projects_updated_at BEFORE UPDATE ON projects
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- ============================================
-- TABLE: project_entities
-- ============================================
CREATE TABLE project_entities (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    project_id UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    entity_type VARCHAR(50) NOT NULL,
    entity_id UUID NOT NULL,
    added_manually BOOLEAN DEFAULT false,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(project_id, entity_type, entity_id)
);

CREATE INDEX idx_project_entities_project ON project_entities(project_id);
CREATE INDEX idx_project_entities_entity ON project_entities(entity_type, entity_id);

-- ============================================
-- TABLE: sprints
-- ============================================
CREATE TABLE sprints (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    sprint_number INTEGER NOT NULL,
    name VARCHAR(255) NOT NULL,
    start_date DATE NOT NULL,
    end_date DATE NOT NULL,
    goal TEXT,
    project_id UUID REFERENCES projects(id) ON DELETE CASCADE,
    status VARCHAR(50) DEFAULT 'planned',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_sprints_project ON sprints(project_id);
CREATE INDEX idx_sprints_status ON sprints(status);
CREATE INDEX idx_sprints_start_date ON sprints(start_date);

CREATE TRIGGER update_sprints_updated_at BEFORE UPDATE ON sprints
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- ============================================
-- TABLE: sprint_tickets
-- ============================================
CREATE TABLE sprint_tickets (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    sprint_id UUID NOT NULL REFERENCES sprints(id) ON DELETE CASCADE,
    ticket_id UUID NOT NULL REFERENCES jira_tickets(id) ON DELETE CASCADE,
    added_date DATE DEFAULT CURRENT_DATE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(sprint_id, ticket_id)
);

CREATE INDEX idx_sprint_tickets_sprint ON sprint_tickets(sprint_id);
CREATE INDEX idx_sprint_tickets_ticket ON sprint_tickets(ticket_id);

-- ============================================
-- VIEW: unified_timeline
-- ============================================
CREATE VIEW unified_timeline AS
SELECT 'commit' as entity_type, id as entity_id, commit_date as event_date, message as title, author_name as actor, related_tickets as context FROM git_commits
UNION ALL
SELECT 'meeting', id, meeting_date, title, NULL, participants FROM meetings
UNION ALL
SELECT 'jira_ticket', id, created_date, summary, assignee, issue_key FROM jira_tickets
UNION ALL
SELECT 'confluence', id, page_created_date, title, author, space FROM confluence_pages
ORDER BY event_date DESC;

-- ============================================
-- VERIFY SETUP
-- ============================================
-- Run: \dt to list all tables
-- Run: \dv to list all views