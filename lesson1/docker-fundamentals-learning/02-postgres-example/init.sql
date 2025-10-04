-- Sample database initialization script
-- This file demonstrates how to initialize a database on first run

CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS posts (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    title VARCHAR(200) NOT NULL,
    content TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Insert sample data
INSERT INTO users (username, email) VALUES
    ('john_doe', 'john@example.com'),
    ('jane_smith', 'jane@example.com')
ON CONFLICT DO NOTHING;

INSERT INTO posts (user_id, title, content) VALUES
    (1, 'First Post', 'Hello from Docker!'),
    (2, 'Learning Docker', 'Containers are amazing!')
ON CONFLICT DO NOTHING;
