CREATE DATABASE IF NOT EXISTS JomGather;

DROP TABLE interest;

CREATE TABLE interest (
    id INT
    AUTO_INCREMENT PRIMARY KEY,
    interest VARCHAR(80), category VARCHAR(100)
);

INSERT INTO interest (id, interest, category) VALUES
    ('001', 'Programming', 'Academic Interests'),
    ('002', 'Data Science', 'Academic Interests'),
    ('003', 'Artificial Intelligence', 'Academic Interests'),
    ('004', 'Cybersecurity', 'Academic Interests'),
    ('005', 'Engineering', 'Academic Interests'),
    ('006', 'Business', 'Academic Interests'),
    ('007', 'Marketing', 'Academic Interests'),
    ('008', 'Finance', 'Academic Interests'),
    ('009', 'Animation', 'Academic Interests'),
    ('010', 'Game Development', 'Academic Interests'),
    ('011', 'Mass Communication', 'Academic Interests'),
    
    ('012', 'Group Study', 'Study Preferences'),
    ('013', 'Solo Study', 'Study Preferences'),
    ('014', 'Library', 'Study Preferences'),
    ('015', 'Learning Point', 'Study Preferences'),
    ('016', 'Early Bird', 'Study Preferences'),
    ('017', 'Night Owl', 'Study Preferences'),
    ('018', 'Weekend Study', 'Study Preferences'),
    ('019', 'Weekday Study', 'Study Preferences'),

    ('020', 'Basketball', 'Sports & Fitness'),
    ('021', 'Football', 'Sports & Fitness'),
    ('022', 'Badminton', 'Sports & Fitness'),
    ('023', 'Tennis', 'Sports & Fitness'),
    ('024', 'Swimming', 'Sports & Fitness'),
    ('025', 'Volleyball', 'Sports & Fitness'),
    ('026', 'Table Tennis', 'Sports & Fitness'),
    ('027', 'Martial Arts', 'Sports & Fitness'),
    ('028', 'Yoga', 'Sports & Fitness'),
    ('029', 'Gym', 'Sports & Fitness'),

    ('030', 'Photography', 'Arts & Entertainment'),
    ('031', 'Content Creation', 'Arts & Entertainment'),
    ('032', 'Music', 'Arts & Entertainment'),
    ('033', 'Singing', 'Arts & Entertainment'),
    ('034', 'Dancing', 'Arts & Entertainment'),
    ('035', 'Painting', 'Arts & Entertainment'),
    ('036', 'Drawing', 'Arts & Entertainment'),
    ('037', 'Acting', 'Arts & Entertainment'),
    ('038', 'Theater', 'Arts & Entertainment'),
    ('039', 'Video Editing', 'Arts & Entertainment'),
    ('040', 'Playing Instruments', 'Arts & Entertainment'),

    ('041', 'Reading', 'Other Hobbies'),
    ('042', 'Writing', 'Other Hobbies'),
    ('043', 'PC Gaming', 'Other Hobbies'),
    ('044', 'Mobile Gaming', 'Other Hobbies'),
    ('045', 'Console Gaming', 'Other Hobbies'),
    ('046', 'AR/VR Gaming', 'Other Hobbies'),
    ('047', 'Cooking', 'Other Hobbies'),
    ('048', 'Baking', 'Other Hobbies'),
    ('049', 'Travel', 'Other Hobbies'),
    ('050', 'Hiking', 'Other Hobbies'),
    ('051', 'Board Games', 'Other Hobbies'),
    ('052', 'Anime', 'Other Hobbies'),
    ('053', 'Movies', 'Other Hobbies'),
    ('054', 'Series', 'Other Hobbies'),

    ('055', 'Volunteering', 'Social Activities'),
    ('056', 'Event Planning', 'Social Activities'),
    ('057', 'Public Speaking', 'Social Activities'),
    ('058', 'Leadership', 'Social Activities'),
    ('059', 'Entrepreneurship', 'Social Activities'),
    ('060', 'Student Clubs', 'Social Activities');

    SELECT * FROM interest;

    CREATE TABLE faculty (
        id INT
        AUTO_INCREMENT PRIMARY KEY,
        faculty VARCHAR(100), programe VARCHAR(100) UNIQUE
    );

SELECT * FROM faculty;

INSERT INTO faculty (id, faculty, programe) VALUES
    ('01', 'Faculty of Computing and Informatics', 'Software Engineering'),
    ('02', 'Faculty of Computing and Informatics', 'Cybersecurity'),
    ('03', 'Faculty of Computing and Informatics', 'Game Development'),
    ('04', 'Faculty of Computing and Informatics', 'Data Science'),
    ('05', 'Faculty of Computing and Informatics', 'Artificial Intelligence'),
    
    ('06', 'Faculty of Engineering', 'Business Management'),

    ('07', 'Faculty of Applied Communication', 'Strategic Communication'),

    ('08', 'Faculty of Management', 'Finance'),
    ('09', 'Faculty of Management', 'Business Administration'),
    ('10', 'Faculty of Management', 'Accounting'),
    ('11', 'Faculty of Management', 'Marketing'),
    ('12', 'Faculty of Management', 'Digital Analytics'),
    ('13', 'Faculty of Management', 'Law'),

    ('14', 'Faculty of Creative Multimedia', 'Animation'),
    ('15', 'Faculty of Creative Multimedia', 'Immersive Media Design'),
    ('16', 'Faculty of Creative Multimedia', 'Advertising Design'),
    ('17', 'Faculty of Creative Multimedia', 'Visual Effects'),

    ('18', 'Faculty of Cinematic Arts', 'Cinematography');

    DROP TABLE IF EXISTS TBC;

    CREATE TABLE TBC (
        id INT
        AUTO_INCREMENT PRIMARY KEY,
        purpose VARCHAR(100), interest_category VARCHAR(100)
    );

SELECT * FROM TBC;

    INSERT INTO TBC (purpose, interest_category) VALUES
    ('Study Partners', 'Academic'),
    ('Project Collaboration', 'Academic'),
    ('Hobby & Recreation', 'Academic'),
    ('Sports & Fitness', 'Academic'),
    ('Events & Activities', 'Academic'),

    ('Study Partners', 'Study Preferences'),
    ('Project Collaboration', 'Study Preferences'),
    ('Hobby & Recreation', 'Study Preferences'),
    ('Sports & Fitness', 'Study Preferences'),
    ('Events & Activities', 'Study Preferences'),

    ('Study Partners', 'Sports & Fitness'),
    ('Project Collaboration', 'Sports & Fitness'),
    ('Hobby & Recreation', 'Sports & Fitness'),
    ('Sports & Fitness', 'Sports & Fitness'),
    ('Events & Activities', 'Sports & Fitness'),

    ('Study Partners', 'Arts & Entertainment'),
    ('Project Collaboration', 'Arts & Entertainment'),
    ('Hobby & Recreation', 'Arts & Entertainment'),
    ('Sports & Fitness', 'Arts & Entertainment'),
    ('Events & Activities', 'Arts & Entertainment'),

    ('Study Partners', 'Social Activities'),
    ('Project Collaboration', 'Social Activities'),
    ('Hobby & Recreation', 'Social Activities'),
    ('Sports & Fitness', 'Social Activities'),
    ('Events & Activities', 'Social Activities'),

    ('Study Partners', 'Other Hobbies'),
    ('Project Collaboration', 'Other Hobbies'),
    ('Hobby & Recreation', 'Other Hobbies'),
    ('Sports & Fitness', 'Other Hobbies'),
    ('Events & Activities', 'Other Hobbies');

CREATE TABLE user (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) DEFAULT NULL,
    email VARCHAR(100) UNIQUE DEFAULT NULL,
    password VARCHAR(100) DEFAULT NULL,
    faculty_id INT DEFAULT NULL,
    interest_id INT DEFAULT NULL,
    tbc_id INT DEFAULT NULL,
    FOREIGN KEY (faculty_id) REFERENCES faculty(id),
    FOREIGN KEY (interest_id) REFERENCES interest(id),
    FOREIGN KEY (tbc_id) REFERENCES TBC(id)
);

ALTER TABLE user ADD `Student_ID` VARCHAR(10) AFTER name;
ALTER TABLE user ADD PRIMARY KEY(`Student_ID`);

SELECT * FROM user;

INSERT INTO user (id, name, faculty_id, interest_id, tbc_id) VALUES
    ('0001', 'Sarah Tan', 
        (SELECT id FROM faculty WHERE programe = 'Software Engineering'),
        (SELECT id FROM interest WHERE interest = 'Programming'),
        (SELECT id FROM TBC WHERE interest_category = 'Academic Interests')
    );

INSERT INTO user (id, name, faculty_id, interest_id, tbc_id) VALUES
     ('0002', 'Ahmad Rizal', 
        (SELECT id FROM faculty WHERE programe = 'Software Engineering'),
        (SELECT id FROM interest WHERE interest = 'Basketball'),
        (SELECT id FROM TBC WHERE interest_category = 'Sports & Fitness')
    );

Insert INTO user (id, name, faculty_id, interest_id, tbc_id) VALUES
    ('0003', 'Michelle Wong', 
        (SELECT id FROM faculty WHERE programe = 'Business Management'),
        (SELECT id FROM interest WHERE interest = 'Marketing'),
        (SELECT id FROM TBC WHERE interest_category = 'Academic Interests')
    );

INSERT INTO user (id, name, faculty_id, interest_id, tbc_id) VALUES
    ('0004', 'Raj Kumar', 
        (SELECT id FROM faculty WHERE programe = 'Business Management'),
        (SELECT id FROM interest WHERE interest = 'Reading'),
        (SELECT id FROM TBC WHERE interest_category = 'Other Hobbies')
    );