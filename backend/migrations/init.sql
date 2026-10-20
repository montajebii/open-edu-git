-- OpenEdu Git - initial schema (must stay in sync with app/models/*)

CREATE EXTENSION IF NOT EXISTS "pg_trgm";

-- --------------------------------------------------------------------------
-- Users
-- --------------------------------------------------------------------------
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    full_name VARCHAR(255) NOT NULL,
    title VARCHAR(255),
    bio TEXT,
    avatar_url VARCHAR(255),
    is_active INTEGER DEFAULT 1,
    is_verified INTEGER DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- --------------------------------------------------------------------------
-- Email verification tokens
-- --------------------------------------------------------------------------
CREATE TABLE verification_tokens (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE NOT NULL,
    token VARCHAR(255) UNIQUE NOT NULL,
    purpose VARCHAR(50) NOT NULL,
    expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- --------------------------------------------------------------------------
-- Pamphlets
-- --------------------------------------------------------------------------
CREATE TABLE pamphlets (
    id SERIAL PRIMARY KEY,
    title VARCHAR(255) NOT NULL,
    author_id INTEGER REFERENCES users(id) ON DELETE CASCADE NOT NULL,
    grade VARCHAR(50) NOT NULL,
    subject VARCHAR(100) NOT NULL,
    chapter VARCHAR(100) NOT NULL,
    method VARCHAR(100),
    difficulty VARCHAR(50),
    is_public INTEGER DEFAULT 1,
    tags JSONB DEFAULT '[]',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE TABLE pamphlet_versions (
    id SERIAL PRIMARY KEY,
    pamphlet_id INTEGER REFERENCES pamphlets(id) ON DELETE CASCADE NOT NULL,
    version_number INTEGER NOT NULL,
    file_path VARCHAR(512) NOT NULL,
    file_type VARCHAR(50) NOT NULL,
    file_size INTEGER NOT NULL DEFAULT 0,
    notes TEXT,
    author_id INTEGER REFERENCES users(id) ON DELETE CASCADE NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- --------------------------------------------------------------------------
-- Reviews
-- --------------------------------------------------------------------------
CREATE TABLE reviews (
    id SERIAL PRIMARY KEY,
    pamphlet_id INTEGER REFERENCES pamphlets(id) ON DELETE CASCADE NOT NULL,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE NOT NULL,
    rating INTEGER NOT NULL CHECK (rating BETWEEN 1 AND 5),
    comment TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- --------------------------------------------------------------------------
-- Fork / merge-request workflow
-- --------------------------------------------------------------------------
CREATE TABLE pamphlet_forks (
    id SERIAL PRIMARY KEY,
    original_pamphlet_id INTEGER REFERENCES pamphlets(id) ON DELETE CASCADE NOT NULL,
    forked_by INTEGER REFERENCES users(id) ON DELETE CASCADE NOT NULL,
    new_pamphlet_id INTEGER REFERENCES pamphlets(id) ON DELETE CASCADE NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE TYPE merge_request_status AS ENUM ('pending', 'approved', 'rejected');

CREATE TABLE merge_requests (
    id SERIAL PRIMARY KEY,
    source_pamphlet_id INTEGER REFERENCES pamphlets(id) ON DELETE CASCADE NOT NULL,
    target_pamphlet_id INTEGER REFERENCES pamphlets(id) ON DELETE CASCADE NOT NULL,
    status merge_request_status NOT NULL DEFAULT 'pending',
    created_by INTEGER REFERENCES users(id) ON DELETE CASCADE NOT NULL,
    reviewed_by INTEGER REFERENCES users(id),
    title VARCHAR(255) NOT NULL,
    description TEXT,
    review_note TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    reviewed_at TIMESTAMP WITH TIME ZONE
);

-- --------------------------------------------------------------------------
-- Indexes
-- --------------------------------------------------------------------------
CREATE INDEX idx_pamphlets_author_id ON pamphlets(author_id);
CREATE INDEX idx_pamphlets_grade ON pamphlets(grade);
CREATE INDEX idx_pamphlets_subject ON pamphlets(subject);
CREATE INDEX idx_pamphlets_chapter ON pamphlets(chapter);
CREATE INDEX idx_pamphlets_is_public ON pamphlets(is_public);
CREATE INDEX idx_versions_pamphlet_id ON pamphlet_versions(pamphlet_id);
CREATE INDEX idx_reviews_pamphlet_id ON reviews(pamphlet_id);
CREATE INDEX idx_reviews_user_id ON reviews(user_id);
CREATE INDEX idx_merge_requests_target ON merge_requests(target_pamphlet_id);

-- --------------------------------------------------------------------------
-- Full-text search
-- NOTE: uses the 'simple' configuration, which ships with PostgreSQL. A
-- 'persian' configuration is not available by default and would make every
-- INSERT fail, so Persian stemming is deferred to a later migration.
-- --------------------------------------------------------------------------
ALTER TABLE pamphlets ADD COLUMN search_vector TSVECTOR;
CREATE INDEX idx_pamphlets_search_vector ON pamphlets USING GIN(search_vector);

CREATE OR REPLACE FUNCTION update_pamphlet_search_vector() RETURNS TRIGGER AS $$
BEGIN
    NEW.search_vector :=
        to_tsvector('simple', COALESCE(NEW.title, '')) ||
        to_tsvector('simple', COALESCE(NEW.grade, '')) ||
        to_tsvector('simple', COALESCE(NEW.subject, '')) ||
        to_tsvector('simple', COALESCE(NEW.chapter, '')) ||
        to_tsvector('simple', COALESCE(NEW.method, '')) ||
        to_tsvector('simple', COALESCE(NEW.difficulty, ''));
    RETURN NEW;
END
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_pamphlet_search_vector
BEFORE INSERT OR UPDATE ON pamphlets
FOR EACH ROW EXECUTE FUNCTION update_pamphlet_search_vector();
