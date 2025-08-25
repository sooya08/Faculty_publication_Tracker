-- Create the database
CREATE DATABASE IF NOT EXISTS faculty1;

-- Use the faculty database
USE faculty1;

-- Create the users table
CREATE TABLE IF NOT EXISTS users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(255) NOT NULL UNIQUE,
    email VARCHAR(255) DEFAULT NULL UNIQUE,
    password VARCHAR(255) NOT NULL,
    user_type ENUM('Faculty', 'Student') NOT NULL,
    approved TINYINT(1) DEFAULT 1, -- 1 for approved, 0 for pending (Faculty only)
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create the publications table
CREATE TABLE IF NOT EXISTS publications (
    pub_id INT AUTO_INCREMENT PRIMARY KEY,
    faculty_name VARCHAR(255) NOT NULL,
    department VARCHAR(255) NOT NULL,
    title TEXT NOT NULL,
    pub_type VARCHAR(100) NOT NULL,
    publisher VARCHAR(255) NOT NULL,
    publisher_email VARCHAR(255) NOT NULL,
    publication_year YEAR NOT NULL,
    doi_or_link TEXT,
    pdf_filename VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Clean up existing empty email records to prevent IntegrityError: Duplicate entry ''
UPDATE users SET email = NULL WHERE email = '';

-- Ensure email column allows NULL to prevent Error 1048: Column 'email' cannot be null
ALTER TABLE users MODIFY COLUMN email VARCHAR(255) DEFAULT NULL UNIQUE;

-- Optional: Insert a test admin user (replace with hashed password in production)
INSERT INTO users (username, email, password, user_type, approved) 
VALUES ('admin', 'admin@example.com', 'admin123', 'Admin', 1);

-- Verify the table structure
DESCRIBE users;
DESCRIBE publications;

-- Verify no empty email strings remain
SELECT email, COUNT(*) FROM users WHERE email = '' GROUP BY email;

-- Optional: Check for any duplicate emails (non-NULL)
SELECT email, COUNT(*) FROM users WHERE email IS NOT NULL GROUP BY email HAVING COUNT(*) > 1;
select * from users;