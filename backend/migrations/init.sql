-- Create extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";

-- Create users table
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

-- Create pamphlets table
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

-- Create pamphlet_versions table
CREATE TABLE pamphlet_versions (
    id SERIAL PRIMARY KEY,
    pamphlet_id INTEGER REFERENCES pamphlets(id) ON DELETE CASCADE NOT NULL,
    version_number INTEGER NOT NULL,
    file_path VARCHAR(512) NOT NULL,
    file_type VARCHAR(50) NOT NULL,
    created_by INTEGER REFERENCES users(id) ON DELETE CASCADE NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create reviews table
CREATE TABLE reviews (
    id SERIAL PRIMARY KEY,
    pamphlet_id INTEGER REFERENCES pamphlets(id) ON DELETE CASCADE NOT NULL,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE NOT NULL,
    rating INTEGER NOT NULL,
    comment TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create indexes for performance
CREATE INDEX idx_pamphlets_author_id ON pamphlets(author_id);
CREATE INDEX idx_pamphlets_grade ON pamphlets(grade);
CREATE INDEX idx_pamphlets_subject ON pamphlets(subject);
CREATE INDEX idx_pamphlets_chapter ON pamphlets(chapter);
CREATE INDEX idx_pamphlets_is_public ON pamphlets(is_public);
CREATE INDEX idx_reviews_pamphlet_id ON reviews(pamphlet_id);
CREATE INDEX idx_reviews_user_id ON reviews(user_id);

-- Enable full-text search on pamphlets
ALTER TABLE pamphlets ADD COLUMN search_vector TSVECTOR;
CREATE INDEX idx_pamphlets_search_vector ON pamphlets USING GIN(search_vector);

-- Trigger to update search_vector on insert/update
CREATE OR REPLACE FUNCTION update_pamphlet_search_vector() RETURNS TRIGGER AS $$
BEGIN
    NEW.search_vector := 
        to_tsvector('persian', COALESCE(NEW.title, '')) ||
        to_tsvector('persian', COALESCE(NEW.grade, '')) ||
        to_tsvector('persian', COALESCE(NEW.subject, '')) ||
        to_tsvector('persian', COALESCE(NEW.chapter, '')) ||
        to_tsvector('persian', COALESCE(NEW.method, '')) ||
        to_tsvector('persian', COALESCE(NEW.difficulty, ''));
    RETURN NEW;
END
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_pamphlet_search_vector
BEFORE INSERT OR UPDATE ON pamphlets
FOR EACH ROW EXECUTE FUNCTION update_pamphlet_search_vector();