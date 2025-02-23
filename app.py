from flask import Flask, request, jsonify, send_from_directory, session, redirect, url_for, render_template
from werkzeug.security import generate_password_hash, check_password_hash
from flask_bcrypt import Bcrypt
from check.duplicate_check import check_bp, calculate_file_hash, check_duplicate, add_file_to_db, log_download, sanitize_filename, generate_unique_filename
import os
import urllib.parse
from datetime import datetime
from urllib.request import urlopen
import re
from werkzeug.security import check_password_hash
from database import get_database
from flask_bcrypt import Bcrypt
from pymongo import MongoClient
from flask import request, jsonify, render_template
from auth.validation import is_valid_employee

app = Flask(__name__, template_folder="templates", static_folder="static")
bcrypt = Bcrypt(app)
UPLOAD_FOLDER = "./static/uploads"
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
ALLOWED_EXTENSIONS = {'pdf', 'jpg', 'jpeg', 'png', 'mp3', 'xlsx', 'xls', 'txt'}

# Setup MongoDB
client = MongoClient("mongodb://localhost:27017/")
db = client["ddas1"]  # Your database name
users_collection = db["users"]  # Your collection name

app.secret_key = "b28c2b3caf1a8963f4523f82358ecc93"  # Use a secure secret key

# Register authentication routes (accessed as /auth/login and /auth/register)

app.register_blueprint(check_bp, url_prefix="/check")
from flask import Flask, request, jsonify, session

from flask import redirect, url_for, session, jsonify, render_template, request
from werkzeug.security import check_password_hash

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "GET":
        return render_template("login.html")

    data = request.get_json() or request.form
    email = data.get("email")
    password = data.get("password")

    print(f"Login attempt: {email}")
    print(f"Password entered by user: {password}")

    user = users_collection.find_one({"email": email})
    print(f"User found: {user}")

    if user:
        print(f"Stored password hash: {user['password']}")
        password_check = check_password_hash(user["password"], password)
        print(f"Password check result: {password_check}")

        if password_check:
            session["user_email"] = user["email"]
            print(f"Session set for: {session['user_email']}")
            return jsonify({"message": "Login successful", "redirect": url_for("index")}), 200
        
        else:
            print("Password mismatch.")
    else:
        print("User not found.")

    return jsonify({"error": "Invalid credentials"}), 401

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "GET":
        return render_template("register.html")

    data = request.get_json() or request.form
    email = data.get("email")
    password = data.get("password")

    # ✅ Check if email exists in employee CSV
    if not is_valid_employee(email):
        return jsonify({"error": "Email not found in the employee database"}), 403

    if users_collection.find_one({"email": email}):
        return jsonify({"error": "User already exists"}), 409

    hashed_password = bcrypt.generate_password_hash(password).decode("utf-8")
    users_collection.insert_one({"email": email, "password": hashed_password})

    return jsonify({"message": "Registration successful"}), 201

@app.route("/")
def home():
    return redirect(url_for("login"))

@app.route("/dashboard")
def dashboard():
    if "user_email" in session:
        return render_template("dashboard.html")
    else:
        return redirect(url_for("login"))


@app.route("/logout", methods=["POST"])
def logout():
    session.clear()
    return jsonify({"message": "Logged out successfully"}), 200


# Home route: Serve index.html from the frontend folder
@app.route("/index", methods=["GET", "POST"])
def index():
    if "user_email" in session:
        print(f"User {session['user_email']} accessed index page.")
        return render_template("index.html")
    else:
        print("User not logged in. Redirecting to login.")
        return redirect(url_for("login"))

# Serve any static file from the frontend folder
@app.route("/<path:path>")
def serve_static_files(path):
    return send_from_directory("../frontend", path)

# Upload route
@app.route("/upload", methods=["POST"])
def upload_file():
    file = request.files.get("file")
    user_id = request.form.get("user_id")
    
    if not file or not user_id:
        return jsonify({"error": "File and user ID are required"}), 400
    
    file_path = os.path.join(UPLOAD_FOLDER, file.filename)
    file.save(file_path)
    
    # Calculate the file hash
    file_hash = calculate_file_hash(file_path)
    
    # Check for duplicates using file hash
    duplicate = check_duplicate(file_hash=file_hash)
    if duplicate:
        return jsonify({
            "message": "Duplicate file detected",
            "uploaded_by": duplicate.get("uploaded_by", "Unknown")
        }), 409
    
    # Save file details to the database
    add_file_to_db(file.filename, file_path, file_hash, description="File metadata", url=None, user_id=user_id)
    return jsonify({"message": "File uploaded successfully"})

# Download route (by file name)
@app.route("/download_by_name", methods=["POST"])
def download_by_name():
    file_name = request.json.get("file_name")
    user_id = request.json.get("user_id")
    
    if not file_name or not user_id:
        return jsonify({"error": "File name and user ID are required"}), 400
    
    # Retrieve file details from the database
    db = get_database()
    file_entry = db["files"].find_one({"file_name": file_name})
    
    if not file_entry:
        return jsonify({"error": "File not found"}), 404
    
    # Use file hash to detect if the user has already downloaded the file
    user_download_entry = db["downloads"].find_one({"file_name": file_name, "user_id": user_id})
    if user_download_entry:
        return jsonify({
            "message": "Duplicate file detected",
            "uploaded_by": file_entry.get("uploaded_by", "Unknown"),
            "users": list(db["downloads"].find({"file_name": file_name}, {"user_id": 1, "timestamp": 1, "_id": 0}))
        }), 200
    
    # Log the download for this user
    log_download(file_name, user_id)
    
    # Return the file as a downloadable response
    return send_from_directory(
        directory=os.path.dirname(file_entry["file_path"]),
        path=os.path.basename(file_entry["file_path"]),
        as_attachment=True
    )

# Download from URL route
@app.route("/download_from_url", methods=["POST"])
def download_from_url():
    data = request.json
    file_url = data.get("file_url")
    user_id = data.get("user_id")
    
    if not file_url or not user_id:
        return jsonify({"error": "Missing file URL or user ID"}), 400
    
    try:
        # Handle Google Drive links
        if "drive.google.com" in file_url:
            match = re.search(r"/file/d/([^/]+)/", file_url)
            if match:
                file_id = match.group(1)
                file_url = f"https://drive.google.com/uc?export=download&id={file_id}"
        
        # Fetch file with headers
        def fetch_file_with_headers(file_url):
            headers = {
                "User-Agent": (
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                    "(KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
                )
            }
            req = urllib.request.Request(file_url, headers=headers)
            response = urllib.request.urlopen(req)
            return response
        
        temp_path = os.path.join(app.config["UPLOAD_FOLDER"], "temp_download")
        with fetch_file_with_headers(file_url) as response, open(temp_path, 'wb') as temp_file:
            temp_file.write(response.read())
        
        # Compute file hash
        file_hash = calculate_file_hash(temp_path)
        
        # Check for duplicates
        duplicate = check_duplicate(file_hash=file_hash, url=file_url)
        if duplicate:
            os.remove(temp_path)
            return jsonify({
                "message": "Duplicate file detected",
                "existing_file": duplicate["file_name"],
                "location": duplicate["file_path"],
                "metadata": duplicate["metadata"],
                "users": duplicate["users"]
            }), 200
        
        # No duplicate: move the temp file to its final location
        unique_filename = generate_unique_filename(file_url, file_hash)
        file_path = os.path.join(app.config["UPLOAD_FOLDER"], unique_filename)
        os.rename(temp_path, file_path)
        
        # Add the file to the database
        add_file_to_db(unique_filename, file_path, file_hash, description=f"Downloaded from {file_url}", url=file_url, user_id=user_id)
        # Log the download
        log_download(unique_filename, user_id)
        
        return jsonify({"message": "File downloaded and processed successfully"}), 200
    
    except urllib.error.HTTPError as e:
        return jsonify({"error": f"HTTP error occurred: {e.code} {e.reason}"}), e.code
    except urllib.error.URLError as e:
        return jsonify({"error": f"URL error occurred: {e.reason}"}), 400
    except Exception as e:
        return jsonify({"error": f"An unexpected error occurred: {str(e)}"}), 500

# Get all files route
@app.route("/get_files", methods=["GET"])
def get_files():
    try:
        db = get_database()
        files = db["files"].find()
        files_list = [{"file_name": file["file_name"], "file_path": file["file_path"], "uploaded_by": file.get("uploaded_by", "Unknown")} for file in files]
        return jsonify({"files": files_list})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    if not os.path.exists(UPLOAD_FOLDER):
        os.makedirs(UPLOAD_FOLDER)
    app.run(host="0.0.0.0", port=5000, debug=True)