CREATE TABLE details (serial_number SERIAL PRIMARY KEY, lastname VARCHAR(50),firstname VARCHAR(50),title VARCHAR(200),email VARCHAR(150),phone_number VARCHAR(50));

CREATE TABLE leaves (serial_number SERIAL PRIMARY KEY,date DATE NOT NULL,employee_id INTEGER NOT NULL REFERENCES details(serial_number),reason VARCHAR(50) NOT NULL,UNIQUE (date,employee_id));

CREATE TABLE designation (id SERIAL,designation VARCHAR(150) PRIMARY KEY,num_of_leaves INTEGER,UNIQUE (id,designation));