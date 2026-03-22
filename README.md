**Hospital Management System**



**## Project Overview**

The Hospital Management System is a web-based application developed to manage hospital workflows including patient management, doctor management, appointment scheduling, and treatment records. The system provides role-based access for Admin, Doctor, and Patient.



**## Features**



**### Admin**

\- Add, edit, and delete doctor profiles

\- View all registered patients

\- Track scheduled, completed, and cancelled appointments

\- Access patient medical history and treatment details



**### Doctor**

\- View dashboard with upcoming appointments

\- Access patient list

\- Update availability schedule

\- Record treatment details (diagnosis, prescription, notes)

\- View patient medical history



**### Patient**

\- Register and log in securely

\- Search doctors by name or specialization

\- Book, reschedule, or cancel appointments

\- View past consultations and treatment notes



**## Tech Stack**

\- Backend: Python, Flask

\- Database: SQLite

\- Frontend: HTML, CSS, Bootstrap

\- Template Engine: Jinja2

\- SQL: Raw SQL Queries



**## Database Tables**

\- Users

\- Patients

\- Doctors

\- Departments

\- Appointments

\- Treatments



**## Project Structure**

hospital-management-system

|

|\_\_controllers/

|\_\_migrations/

|\_\_ststic/

|\_\_templates/

|\_\_app.py

|\_\_database.py

|\_\_database\_setup.py

|\_\_hospital\_system.db

|\_\_models.py

|\_\_README.md

|\_\_requirements.txt

|\_\_.gitignore



**## How to Run the Project**



1\. Clone the repository

2\. Install dependencies

3\. Run the Flask app



pip install -r requirements.txt

python app.py



Open browser and go to:



http://127.0.0.1:5000/



**## Future Improvements**

\- Email notifications

\- Online payments

\- Admin analytics dashboard

\- Report generation

\- SMS appointment reminders



**## Author**

Pragya Deshwal

B.Sc Physical Science with Computer Science – Miranda House

B.S Data Science – IIT Madras
