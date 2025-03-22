CREATE DATABASE ccs_sitin_project;

USE ccs_sitin_project;

CREATE TABLE users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    idno VARCHAR(50) NOT NULL UNIQUE,
    lastname VARCHAR(50) NOT NULL,
    firstname VARCHAR(50) NOT NULL,
    midname VARCHAR(50) NOT NULL,
    course VARCHAR(50) NOT NULL,
    yearlevel VARCHAR(50) NOT NULL,
    email VARCHAR(100) NOT NULL UNIQUE,
    username VARCHAR(50) NOT NULL UNIQUE,
    password VARCHAR(100) NOT NULL
);

ALTER TABLE users 
ADD COLUMN photo_url VARCHAR(200);

ALTER TABLE users
MODIFY COLUMN midname VARCHAR(50) NULL;

-- add student_session column
ALTER TABLE users 
ADD COLUMN student_session INT;

-- update student_session column set to 30 if course is Bachelor of Science in Information Technology or Bachelor of Science Computer Science
-- otherwise set to 15
UPDATE users
SET student_session = CASE 
    WHEN course IN ('Bachelor of Science in Information Technology', 'Bachelor of Science Computer Science', 'BSIT', 'BSCS') THEN 30
    ELSE 15
END;

-- Create announcements table
CREATE TABLE announcements (
    id INT AUTO_INCREMENT PRIMARY KEY,
    title VARCHAR(200) NOT NULL,
    content TEXT NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    is_active BOOLEAN DEFAULT TRUE,
    priority INT DEFAULT 0
);

-- Sample announcement data
INSERT INTO announcements (title, content, priority) VALUES
('Lab Hours Update', 'Please note that the computer lab will be closed', 2);


SELECT * FROM users;
SELECT * FROM announcements;

DESCRIBE users;
DESCRIBE announcements;