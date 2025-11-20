import os
import time
from flask import Flask, request, jsonify, send_file
import psycopg2
from psycopg2 import OperationalError, errors
from werkzeug.security import check_password_hash, generate_password_hash # Import for hashing

app = Flask(__name__)

# --- Database Configuration ---
DB_HOST = os.environ.get('DB_HOST', 'db')
DB_NAME = os.environ.get('POSTGRES_DB', 'hackathondb')
DB_USER = os.environ.get('POSTGRES_USER', 'user')
DB_PASS = os.environ.get('POSTGRES_PASSWORD', 'password')
DB_PORT = "5432"

MAX_RETRIES = 15
RETRY_DELAY = 2

def get_db_connection():
    """Attempts to establish and return a PostgreSQL connection."""
    for i in range(MAX_RETRIES):
        try:
            conn = psycopg2.connect(
                host=DB_HOST,
                database=DB_NAME,
                user=DB_USER,
                password=DB_PASS,
                port=DB_PORT,
                connect_timeout=3
            )
            return conn
        except OperationalError as e:
            if i < MAX_RETRIES - 1:
                # print(f"DB connection attempt {i+1} failed. Retrying in {RETRY_DELAY}s...")
                time.sleep(RETRY_DELAY)
            else:
                # Simplified error raising since this function is usually called within a try/except
                raise OperationalError(f"Failed to connect to database after {MAX_RETRIES} attempts.")

def initialize_db():
    """Ensures the required 'users' table exists."""
    print("Attempting to initialize database...")
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        # Create users table if it doesn't exist.
        cur.execute("""
            CREATE TABLE IF NOT EXISTS users (
                student_id VARCHAR(50) PRIMARY KEY,
                password TEXT NOT NULL,
                image_data BYTEA,
                mime_type VARCHAR(50)
            );
        """)
        
        # Add a dummy user for testing, using werkzeug.security.generate_password_hash
        # Use generate_password_hash with 'pbkdf2:sha256' which is compatible with check_password_hash
        DUMMY_PASSWORD = 'password123'
        DUMMY_PASSWORD_HASH = generate_password_hash(DUMMY_PASSWORD) # Hash 'password123'
        
        cur.execute("SELECT 1 FROM users WHERE student_id = 'testuser'")
        if not cur.fetchone():
            print(f"Inserting dummy user: 'testuser' with password '{DUMMY_PASSWORD}'")
            cur.execute("""
                INSERT INTO users (student_id, password, mime_type) VALUES 
                (%s, %s, %s)
            """, ('testuser', DUMMY_PASSWORD_HASH, 'image/png'))
        
        conn.commit()
        cur.close()
        conn.close()
        print("Database initialization successful.")

    except OperationalError as e:
        print(f"DB initialization failed: {e}")
    except Exception as e:
        print(f"An unexpected error occurred during DB initialization: {e}")


# --- Flask Routes ---

@app.route('/', methods=['GET'])
def home():
    """Serves the index.html (Login page)."""
    return send_file('index.html')

@app.route('/registration', methods=['GET'])
def registration_page():
    """Serves the registration.html page."""
    return send_file('registration.html')


@app.route('/login', methods=['POST'])
def login():
    """Handles user login and returns student details and base64 image data."""
    
    response = {'success': False, 'message': "", 'student_id': '', 'image': '', 'mime_type': ''}
    
    data = request.get_json(silent=True)
    if not data:
        data = request.form # Fallback for form-encoded data
        
    student_id = data.get('student_id')
    password = data.get('password')

    if not student_id or not password:
        response['message'] = "Please provide all information."
        return jsonify(response), 400

    try:
        conn = get_db_connection()
        cur = conn.cursor()

        # Prepare and execute the SQL query to fetch password hash and image data
        cur.execute("SELECT student_id, password, image_data, mime_type FROM users WHERE student_id = %s", (student_id,))
        row = cur.fetchone() 
        column_names = [desc[0] for desc in cur.description]
        row_dict = dict(zip(column_names, row)) if row else None

        cur.close()
        conn.close()

        if row_dict and check_password_hash(row_dict['password'], password):
            # Credentials valid
            response['success'] = True
            response['message'] = "Login successful"
            response['student_id'] = row_dict['student_id']

            if row_dict['image_data']:
                # Convert binary image data to base64 string
                response['image'] = row_dict['image_data'].tobytes().decode('latin-1')
                response['mime_type'] = row_dict['mime_type']
            else:
                response['message'] = "Verified, but no valid image data found."

        else:
            response['message'] = "Invalid Credentials."
            
    except OperationalError as e:
        response['message'] = f"Database connectivity error."
        print(f"Database error in login: {e}")
        return jsonify(response), 500
    except Exception as e:
        response['message'] = f"An unexpected server error occurred."
        print(f"Server error in login: {e}")
        return jsonify(response), 500
        
    return jsonify(response)


@app.route('/api/register', methods=['POST'])
def register_student():
    """Handles new student registration, hashes password, and inserts into DB."""
    
    response = {'success': False, 'message': "", 'student_id': ''}
    data = request.get_json(silent=True)
    
    student_id = data.get('student_id')
    password = data.get('password')

    if not student_id or not password:
        response['message'] = "Please provide both Student ID and Password."
        return jsonify(response), 400

    # Basic validation (must match front-end)
    if len(student_id) < 8 or len(password) < 8:
        response['message'] = "Student ID and Password must be at least 8 characters long."
        return jsonify(response), 400

    try:
        conn = get_db_connection()
        cur = conn.cursor()

        # 1. Hash the password before storing it
        hashed_password = generate_password_hash(password)

        # 2. Insert new user into the database
        cur.execute("""
            INSERT INTO users (student_id, password) VALUES (%s, %s);
        """, (student_id, hashed_password))
        
        conn.commit()
        cur.close()
        conn.close()

        response['success'] = True
        response['message'] = "Registration successful."
        response['student_id'] = student_id
        
    except errors.UniqueViolation:
        response['message'] = f"Student ID '{student_id}' already exists. Please choose a different ID or log in."
        print(f"Registration failed: Student ID already exists.")
        return jsonify(response), 409 # HTTP 409 Conflict

    except OperationalError as e:
        response['message'] = f"Database connectivity error during registration."
        print(f"Database error in register: {e}")
        return jsonify(response), 500
        
    except Exception as e:
        response['message'] = f"An unexpected server error occurred during registration."
        print(f"Server error in register: {e}")
        return jsonify(response), 500
        
    return jsonify(response)


# --- Startup and Entrypoint ---

# Initialize the database table before running the app
initialize_db()

if __name__ == '__main__':
    # This block is only for local testing, not used by Gunicorn/Docker CMD
    app.run(debug=True, host='0.0.0.0', port=8000)