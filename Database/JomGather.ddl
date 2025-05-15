-- Active: 1746064849072@@127.0.0.1@3306@jomgather
CREATE DATABASE IF NOT EXISTS JomGather;

SHOW TABLES;

CREATE TABLE `user` (
  id INT AUTO_INCREMENT PRIMARY KEY,
  student_id VARCHAR(15) NOT NULL,
  username VARCHAR(64) NOT NULL,
  email VARCHAR(120) NOT NULL,
  password_hash VARCHAR(128),
  created_at DATETIME,
  is_active BOOLEAN,
  last_login DATETIME
);

CREATE TABLE customisation (
  id INT AUTO_INCREMENT PRIMARY KEY,
  user_id INT NOT NULL,
  profile_picture VARCHAR(255),
  bio TEXT,
  interests VARCHAR(500),
  faculty VARCHAR(100),
  course VARCHAR(100),
  year_of_study INT,
  created_at DATETIME,
  updated_at DATETIME
);

CREATE TABLE connection (
  id INT AUTO_INCREMENT PRIMARY KEY,
  user_id INT NOT NULL,
  connected_user_id INT NOT NULL,
  status VARCHAR(20),
  created_at DATETIME,
  updated_at DATETIME
);


CREATE TABLE message (
  id INT AUTO_INCREMENT PRIMARY KEY,
  connection_id INT NOT NULL,
  sender_id INT NOT NULL,
  content TEXT NOT NULL,
  is_read BOOLEAN,
  created_at DATETIME
);
