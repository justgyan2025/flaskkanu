import sys
import os
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

logger.info("Python version: %s", sys.version)
logger.info("Current working directory: %s", os.getcwd())
logger.info("Directory contents: %s", os.listdir("."))

# Get absolute paths for templates and static files
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
TEMPLATE_FOLDER = os.path.join(BASE_DIR, 'app', 'templates')
STATIC_FOLDER = os.path.join(BASE_DIR, 'app', 'static')

logger.info("Base directory: %s", BASE_DIR)
logger.info("Template folder path: %s", TEMPLATE_FOLDER)
logger.info("Template folder exists: %s", os.path.exists(TEMPLATE_FOLDER))
if os.path.exists(TEMPLATE_FOLDER):
    logger.info("Template folder contents: %s", os.listdir(TEMPLATE_FOLDER))
logger.info("Python path: %s", sys.path)

# First try importing Flask to verify it's installed
try:
    from flask import Flask, render_template, jsonify
    logger.info("Flask imported successfully")
except ImportError as e:
    logger.error("Failed to import Flask: %s", e)
    raise

# Try to import from our simplified app first
try:
    logger.info("Attempting to import app_vercel.py...")
    from app_vercel import app
    logger.info("Successfully imported app_vercel.py")
    # Use the imported app - this should now show the login page
    application = app
except ImportError as e:
    logger.error("Error importing app_vercel: %s", e)
    logger.info("Trying to import from main app.py")
    
    # Try to import from the main app
    try:
        from app import app
        logger.info("Successfully imported from app.py")
        application = app
    except ImportError as e:
        logger.error("Error importing app.py: %s", e)
        logger.info("Falling back to basic Flask app")
        
        # Create a basic Flask app as fallback
        application = Flask(__name__, 
                          template_folder=TEMPLATE_FOLDER,
                          static_folder=STATIC_FOLDER)
        
        @application.route('/')
        def home():
            try:
                # Try to render the login template
                return render_template('login.html')
            except Exception as e:
                error_msg = f"Error rendering login template: {str(e)}"
                print(error_msg)
                # Serve an inline login page if template loading fails
                return f"""
                <!DOCTYPE html>
                <html lang="en">
                <head>
                    <meta charset="UTF-8">
                    <meta name="viewport" content="width=device-width, initial-scale=1.0">
                    <title>Investment Tracker - Login</title>
                    <style>
                        body {{
                            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                            background-color: #f0f2f5;
                            margin: 0;
                            padding: 0;
                            display: flex;
                            justify-content: center;
                            align-items: center;
                            height: 100vh;
                        }}
                        .login-container {{
                            background-color: white;
                            border-radius: 8px;
                            box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
                            padding: 40px;
                            width: 100%;
                            max-width: 400px;
                        }}
                        .form-title {{
                            color: #2c3e50;
                            text-align: center;
                            margin-bottom: 30px;
                        }}
                        .form-group {{
                            margin-bottom: 20px;
                        }}
                        .form-label {{
                            display: block;
                            margin-bottom: 8px;
                            font-weight: 500;
                            color: #3d4852;
                        }}
                        .form-input {{
                            width: 100%;
                            padding: 12px 15px;
                            border: 1px solid #e1e1e1;
                            border-radius: 4px;
                            font-size: 16px;
                            box-sizing: border-box;
                        }}
                        .form-button {{
                            background-color: #3498db;
                            color: white;
                            border: none;
                            border-radius: 4px;
                            padding: 12px 20px;
                            width: 100%;
                            font-size: 16px;
                            cursor: pointer;
                        }}
                        .form-button:hover {{
                            background-color: #2980b9;
                        }}
                        .flash-message {{
                            background-color: #f8d7da;
                            color: #721c24;
                            padding: 12px;
                            border-radius: 4px;
                            margin-bottom: 20px;
                        }}
                    </style>
                </head>
                <body>
                    <div class="login-container">
                        <h1 class="form-title">Investment Tracker</h1>
                        <div class="flash-message" style="display: none;">Error message will appear here</div>
                        <form action="/login" method="POST">
                            <div class="form-group">
                                <label for="email" class="form-label">Email Address</label>
                                <input type="email" id="email" name="email" class="form-input" required>
                            </div>
                            <div class="form-group">
                                <label for="password" class="form-label">Password</label>
                                <input type="password" id="password" name="password" class="form-input" required>
                            </div>
                            <button type="submit" class="form-button">Login</button>
                        </form>
                        <div style="margin-top: 15px; font-size: 12px; color: #666; text-align: center;">
                            Note: This is a backup login page. Template rendering failed.
                        </div>
                    </div>
                </body>
                </html>
                """
        
        @application.route('/debug')
        def debug():
            # Return debug information
            template_folder_exists = os.path.exists(application.template_folder) if application.template_folder else False
            template_files = os.listdir(application.template_folder) if template_folder_exists else []
            
            debug_info = {
                "python_version": sys.version,
                "cwd": os.getcwd(),
                "directory_contents": os.listdir("."),
                "python_path": str(sys.path),
                "template_folder": application.template_folder,
                "template_folder_exists": template_folder_exists,
                "template_files": template_files,
                "environment_variables": {k: v for k, v in os.environ.items() if not k.startswith("AWS_")}
            }
            return jsonify(debug_info)

# Export the application for Vercel
app = application

if __name__ == "__main__":
    app.run() 