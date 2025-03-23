import sys
try:
    from flask import Flask, render_template, request, redirect, url_for, jsonify
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

# Initialize Flask app
app = Flask(__name__)

@app.route('/')
def index():
    return "Hello from Investment Tracker! Flask is working correctly."

@app.route('/health')
def health():
    return jsonify({
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "environment": os.environ.get("VERCEL_ENV", "unknown"),
        "setuptools_available": "setuptools" in sys.modules,
        "pkg_resources_available": "pkg_resources" in sys.modules,
        "pyrebase_available": "pyrebase" in sys.modules
    })

# Add a special debug route
@app.route('/debug')
def debug():
    modules = sorted([m for m in sys.modules.keys()])
    return jsonify({
        "python_version": sys.version,
        "cwd": os.getcwd(),
        "files_in_cwd": os.listdir("."),
        "sys_path": sys.path,
        "loaded_modules": modules[:50],  # First 50 modules to avoid response size limits
        "environment": dict(os.environ)
    })

if __name__ == '__main__':
    app.run(debug=True) 