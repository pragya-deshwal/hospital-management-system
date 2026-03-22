from flask import Flask
from database import start_connection, close_connection
from controllers.authentication import authentication_blueprint
from controllers.admin import admin_blueprint
from controllers.doctor import doctor_blueprint
from controllers.patient import patient_blueprint

app = Flask(__name__)
app.secret_key = "hosp_management1"

#It will register the authentication blueprint
app.register_blueprint(authentication_blueprint)
app.register_blueprint(admin_blueprint)
app.register_blueprint(doctor_blueprint)
app.register_blueprint(patient_blueprint)

#Close the database connection after each request
@app.teardown_appcontext
def teardown_database(exception):
    close_connection()

@app.route("/")
def home():
    return "Hospital Management System is running and database has been connected"

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=8000, debug=True)



