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



SELECT * FROM users;

