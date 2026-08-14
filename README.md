# Employee Management System

A professional Employee Management System built with Flask and Oracle Database.

This application provides a complete CRUD interface for managing employee records, including creating, viewing, updating, deleting, and searching employees.

## Features

- Add new employees
- View all employees
- Edit employee information
- Delete employees
- Search employees
- Dynamic employee count dashboard
- Oracle Database integration
- Form validation
- Backend validation
- Duplicate email handling
- Success and error flash messages
- Responsive Bootstrap UI
- Secure environment variables using `.env`

## Technologies Used

- Python 3.14
- Flask 3.1
- Oracle Database 11g
- python-oracledb
- Bootstrap 5.3
- HTML5
- CSS3
- Jinja2
- python-dotenv
- Git & GitHub

## Project Structure

```text
employee-management-system/
│
├── app.py
├── .env
├── .env.example
├── .gitignore
├── README.md
├── requirements.txt
│
├── app/
│
├── database/
│   ├── db.py
│   ├── test_connection.py
│   └── create_tables.sql
│
├── static/
│
└── templates/
    ├── index.html
    ├── employees.html
    ├── add_employee.html
    └── edit_employee.html
