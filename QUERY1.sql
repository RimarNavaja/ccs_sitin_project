-- Active: 1738563940771@@127.0.0.1@3306@ccs_sitin_project
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

--alter talbe users, change midname column to allow null values
-- This is to allow users to not have a middle name
ALTER TABLE users
MODIFY COLUMN midname VARCHAR(50) NULL;

-- Add lab_points column for rewards system
ALTER TABLE users ADD COLUMN lab_points INT DEFAULT 0;

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

-- Create sit_in_sessions table
CREATE TABLE sit_in_sessions (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    purpose VARCHAR(100) NOT NULL,
    lab VARCHAR(10),
    notes TEXT,
    start_time DATETIME DEFAULT CURRENT_TIMESTAMP,
    end_time DATETIME,
    status VARCHAR(20) DEFAULT 'active',
    FOREIGN KEY (user_id) REFERENCES users(id)
);

-- Make sure computer_number column is removed from sit_in_sessions table
ALTER TABLE sit_in_sessions DROP COLUMN IF EXISTS computer_number;

-- Add missing lab column to sit_in_sessions table
ALTER TABLE sit_in_sessions 
ADD COLUMN lab VARCHAR(10) AFTER purpose;

-- Sample announcement data
INSERT INTO announcements (title, content, priority) VALUES
('Lab Hours Update', 'Please note that the computer lab will be closed', 2);

SELECT * FROM users;
SELECT * FROM announcements;
SELECT * FROM sit_in_sessions;

SELECT * FROM feedback;

DESCRIBE users;
DESCRIBE announcements;

DESCRIBE sit_in_sessions;

-- Create computer_status table to track individual PC states
CREATE TABLE computer_status (
    id INT AUTO_INCREMENT PRIMARY KEY,
    lab_name VARCHAR(50) NOT NULL,
    pc_number INT NOT NULL,
    status VARCHAR(20) DEFAULT 'available' NOT NULL, -- 'available', 'used', 'maintenance'
    current_session_id INT NULL, -- Link to the sit_in_sessions if 'used'
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    UNIQUE KEY unique_lab_pc (lab_name, pc_number),
    FOREIGN KEY (current_session_id) REFERENCES sit_in_sessions(id) ON DELETE SET NULL
);

DESCRIBE computer_status;

-- Populate the computer_status table for labs 517, 524, 526, 528, 530, 542, 544 with 50 PCs each
INSERT INTO computer_status (lab_name, pc_number)
VALUES
('517', 1), ('517', 2), ('517', 3), ('517', 4), ('517', 5), ('517', 6), ('517', 7), ('517', 8), ('517', 9), ('517', 10),
('517', 11), ('517', 12), ('517', 13), ('517', 14), ('517', 15), ('517', 16), ('517', 17), ('517', 18), ('517', 19), ('517', 20),
('517', 21), ('517', 22), ('517', 23), ('517', 24), ('517', 25), ('517', 26), ('517', 27), ('517', 28), ('517', 29), ('517', 30),
('517', 31), ('517', 32), ('517', 33), ('517', 34), ('517', 35), ('517', 36), ('517', 37), ('517', 38), ('517', 39), ('517', 40),
('517', 41), ('517', 42), ('517', 43), ('517', 44), ('517', 45), ('517', 46), ('517', 47), ('517', 48), ('517', 49), ('517', 50),
('524', 1), ('524', 2), ('524', 3), ('524', 4), ('524', 5), ('524', 6), ('524', 7), ('524', 8), ('524', 9), ('524', 10),
('524', 11), ('524', 12), ('524', 13), ('524', 14), ('524', 15), ('524', 16), ('524', 17), ('524', 18), ('524', 19), ('524', 20),
('524', 21), ('524', 22), ('524', 23), ('524', 24), ('524', 25), ('524', 26), ('524', 27), ('524', 28), ('524', 29), ('524', 30),
('524', 31), ('524', 32), ('524', 33), ('524', 34), ('524', 35), ('524', 36), ('524', 37), ('524', 38), ('524', 39), ('524', 40),
('524', 41), ('524', 42), ('524', 43), ('524', 44), ('524', 45), ('524', 46), ('524', 47), ('524', 48), ('524', 49), ('524', 50),
('526', 1), ('526', 2), ('526', 3), ('526', 4), ('526', 5), ('526', 6), ('526', 7), ('526', 8), ('526', 9), ('526', 10),
('526', 11), ('526', 12), ('526', 13), ('526', 14), ('526', 15), ('526', 16), ('526', 17), ('526', 18), ('526', 19), ('526', 20),
('526', 21), ('526', 22), ('526', 23), ('526', 24), ('526', 25), ('526', 26), ('526', 27), ('526', 28), ('526', 29), ('526', 30),
('526', 31), ('526', 32), ('526', 33), ('526', 34), ('526', 35), ('526', 36), ('526', 37), ('526', 38), ('526', 39), ('526', 40),
('526', 41), ('526', 42), ('526', 43), ('526', 44), ('526', 45), ('526', 46), ('526', 47), ('526', 48), ('526', 49), ('526', 50),
('528', 1), ('528', 2), ('528', 3), ('528', 4), ('528', 5), ('528', 6), ('528', 7), ('528', 8), ('528', 9), ('528', 10),
('528', 11), ('528', 12), ('528', 13), ('528', 14), ('528', 15), ('528', 16), ('528', 17), ('528', 18), ('528', 19), ('528', 20),
('528', 21), ('528', 22), ('528', 23), ('528', 24), ('528', 25), ('528', 26), ('528', 27), ('528', 28), ('528', 29), ('528', 30),
('528', 31), ('528', 32), ('528', 33), ('528', 34), ('528', 35), ('528', 36), ('528', 37), ('528', 38), ('528', 39), ('528', 40),
('528', 41), ('528', 42), ('528', 43), ('528', 44), ('528', 45), ('528', 46), ('528', 47), ('528', 48), ('528', 49), ('528', 50),
('530', 1), ('530', 2), ('530', 3), ('530', 4), ('530', 5), ('530', 6), ('530', 7), ('530', 8), ('530', 9), ('530', 10),
('530', 11), ('530', 12), ('530', 13), ('530', 14), ('530', 15), ('530', 16), ('530', 17), ('530', 18), ('530', 19), ('530', 20),
('530', 21), ('530', 22), ('530', 23), ('530', 24), ('530', 25), ('530', 26), ('530', 27), ('530', 28), ('530', 29), ('530', 30),
('530', 31), ('530', 32), ('530', 33), ('530', 34), ('530', 35), ('530', 36), ('530', 37), ('530', 38), ('530', 39), ('530', 40),
('530', 41), ('530', 42), ('530', 43), ('530', 44), ('530', 45), ('530', 46), ('530', 47), ('530', 48), ('530', 49), ('530', 50),
('542', 1), ('542', 2), ('542', 3), ('542', 4), ('542', 5), ('542', 6), ('542', 7), ('542', 8), ('542', 9), ('542', 10),
('542', 11), ('542', 12), ('542', 13), ('542', 14), ('542', 15), ('542', 16), ('542', 17), ('542', 18), ('542', 19), ('542', 20),
('542', 21), ('542', 22), ('542', 23), ('542', 24), ('542', 25), ('542', 26), ('542', 27), ('542', 28), ('542', 29), ('542', 30),
('542', 31), ('542', 32), ('542', 33), ('542', 34), ('542', 35), ('542', 36), ('542', 37), ('542', 38), ('542', 39), ('542', 40),
('542', 41), ('542', 42), ('542', 43), ('542', 44), ('542', 45), ('542', 46), ('542', 47), ('542', 48), ('542', 49), ('542', 50),
('544', 1), ('544', 2), ('544', 3), ('544', 4), ('544', 5), ('544', 6), ('544', 7), ('544', 8), ('544', 9), ('544', 10),
('544', 11), ('544', 12), ('544', 13), ('544', 14), ('544', 15), ('544', 16), ('544', 17), ('544', 18), ('544', 19), ('544', 20),
('544', 21), ('544', 22), ('544', 23), ('544', 24), ('544', 25), ('544', 26), ('544', 27), ('544', 28), ('544', 29), ('544', 30),
('544', 31), ('544', 32), ('544', 33), ('544', 34), ('544', 35), ('544', 36), ('544', 37), ('544', 38), ('544', 39), ('544', 40),
('544', 41), ('544', 42), ('544', 43), ('544', 44), ('544', 45), ('544', 46), ('544', 47), ('544', 48), ('544', 49), ('544', 50);

SELECT * FROM computer_status