import os
from flask import Flask, json, render_template, request, redirect, url_for, flash
import mysql.connector
from datetime import datetime
import re

app = Flask(__name__)
app.secret_key = 'super secret key'

def get_db_connection():
    try:
        dbconn = mysql.connector.connect(
            host="localhost",
            user="root",
            password="",
            database="coop"
        )
        return dbconn
    except mysql.connector.Error as err:
        print(f"Error connecting to MySQL: {err}")
        return None

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    message = ""
    success = False

    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        connection = get_db_connection()
        if connection:
            cursor = connection.cursor()
            query = "SELECT * FROM users WHERE email = %s"  
            cursor.execute(query, (username,))
            user = cursor.fetchone()

            if user and user[2] == password:  # Access password
                message = "Account Login Successfully!<br> Redirecting to product page"
                success = True
                # Store user info in session if needed
                return render_template('products.html', message=message, success=success)
            else:
                message = "Invalid input. Email and Password not found"  # Changed message
            cursor.close()
            connection.close()
        else:
            message = "Database connection error. Please try again."

    return render_template('login.html', message=message, success=success)

@app.route('/register/', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        first_name = request.form['firstName']
        middle_name = request.form['middleName']
        last_name = request.form['lastName']
        birthdate_str = request.form['birthdate']
        email = request.form['email']
        password = request.form['password']
        confirm_password = request.form['confirmPassword']

        print("\n--- Registration Form Data ---")
        print(f"First Name: {first_name}")
        print(f"Middle Name: {middle_name}")
        print(f"Last Name: {last_name}")
        print(f"Birthdate (string): {birthdate_str}")
        print(f"Email: {email}")
        print(f"Password: {password}")
        print(f"Confirm Password: {confirm_password}")

        # --- Validation ---
        if not all([first_name and first_name.strip(), last_name and last_name.strip(), birthdate_str, email and email.strip(), password, confirm_password]):
            flash('All required fields must be filled.', 'error')
            print("Validation Failed: Missing required fields")
            return render_template('register.html')

        if password != confirm_password:
            flash('Passwords do not match.', 'error')
            print("Validation Failed: Passwords do not match")
            return render_template('register.html')

        if not re.match(r"[^@]+@[^@]+\.[^@]+", email):
            flash("Invalid email address.", "error")
            print("Validation Failed: Invalid email address")
            return render_template('register.html')

        try:
            birthdate = datetime.strptime(birthdate_str, '%Y-%m-%d').date()
            if birthdate > datetime.now().date():
                flash('Birthdate cannot be in the future', 'error')
                print("Validation Failed: Birthdate in the future")
                return render_template('register.html')
            print(f"Birthdate (datetime.date): {birthdate}")
        except ValueError:
            flash('Invalid date format. Please use %Y-%m-%d.', 'error')
            print("Validation Failed: Invalid date format")
            return render_template('register.html')

        if (len(password) < 8 or not any(c.isupper() for c in password)
                or not any(c.islower() for c in password)
                or not any(c.isdigit() for c in password)
                or not re.search(r'[!@#$%^&*(),.?":{}|<>]', password)):
            flash('Password must meet complexity requirements.', 'error')
            print("Validation Failed: Password complexity")
            return render_template('register.html')

        # DATABASE TO
        dbconn = get_db_connection()
        cursor = dbconn.cursor() if dbconn else None

        if cursor:
            try:
                print("\n--- Attempting Database Insertion ---")
                print(f"Value of birthdate before insert: {birthdate}")

                sql = """
                    INSERT INTO users (email, password, fname, lname, mname, birthdate)
                    VALUES (%s, %s, %s, %s, %s, %s)
                """
                data_to_insert = (email, password, first_name, last_name, middle_name, birthdate)
                print(f"SQL Query: {sql}")
                print(f"Data to Insert: {data_to_insert}")
                cursor.execute(sql, data_to_insert)
                dbconn.commit()
                print("Database commit successful!")
                flash('Registration successful! Please log in.', 'success')
                return redirect(url_for('login'))
            except mysql.connector.Error as err:
                flash(f'Database Error: {err}', 'error')
                print(f"Database Insert Error: {err}")
                print(f"MySQL Error Number: {err.errno}")
                print(f"MySQL Error SQLSTATE: {err.sqlstate}")
                dbconn.rollback()
                return render_template('register.html')
            except Exception as e:
                flash(f'An unexpected error occurred: {e}', 'error')
                print(f"Unexpected Error during database operation: {e}")
                return render_template('register.html')
            finally:
                cursor.close()
                dbconn.close()
        else:
            flash('Could not connect to the database.', 'error')
            print("Error: Could not get database cursor")
            return render_template('register.html')
    return render_template('register.html')


@app.route('/products')
def products():
    try:
        # Construct the absolute path to the JSON file
        json_path = os.path.join(app.static_folder, 'data', 'products.json')
        print(f"Attempting to open: {json_path}")
        with open(json_path, 'r') as f:
            product_data = json.load(f)
        print("products.json loaded successfully:")
        print(product_data)
        return render_template('products.html', products=product_data)
    except FileNotFoundError:
        print(f"Error: products.json not found at: {json_path}")
        return "Error: Could not load products.", 500
    except json.JSONDecodeError:
        print("Error: Invalid JSON in products.json!")
        return "Error: Invalid product data.", 500


if __name__ == "__main__":
    app.run(debug=True)
