import sys
import os
try:
    from flask import Flask, render_template, request, redirect, url_for, jsonify, flash
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

# Get absolute paths for templates and static files
# For Vercel, we need to adjust paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
TEMPLATE_FOLDER = os.path.join(BASE_DIR, 'app', 'templates')
STATIC_FOLDER = os.path.join(BASE_DIR, 'app', 'static')

# Print paths for debugging
print(f"Base directory: {BASE_DIR}")
print(f"Template folder path: {TEMPLATE_FOLDER}")
print(f"Template folder exists: {os.path.exists(TEMPLATE_FOLDER)}")
if os.path.exists(TEMPLATE_FOLDER):
    print(f"Template folder contents: {os.listdir(TEMPLATE_FOLDER)}")

# Initialize Flask app with absolute path to templates
app = Flask(__name__, 
           template_folder=TEMPLATE_FOLDER,
           static_folder=STATIC_FOLDER)

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
        # Try to list template directory contents
        template_dir = app.template_folder
        if os.path.exists(template_dir):
            print(f"Template dir contents: {os.listdir(template_dir)}")
        else:
            print(f"Template dir does not exist: {template_dir}")
        
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

@app.route('/dashboard')
def dashboard():
    # Get token from request
    token = request.args.get('token')
    
    if not token:
        flash("Authentication required")
        return redirect(url_for('index'))
    
    try:
        # Verify the token
        user = auth_firebase.get_account_info(token)
        user_id = user['users'][0]['localId']
        
        # For now, just render a simple dashboard
        return f"""
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Investment Tracker - Dashboard</title>
            <style>
                body {{
                    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                    background-color: #f0f2f5;
                    margin: 0;
                    padding: 0;
                }}
                .navbar {{
                    background-color: #2c3e50;
                    color: white;
                    padding: 15px 20px;
                    display: flex;
                    justify-content: space-between;
                    align-items: center;
                }}
                .navbar-brand {{
                    font-size: 24px;
                    font-weight: bold;
                }}
                .navbar-menu {{
                    display: flex;
                    gap: 20px;
                }}
                .navbar-menu a {{
                    color: white;
                    text-decoration: none;
                    padding: 5px 10px;
                }}
                .navbar-menu a:hover {{
                    background-color: rgba(255, 255, 255, 0.1);
                    border-radius: 4px;
                }}
                .content {{
                    padding: 20px;
                    max-width: 1200px;
                    margin: 0 auto;
                }}
                .welcome-card {{
                    background-color: white;
                    border-radius: 8px;
                    box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
                    padding: 20px;
                    margin-bottom: 20px;
                }}
                .card-title {{
                    color: #2c3e50;
                    margin-top: 0;
                }}
            </style>
        </head>
        <body>
            <div class="navbar">
                <div class="navbar-brand">Investment Tracker</div>
                <div class="navbar-menu">
                    <a href="/dashboard?token={token}">Dashboard</a>
                    <a href="/stocks?token={token}">Stocks</a>
                    <a href="/mutual-funds?token={token}">Mutual Funds</a>
                    <a href="/logout">Logout</a>
                </div>
            </div>
            <div class="content">
                <div class="welcome-card">
                    <h2 class="card-title">Welcome to Your Investment Dashboard</h2>
                    <p>This is a simple dashboard view. You can use the navigation bar to access different sections of the application.</p>
                </div>
                <div class="welcome-card">
                    <h3 class="card-title">Quick Links</h3>
                    <ul>
                        <li><a href="/stocks?token={token}">Manage your stock portfolio</a></li>
                        <li><a href="/mutual-funds?token={token}">Manage your mutual fund investments</a></li>
                    </ul>
                </div>
            </div>
        </body>
        </html>
        """
    except Exception as e:
        flash("Authentication failed")
        return redirect(url_for('index'))

@app.route('/logout')
def logout():
    # Simply redirect to the login page
    return redirect(url_for('index'))

@app.route('/stocks')
def stocks():
    # Get token from request
    token = request.args.get('token')
    
    if not token:
        flash("Authentication required")
        return redirect(url_for('index'))
    
    try:
        # Verify the token
        user = auth_firebase.get_account_info(token)
        user_id = user['users'][0]['localId']
        
        # Get user's stocks (or return empty dict if not found)
        stocks_data = {}
        if db:
            try:
                stocks_data = db.child("users").child(user_id).child("stocks").get(token).val() or {}
            except Exception as e:
                print(f"Error fetching stocks: {e}")
        
        # Generate table rows HTML
        table_rows = ""
        for ticker, stock_data in stocks_data.items():
            name = stock_data.get('name', 'N/A')
            quantity = stock_data.get('quantity', 0)
            purchase_price = float(stock_data.get('purchase_price', 0))
            current_price = float(stock_data.get('current_price', 0))
            value = current_price * quantity
            gain_loss = ((current_price - purchase_price) / purchase_price * 100) if purchase_price > 0 else 0
            
            table_rows += f"""
            <tr>
                <td>{ticker}</td>
                <td>{name}</td>
                <td>{quantity}</td>
                <td>{purchase_price:.2f}</td>
                <td>{current_price:.2f}</td>
                <td>{value:.2f}</td>
                <td>{gain_loss:.2f}%</td>
            </tr>
            """
        
        # Render the stocks page
        return f"""
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Investment Tracker - Stocks</title>
            <style>
                body {{
                    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                    background-color: #f0f2f5;
                    margin: 0;
                    padding: 0;
                }}
                .navbar {{
                    background-color: #2c3e50;
                    color: white;
                    padding: 15px 20px;
                    display: flex;
                    justify-content: space-between;
                    align-items: center;
                }}
                .navbar-brand {{
                    font-size: 24px;
                    font-weight: bold;
                }}
                .navbar-menu {{
                    display: flex;
                    gap: 20px;
                }}
                .navbar-menu a {{
                    color: white;
                    text-decoration: none;
                    padding: 5px 10px;
                }}
                .navbar-menu a:hover {{
                    background-color: rgba(255, 255, 255, 0.1);
                    border-radius: 4px;
                }}
                .content {{
                    padding: 20px;
                    max-width: 1200px;
                    margin: 0 auto;
                }}
                .card {{
                    background-color: white;
                    border-radius: 8px;
                    box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
                    padding: 20px;
                    margin-bottom: 20px;
                }}
                .card-title {{
                    color: #2c3e50;
                    margin-top: 0;
                }}
                .btn {{
                    display: inline-block;
                    background-color: #3498db;
                    color: white;
                    border: none;
                    border-radius: 4px;
                    padding: 10px 15px;
                    cursor: pointer;
                    text-decoration: none;
                }}
                .btn:hover {{
                    background-color: #2980b9;
                }}
                table {{
                    width: 100%;
                    border-collapse: collapse;
                    margin-top: 20px;
                }}
                th, td {{
                    padding: 12px;
                    text-align: left;
                    border-bottom: 1px solid #ddd;
                }}
                th {{
                    background-color: #f8f9fa;
                    font-weight: 600;
                }}
                tr:hover {{
                    background-color: #f5f5f5;
                }}
                .form-group {{
                    margin-bottom: 15px;
                }}
                .form-label {{
                    display: block;
                    margin-bottom: 5px;
                    font-weight: 500;
                }}
                .form-input {{
                    width: 100%;
                    padding: 10px;
                    border: 1px solid #ddd;
                    border-radius: 4px;
                    box-sizing: border-box;
                }}
                .form-row {{
                    display: flex;
                    gap: 15px;
                }}
                .form-row .form-group {{
                    flex: 1;
                }}
            </style>
        </head>
        <body>
            <div class="navbar">
                <div class="navbar-brand">Investment Tracker</div>
                <div class="navbar-menu">
                    <a href="/dashboard?token={token}">Dashboard</a>
                    <a href="/stocks?token={token}">Stocks</a>
                    <a href="/mutual-funds?token={token}">Mutual Funds</a>
                    <a href="/logout">Logout</a>
                </div>
            </div>
            <div class="content">
                <div class="card">
                    <h2 class="card-title">Your Stock Portfolio</h2>
                    <a href="#" class="btn" onclick="showAddStockForm()">Add New Stock</a>
                    
                    <div id="addStockForm" style="display: none; margin-top: 20px;">
                        <h3>Add a Stock</h3>
                        <form action="/add_stock" method="POST">
                            <input type="hidden" name="token" value="{token}">
                            
                            <div class="form-row">
                                <div class="form-group">
                                    <label for="ticker" class="form-label">Stock Ticker</label>
                                    <div style="display: flex;">
                                        <input type="text" id="ticker" name="ticker" class="form-input" placeholder="e.g., RELIANCE.NS" required style="flex: 1;">
                                        <button type="button" id="fetchStock" class="btn" style="margin-left: 10px;">Fetch</button>
                                    </div>
                                    <div style="font-size: 12px; margin-top: 5px;">
                                        Examples: RELIANCE.NS, TCS.NS, INFY.NS
                                    </div>
                                </div>
                            </div>
                            
                            <div class="form-row">
                                <div class="form-group">
                                    <label for="name" class="form-label">Company Name</label>
                                    <input type="text" id="name" name="name" class="form-input" readonly placeholder="Auto-filled after fetching">
                                </div>
                                <div class="form-group">
                                    <label for="price" class="form-label">Current Price (₹)</label>
                                    <input type="text" id="price" name="current_price" class="form-input" readonly placeholder="Auto-filled after fetching">
                                </div>
                            </div>
                            
                            <div class="form-row">
                                <div class="form-group">
                                    <label for="exchange" class="form-label">Exchange</label>
                                    <input type="text" id="exchange" name="exchange" class="form-input" readonly placeholder="Auto-filled after fetching">
                                </div>
                                <div class="form-group">
                                    <label for="symbol" class="form-label">Symbol</label>
                                    <input type="text" id="symbol" name="symbol" class="form-input" readonly placeholder="Auto-filled after fetching">
                                </div>
                            </div>
                            
                            <div class="form-row">
                                <div class="form-group">
                                    <label for="quantity" class="form-label">Quantity</label>
                                    <input type="number" id="quantity" name="quantity" class="form-input" min="1" required>
                                </div>
                                <div class="form-group">
                                    <label for="purchase_price" class="form-label">Purchase Price (₹)</label>
                                    <input type="number" id="purchase_price" name="purchase_price" class="form-input" step="0.01" min="0" required>
                                </div>
                            </div>
                            
                            <button type="submit" class="btn">Add Stock</button>
                            <button type="button" class="btn" style="background-color: #7f8c8d;" onclick="hideAddStockForm()">Cancel</button>
                        </form>
                    </div>
                    
                    <table>
                        <thead>
                            <tr>
                                <th>Ticker</th>
                                <th>Company Name</th>
                                <th>Quantity</th>
                                <th>Purchase Price (₹)</th>
                                <th>Current Price (₹)</th>
                                <th>Value (₹)</th>
                                <th>Gain/Loss</th>
                            </tr>
                        </thead>
                        <tbody>
                            {table_rows}
                        </tbody>
                    </table>
                </div>
            </div>
            
            <script>
                function showAddStockForm() {
                    document.getElementById('addStockForm').style.display = 'block';
                }
                
                function hideAddStockForm() {
                    document.getElementById('addStockForm').style.display = 'none';
                }
                
                document.getElementById('fetchStock').addEventListener('click', function() {
                    const ticker = document.getElementById('ticker').value;
                    if (!ticker) {
                        alert('Please enter a stock ticker');
                        return;
                    }
                    
                    // Show loading state
                    this.textContent = 'Loading...';
                    this.disabled = true;
                    
                    fetch(`/fetch_stock_data?ticker=${ticker}`)
                        .then(response => response.json())
                        .then(data => {
                            if (data.error) {
                                alert(data.error);
                            } else {
                                document.getElementById('name').value = data.name || '';
                                document.getElementById('price').value = data.current_price || '';
                                document.getElementById('exchange').value = data.exchange || '';
                                document.getElementById('symbol').value = data.symbol || ticker;
                            }
                        })
                        .catch(error => {
                            alert('Error fetching stock data: ' + error);
                        })
                        .finally(() => {
                            // Reset button state
                            this.textContent = 'Fetch';
                            this.disabled = false;
                        });
                });
            </script>
        </body>
        </html>
        """
    except Exception as e:
        flash("Authentication failed")
        return redirect(url_for('index'))

@app.route('/fetch_stock_data')
def fetch_stock_data():
    ticker = request.args.get('ticker')
    if not ticker:
        return jsonify({"error": "Ticker is required"})
    
    try:
        # If yfinance is available
        try:
            import yfinance as yf
            stock = yf.Ticker(ticker)
            info = stock.info
            if not info or 'regularMarketPrice' not in info:
                return jsonify({"error": f"Could not find stock data for {ticker}"})
            
            # Get the current price
            current_price = info.get('regularMarketPrice', 0)
            
            # Determine the exchange
            exchange = "NSE" if ticker.endswith(".NS") else "BSE" if ticker.endswith(".BO") else "Unknown"
            
            # Format name properly
            name = info.get('longName', info.get('shortName', ticker))
            
            return jsonify({
                "name": name,
                "current_price": current_price,
                "exchange": exchange,
                "symbol": ticker
            })
        except ImportError:
            # Fallback if yfinance is not available - return dummy data
            price = 1000.0  # Dummy price
            if "RELIANCE" in ticker:
                name = "Reliance Industries Ltd."
                price = 2500.75
            elif "TCS" in ticker:
                name = "Tata Consultancy Services Ltd."
                price = 3400.50
            elif "INFY" in ticker:
                name = "Infosys Ltd."
                price = 1500.25
            else:
                name = f"{ticker} Company"
            
            exchange = "NSE" if ticker.endswith(".NS") else "BSE" if ticker.endswith(".BO") else "Unknown"
            
            return jsonify({
                "name": name,
                "current_price": price,
                "exchange": exchange,
                "symbol": ticker
            })
    except Exception as e:
        return jsonify({"error": f"Error fetching stock data: {str(e)}"})

@app.route('/add_stock', methods=['POST'])
def add_stock():
    token = request.form.get('token')
    if not token:
        flash("Authentication required")
        return redirect(url_for('index'))
    
    try:
        # Verify the token
        user = auth_firebase.get_account_info(token)
        user_id = user['users'][0]['localId']
        
        ticker = request.form.get('ticker')
        name = request.form.get('name')
        current_price = float(request.form.get('current_price', 0))
        purchase_price = float(request.form.get('purchase_price', 0))
        quantity = int(request.form.get('quantity', 0))
        exchange = request.form.get('exchange', 'Unknown')
        symbol = request.form.get('symbol', ticker)
        
        # Format the base ticker (without exchange suffix)
        base_ticker = ticker
        if base_ticker.endswith('.NS') or base_ticker.endswith('.BO'):
            base_ticker = base_ticker.rsplit('.', 1)[0]
        
        # Save to Firebase
        if db:
            stock_data = {
                "name": name,
                "current_price": current_price,
                "purchase_price": purchase_price,
                "quantity": quantity,
                "exchange": exchange,
                "symbol": symbol,
                "last_updated": datetime.now().isoformat()
            }
            
            db.child("users").child(user_id).child("stocks").child(base_ticker).set(stock_data, token)
            flash("Stock added successfully!")
        else:
            flash("Database not available!")
        
        return redirect(url_for('stocks', token=token))
    except Exception as e:
        flash(f"Error adding stock: {str(e)}")
        return redirect(url_for('stocks', token=token))

@app.route('/mutual-funds')
def mutual_funds():
    # Get token from request
    token = request.args.get('token')
    
    if not token:
        flash("Authentication required")
        return redirect(url_for('index'))
    
    try:
        # Verify the token
        user = auth_firebase.get_account_info(token)
        user_id = user['users'][0]['localId']
        
        # Get user's mutual funds (or return empty dict if not found)
        mutual_funds_data = {}
        if db:
            try:
                mutual_funds_data = db.child("users").child(user_id).child("mutual_funds").get(token).val() or {}
            except Exception as e:
                print(f"Error fetching mutual funds: {e}")
        
        # Generate table rows HTML
        table_rows = ""
        for fund_id, fund_data in mutual_funds_data.items():
            name = fund_data.get('name', 'N/A')
            units = fund_data.get('units', 0)
            purchase_nav = float(fund_data.get('purchase_nav', 0))
            current_nav = float(fund_data.get('current_nav', 0))
            value = current_nav * units
            gain_loss = ((current_nav - purchase_nav) / purchase_nav * 100) if purchase_nav > 0 else 0
            
            table_rows += f"""
            <tr>
                <td>{fund_id}</td>
                <td>{name}</td>
                <td>{units}</td>
                <td>{purchase_nav:.2f}</td>
                <td>{current_nav:.2f}</td>
                <td>{value:.2f}</td>
                <td>{gain_loss:.2f}%</td>
            </tr>
            """
        
        # Render the mutual funds page with minimal styling
        return f"""
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Investment Tracker - Mutual Funds</title>
            <style>
                body {{
                    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                    background-color: #f0f2f5;
                    margin: 0;
                    padding: 0;
                }}
                .navbar {{
                    background-color: #2c3e50;
                    color: white;
                    padding: 15px 20px;
                    display: flex;
                    justify-content: space-between;
                    align-items: center;
                }}
                .navbar-brand {{
                    font-size: 24px;
                    font-weight: bold;
                }}
                .navbar-menu {{
                    display: flex;
                    gap: 20px;
                }}
                .navbar-menu a {{
                    color: white;
                    text-decoration: none;
                    padding: 5px 10px;
                }}
                .content {{
                    padding: 20px;
                    max-width: 1200px;
                    margin: 0 auto;
                }}
                .card {{
                    background-color: white;
                    border-radius: 8px;
                    box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
                    padding: 20px;
                    margin-bottom: 20px;
                }}
                .btn {{
                    display: inline-block;
                    background-color: #3498db;
                    color: white;
                    border: none;
                    border-radius: 4px;
                    padding: 10px 15px;
                    cursor: pointer;
                    text-decoration: none;
                }}
                table {{
                    width: 100%;
                    border-collapse: collapse;
                    margin-top: 20px;
                }}
                th, td {{
                    padding: 12px;
                    text-align: left;
                    border-bottom: 1px solid #ddd;
                }}
                th {{
                    background-color: #f8f9fa;
                }}
                .form-group {{
                    margin-bottom: 15px;
                }}
                .form-input {{
                    width: 100%;
                    padding: 10px;
                    border: 1px solid #ddd;
                    border-radius: 4px;
                }}
                .form-row {{
                    display: flex;
                    gap: 15px;
                }}
                .form-row .form-group {{
                    flex: 1;
                }}
            </style>
        </head>
        <body>
            <div class="navbar">
                <div class="navbar-brand">Investment Tracker</div>
                <div class="navbar-menu">
                    <a href="/dashboard?token={token}">Dashboard</a>
                    <a href="/stocks?token={token}">Stocks</a>
                    <a href="/mutual-funds?token={token}">Mutual Funds</a>
                    <a href="/logout">Logout</a>
                </div>
            </div>
            <div class="content">
                <div class="card">
                    <h2>Your Mutual Fund Portfolio</h2>
                    <a href="#" class="btn" onclick="showAddFundForm()">Add New Fund</a>
                    
                    <div id="addFundForm" style="display: none; margin-top: 20px;">
                        <h3>Add a Mutual Fund</h3>
                        <form action="/add_mutual_fund" method="POST">
                            <input type="hidden" name="token" value="{token}">
                            
                            <div class="form-row">
                                <div class="form-group">
                                    <label for="fund_id">Fund ID/Code</label>
                                    <input type="text" id="fund_id" name="fund_id" class="form-input" required>
                                </div>
                            </div>
                            
                            <div class="form-row">
                                <div class="form-group">
                                    <label for="name">Fund Name</label>
                                    <input type="text" id="name" name="name" class="form-input" required>
                                </div>
                            </div>
                            
                            <div class="form-row">
                                <div class="form-group">
                                    <label for="units">Units</label>
                                    <input type="number" id="units" name="units" class="form-input" step="0.001" min="0" required>
                                </div>
                                <div class="form-group">
                                    <label for="purchase_nav">Purchase NAV (₹)</label>
                                    <input type="number" id="purchase_nav" name="purchase_nav" class="form-input" step="0.01" min="0" required>
                                </div>
                            </div>
                            
                            <div class="form-row">
                                <div class="form-group">
                                    <label for="current_nav">Current NAV (₹)</label>
                                    <input type="number" id="current_nav" name="current_nav" class="form-input" step="0.01" min="0" required>
                                </div>
                            </div>
                            
                            <button type="submit" class="btn">Add Fund</button>
                            <button type="button" class="btn" style="background-color: #7f8c8d;" onclick="hideAddFundForm()">Cancel</button>
                        </form>
                    </div>
                    
                    <table>
                        <thead>
                            <tr>
                                <th>Fund ID</th>
                                <th>Fund Name</th>
                                <th>Units</th>
                                <th>Purchase NAV (₹)</th>
                                <th>Current NAV (₹)</th>
                                <th>Value (₹)</th>
                                <th>Gain/Loss</th>
                            </tr>
                        </thead>
                        <tbody>
                            {table_rows}
                        </tbody>
                    </table>
                </div>
            </div>
            
            <script>
                function showAddFundForm() {
                    document.getElementById('addFundForm').style.display = 'block';
                }
                
                function hideAddFundForm() {
                    document.getElementById('addFundForm').style.display = 'none';
                }
            </script>
        </body>
        </html>
        """
    except Exception as e:
        flash("Authentication failed")
        return redirect(url_for('index'))

@app.route('/add_mutual_fund', methods=['POST'])
def add_mutual_fund():
    token = request.form.get('token')
    if not token:
        flash("Authentication required")
        return redirect(url_for('index'))
    
    try:
        # Verify the token
        user = auth_firebase.get_account_info(token)
        user_id = user['users'][0]['localId']
        
        fund_id = request.form.get('fund_id')
        name = request.form.get('name')
        units = float(request.form.get('units', 0))
        purchase_nav = float(request.form.get('purchase_nav', 0))
        current_nav = float(request.form.get('current_nav', 0))
        
        # Save to Firebase
        if db:
            fund_data = {
                "name": name,
                "units": units,
                "purchase_nav": purchase_nav,
                "current_nav": current_nav,
                "last_updated": datetime.now().isoformat()
            }
            
            db.child("users").child(user_id).child("mutual_funds").child(fund_id).set(fund_data, token)
            flash("Mutual fund added successfully!")
        else:
            flash("Database not available!")
        
        return redirect(url_for('mutual_funds', token=token))
    except Exception as e:
        flash(f"Error adding mutual fund: {str(e)}")
        return redirect(url_for('mutual_funds', token=token))

if __name__ == '__main__':
    app.run(debug=True) 