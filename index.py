import sys
import os
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

logger.info("Python version: %s", sys.version)
logger.info("Current working directory: %s", os.getcwd())
logger.info("Directory contents: %s", os.listdir("."))
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
                          template_folder='app/templates',
                          static_folder='app/static')
        
        @application.route('/')
        def home():
            try:
                return render_template('login.html')
            except Exception as e:
                return f"Error rendering login template: {str(e)}<br>Path: {application.template_folder}"
        
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