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

INSERT INTO `user` (id, student_id, username, email, password_hash, created_at, is_active, last_login) VALUES
(1, '242FC242F0', 'Chee Wei Keong', 'CHEE.WEI.KEONG@student.mmu.edu.my', 'scrypt:32768:8:1$eWVc2XfDS5QKFnbK$14ed19407952...', '2025-05-14 16:03:55.800915', 1, '2025-05-15 06:01:44.176615'),
(2, 'test1234', 'Chee Wei Keong test', 'xiaohuangren0000@gmail.com', 'scrypt:32768:8:1$FgnHPExIFK3PLngq$4d070994316e...', '2025-05-14 16:40:11.684294', 1, '2025-05-14 18:21:32.217285'),
(3, '0123456789AB', 'Ong Jun Ze', 'ongjunze@gmail.com', 'scrypt:32768:8:1$i2xHvuugfIBZPJIt$cc311fd48402...', '2025-05-15 05:57:15.402551', 1, '2025-05-15 05:57:48.442740');

INSERT INTO customisation (id, user_id, profile_picture, bio, interests, faculty, course, year_of_study, created_at, updated_at) VALUES
(1, 1, 'RobloxScreenShot20250512_213812508.png', 'Testing Bio', 'Programming,PC Gaming,Mobile Gaming', 'Faculty of Computing & Informatics', 'Foundation in IT', 1, '2025-05-14 16:03:55.803320', '2025-05-14 18:20:53.741598'),
(2, 2, 'RobloxScreenShot20250318_180201598.png', 'Testing Account', 'None,Programming,Night Owl,Weekday Study,Badminton', 'Faculty of Computing & Informatics', 'Foundation in IT', 1, '2025-05-14 16:40:11.686440', '2025-05-14 16:41:49.100516'),
(3, 3, 'smiley.png.png', 'See you later', 'None,Programming,Data Science,Solo Study,Library', 'Faculty of Computing & Informatics', 'Data Science', 1, '2025-05-15 05:57:15.421785', '2025-05-15 05:59:08.934905');

INSERT INTO connection (id, user_id, connected_user_id, status, created_at, updated_at) VALUES
(1, 1, 2, 'accepted', '2025-05-14 16:58:48.168996', '2025-05-14 17:09:17.553442');

INSERT INTO message (id, connection_id, sender_id, content, is_read, created_at) VALUES
(1, 1, 2, 'hello', 1, '2025-05-14 17:13:47.356585'),
(2, 1, 1, 'hi', 1, '2025-05-14 17:14:30.394323'),
(3, 1, 1, 'hello', 1, '2025-05-14 18:21:15.238091'),
(4, 1, 2, 'halo', 0, '2025-05-14 18:21:56.994769');

SELECT * FROM `user`;

