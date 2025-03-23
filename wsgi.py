import sys
import os

print("Python version:", sys.version)
print("Current working directory:", os.getcwd())
print("Directory contents:", os.listdir("."))
print("Checking if site-packages is accessible...")
print(sys.path)

try:
    import flask
    print("Flask version:", flask.__version__)
except ImportError as e:
    print(f"Flask import error: {e}")

try:
    from app import app
except ImportError as e:
    print(f"App import error: {e}")
    # For debugging: try to manually import Flask again
    try:
        from flask import Flask
        print("Flask can be imported directly here, but not in app.py")
    except ImportError:
        print("Flask cannot be imported here either")
    raise

app = app

if __name__ == "__main__":
    app.run() 