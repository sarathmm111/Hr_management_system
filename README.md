# HR Management System

This repository contains a simple HR Management System implemented in Python. The system is designed to perform various HR-related tasks such as creating and managing an employee database, handling leaves, generating vCards and QR codes, and providing a web interface for interactions.

## Features

### Initialization of Database Tables (initdb):

- Creates the necessary tables in the PostgreSQL database.
- Tables include `employee`, `leaves`, and `designation`.

### Importing Employee Data from CSV (import):

- Loads employee data from a CSV file into the `employee` table of the database.
- CSV file should contain columns for last name, first name, title, email, and phone.
- The name of the csv file was names.csv

### Retrieving Employee Information (retrieve):

- Retrieves information about a specific employee using their ID.
- Options to generate vCard, vCard file, and QR code for the employee.

### Generating vCards (genvcard):

- Generates vCard files for a specified number of employee records.
- Option to generate QR codes along with vCards.

### Inputting Leave Data (initleave):

- Allows the input of leave data into the `leaves` table.
- Requires the date, employee ID, and reason for leave.

### Retrieving Leave Data (retrieve_leave):

- Retrieves leave data for a specific employee, including available and taken leaves.

### Generating CSV of Leave Data (retrieve_csv):

- Generates a CSV file containing details of employees' leave data.

### Web Interface (web):
- python3 v_cards.py web//to run the web interface
- Provides a web interface for interacting with the HR system.
- Accessible at [http://localhost:5000](http://localhost:5000) after initializing the web server.

## Setup

### Dependencies:

- Python 3.x
- PostgreSQL database
- Required Python packages (can be installed using `pip install -r requirements.txt`)

### Configuration:

- Set up PostgreSQL and update the `config.ini` file with the appropriate database configurations.

### Running the Program:

- Execute the main script (`v_cards.py`) with appropriate command-line arguments.
- Example: `python v_cards.py initdb`
- See command-line options in the script for more details.

## Logging

Logging is implemented to provide information and debug messages. Logs are displayed on the console with the option to enable verbose logging.

