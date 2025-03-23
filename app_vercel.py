import sys
try:
    from flask import Flask, render_template, request, redirect, url_for, jsonify, flash
    import os
    import json
    from datetime import datetime
    print("Basic imports successful")
    
    # Try importing pkg_resources directly to check if it's available
    try:
        import pkg_resources
        print("pkg_resources is available")
    except ImportError as e:
        print(f"pkg_resources not available: {e}")
    
    # Try importing setuptools to check if it's available
    try:
        import setuptools
        print(f"setuptools version: {setuptools.__version__}")
    except ImportError as e:
        print(f"setuptools not available: {e}")
    
    # Try importing pyrebase carefully
    try:
        import pyrebase
        print("Pyrebase imported successfully")
    except ImportError as e:
        print(f"Pyrebase import error: {e}")
        
except ImportError as e:
    print(f"Basic import error: {e}")
    raise

# Initialize Flask app with correct template and static folder paths
app = Flask(__name__, 
           template_folder='app/templates',
           static_folder='app/static')

# Configure secret key
app.secret_key = os.environ.get('SECRET_KEY', os.urandom(24))

# Initialize Firebase if available
try:
    firebase_config = {
        "apiKey": os.getenv("FIREBASE_API_KEY"),
        "authDomain": os.getenv("FIREBASE_AUTH_DOMAIN"),
        "projectId": os.getenv("FIREBASE_PROJECT_ID"),
        "storageBucket": os.getenv("FIREBASE_STORAGE_BUCKET"),
        "messagingSenderId": os.getenv("FIREBASE_MESSAGING_SENDER_ID"),
        "appId": os.getenv("FIREBASE_APP_ID"),
        "databaseURL": os.getenv("FIREBASE_DATABASE_URL")
    }
    firebase = pyrebase.initialize_app(firebase_config)
    auth_firebase = firebase.auth()
    db = firebase.database()
    print("Firebase initialized successfully")
except Exception as e:
    print(f"Firebase initialization error: {e}")
    # Create dummy firebase objects for development
    firebase = None
    auth_firebase = None
    db = None

@app.route('/')
def index():
    try:
        return render_template('login.html')
    except Exception as e:
        return f"Error rendering login template: {str(e)}"

@app.route('/login', methods=['POST'])
def login():
    if not auth_firebase:
        return "Firebase authentication not available", 503

    email = request.form.get('email')
    password = request.form.get('password')
    
    try:
        user = auth_firebase.sign_in_with_email_and_password(email, password)
        user_id = user['localId']
        id_token = user['idToken']
        # Return token to client for future requests
        return redirect(url_for('dashboard', token=id_token))
    except Exception as e:
        error_message = "Login failed. Please check your credentials."
        flash(error_message)
        return redirect(url_for('index'))

@app.route('/health')
def health():
    return jsonify({
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "environment": os.environ.get("VERCEL_ENV", "unknown"),
        "setuptools_available": "setuptools" in sys.modules,
        "pkg_resources_available": "pkg_resources" in sys.modules,
        "pyrebase_available": "pyrebase" in sys.modules,
        "template_folder": app.template_folder,
        "static_folder": app.static_folder
    })

# Add a special debug route
@app.route('/debug')
def debug():
    modules = sorted([m for m in sys.modules.keys()])
    
    # Check if template folder exists
    template_folder_exists = os.path.exists(app.template_folder) if app.template_folder else False
    template_folder_contents = os.listdir(app.template_folder) if template_folder_exists else []
    
    return jsonify({
        "python_version": sys.version,
        "cwd": os.getcwd(),
        "files_in_cwd": os.listdir("."),
        "template_folder": app.template_folder,
        "template_folder_exists": template_folder_exists,
        "template_folder_contents": template_folder_contents,
        "sys_path": sys.path,
        "loaded_modules": modules[:50],  # First 50 modules to avoid response size limits
        "environment": {k: v for k, v in os.environ.items() if not k.startswith("AWS_")}
    })

if __name__ == '__main__':
    app.run(debug=True) 