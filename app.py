from flask import Flask, render_template, request, redirect, url_for, jsonify, flash
from dotenv import load_dotenv
import os
import pyrebase
import json
import yfinance as yf
import requests
from datetime import datetime, timedelta
import traceback
import time
import random

# Load environment variables
load_dotenv()

# Initialize Flask app
app = Flask(__name__, 
            template_folder='app/templates',
            static_folder='app/static')

# Use a fixed secret key for production
secret_key = os.getenv("SECRET_KEY")
if not secret_key:
    secret_key = os.urandom(24)
app.secret_key = secret_key

# Check if Firebase environment variables are set
required_env_vars = [
    "FIREBASE_API_KEY",
    "FIREBASE_AUTH_DOMAIN",
    "FIREBASE_PROJECT_ID",
    "FIREBASE_STORAGE_BUCKET",
    "FIREBASE_MESSAGING_SENDER_ID",
    "FIREBASE_APP_ID",
    "FIREBASE_DATABASE_URL"
]

missing_vars = [var for var in required_env_vars if not os.getenv(var)]
if missing_vars:
    print(f"ERROR: Missing required environment variables: {', '.join(missing_vars)}")
    print("Please set these variables in your Vercel project settings.")

# Firebase configuration
firebase_config = {
    "apiKey": os.getenv("FIREBASE_API_KEY"),
    "authDomain": os.getenv("FIREBASE_AUTH_DOMAIN"),
    "projectId": os.getenv("FIREBASE_PROJECT_ID"),
    "storageBucket": os.getenv("FIREBASE_STORAGE_BUCKET"),
    "messagingSenderId": os.getenv("FIREBASE_MESSAGING_SENDER_ID"),
    "appId": os.getenv("FIREBASE_APP_ID"),
    "databaseURL": os.getenv("FIREBASE_DATABASE_URL")
}

# Initialize Firebase
firebase = pyrebase.initialize_app(firebase_config)
auth_firebase = firebase.auth()
db = firebase.database()

# Cache for stock data to reduce API calls
stock_cache = {}
CACHE_DURATION = 3600  # Cache duration in seconds (1 hour)

# Function to get stock data with caching and rate limiting
def get_stock_data(ticker):
    # Clean the ticker input
    ticker = ticker.strip().upper()
    
    # Check if data is in cache and not expired
    current_time = datetime.now()
    if ticker in stock_cache:
        cache_time, cache_data = stock_cache[ticker]
        if (current_time - cache_time).total_seconds() < CACHE_DURATION:
            return cache_data
    
    # Remove any existing suffixes
    if ticker.endswith('.NS') or ticker.endswith('.BO'):
        base_ticker = ticker[:-3]
    else:
        base_ticker = ticker
    
    # Add a small random delay to avoid rate limiting (0.5 to 2 seconds)
    time.sleep(random.uniform(0.5, 2))
    
    # Try NSE first
    nse_ticker = f"{base_ticker}.NS"
    try:
        # Use a more reliable method to get current price
        stock = yf.Ticker(nse_ticker)
        
        # Try multiple methods to get the price
        price = None
        name = None
        
        # Method 1: Try getting from recent history
        try:
            hist = stock.history(period="1d")
            if not hist.empty and 'Close' in hist.columns:
                price = float(hist['Close'].iloc[-1])
        except Exception as e:
            print(f"NSE history error: {str(e)}")
        
        # Method 2: Try getting from quote
        if price is None:
            try:
                todays_data = stock.info
                price = float(todays_data.get('regularMarketPrice', 0))
                if price == 0:
                    price = float(todays_data.get('previousClose', 0))
            except Exception as e:
                print(f"NSE quote error: {str(e)}")
        
        # Get company name
        try:
            info = stock.info
            name = info.get('shortName', info.get('longName', nse_ticker))
        except Exception as e:
            print(f"NSE name error: {str(e)}")
            name = nse_ticker
        
        # If we found a valid price, cache and return the data
        if price and price > 0:
            result = {
                'name': name,
                'current_price': price,
                'exchange': 'NSE',
                'symbol': nse_ticker
            }
            stock_cache[ticker] = (current_time, result)
            return result
    except Exception as e:
        print(f"NSE overall error: {str(e)}")
    
    # Add another small delay before trying BSE
    time.sleep(random.uniform(0.5, 2))
    
    # If NSE fails, try BSE
    bse_ticker = f"{base_ticker}.BO"
    try:
        stock = yf.Ticker(bse_ticker)
        
        # Try multiple methods to get the price
        price = None
        name = None
        
        # Method 1: Try getting from recent history
        try:
            hist = stock.history(period="1d")
            if not hist.empty and 'Close' in hist.columns:
                price = float(hist['Close'].iloc[-1])
        except Exception as e:
            print(f"BSE history error: {str(e)}")
        
        # Method 2: Try getting from quote
        if price is None:
            try:
                todays_data = stock.info
                price = float(todays_data.get('regularMarketPrice', 0))
                if price == 0:
                    price = float(todays_data.get('previousClose', 0))
            except Exception as e:
                print(f"BSE quote error: {str(e)}")
        
        # Get company name
        try:
            info = stock.info
            name = info.get('shortName', info.get('longName', bse_ticker))
        except Exception as e:
            print(f"BSE name error: {str(e)}")
            name = bse_ticker
        
        # If we found a valid price, cache and return the data
        if price and price > 0:
            result = {
                'name': name,
                'current_price': price,
                'exchange': 'BSE',
                'symbol': bse_ticker
            }
            stock_cache[ticker] = (current_time, result)
            return result
    except Exception as e:
        print(f"BSE overall error: {str(e)}")
    
    # Add another small delay before trying direct API
    time.sleep(random.uniform(0.5, 2))
    
    # If both fail, try a direct approach for well-known Indian stocks
    try:
        # Try to get data from an alternative source - Yahoo Finance direct API
        url = f"https://query1.finance.yahoo.com/v8/finance/chart/{base_ticker}.NS?interval=1d"
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            data = response.json()
            if 'chart' in data and 'result' in data['chart'] and data['chart']['result']:
                result = data['chart']['result'][0]
                if 'meta' in result and 'regularMarketPrice' in result['meta']:
                    price = float(result['meta']['regularMarketPrice'])
                    name = base_ticker
                    if 'shortName' in result['meta']:
                        name = result['meta']['shortName']
                    
                    result = {
                        'name': name,
                        'current_price': price,
                        'exchange': 'NSE',
                        'symbol': f"{base_ticker}.NS"
                    }
                    stock_cache[ticker] = (current_time, result)
                    return result
    except Exception as e:
        print(f"Direct Yahoo API error: {str(e)}")
    
    # Try alternative API for Indian stocks
    try:
        # Using a different endpoint that might be less rate-limited
        url = f"https://query2.finance.yahoo.com/v7/finance/options/{base_ticker}.NS"
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            data = response.json()
            if 'optionChain' in data and 'result' in data['optionChain'] and data['optionChain']['result']:
                result = data['optionChain']['result'][0]
                if 'quote' in result:
                    quote = result['quote']
                    price = float(quote.get('regularMarketPrice', 0))
                    name = quote.get('shortName', quote.get('longName', base_ticker))
                    
                    if price and price > 0:
                        result = {
                            'name': name,
                            'current_price': price,
                            'exchange': 'NSE',
                            'symbol': f"{base_ticker}.NS"
                        }
                        stock_cache[ticker] = (current_time, result)
                        return result
    except Exception as e:
        print(f"Alternative API error: {str(e)}")
    
    # If everything fails, use default values but still cache to avoid hammering APIs
    result = {
        'name': base_ticker,
        'current_price': 0,
        'exchange': 'Unknown',
        'symbol': base_ticker
    }
    stock_cache[ticker] = (current_time, result)
    return result

# Routes
@app.route('/')
def index():
    return render_template('login.html')

@app.route('/login', methods=['POST'])
def login():
    email = request.form.get('email')
    password = request.form.get('password')
    try:
        user = auth_firebase.sign_in_with_email_and_password(email, password)
        user_id = user['localId']
        id_token = user['idToken']
        # Return token to client for future requests
        return redirect(url_for('dashboard', token=id_token))
    except Exception as e:
        error_message = json.loads(e.args[1])['error']['message']
        flash(f"Login failed: {error_message}")
        return redirect(url_for('index'))

@app.route('/dashboard')
def dashboard():
    token = request.args.get('token')
    if not token:
        return redirect(url_for('index'))
    
    try:
        # Verify the token
        user = auth_firebase.get_account_info(token)
        user_id = user['users'][0]['localId']
        
        # Get user's stocks from Firebase
        user_stocks = db.child("users").child(user_id).child("stocks").get(token=token).val() or {}
        
        # Get updated stock information
        stock_data = {}
        
        # Process a limited number of stocks at a time to avoid rate limiting
        # For dashboard, use cached data more aggressively
        stock_count = 0
        max_stocks_to_update = 3  # Limit updates to avoid rate limiting
        
        for ticker, details in user_stocks.items():
            try:
                # Check if we should update this stock or use existing data
                should_update = stock_count < max_stocks_to_update
                
                if should_update:
                    # Use the stored symbol if available
                    symbol_to_use = details.get('symbol', ticker)
                    
                    # Get current stock data
                    stock_info = get_stock_data(symbol_to_use)
                    stock_count += 1
                    
                    # Update stock data
                    stock_data[ticker] = {
                        'name': details.get('name', stock_info['name']),
                        'current_price': stock_info['current_price'],
                        'quantity': details.get('quantity', 0),
                        'purchase_price': details.get('purchase_price', 0),
                        'exchange': details.get('exchange', stock_info['exchange']),
                        'symbol': details.get('symbol', symbol_to_use)
                    }
                else:
                    # Use existing data for remaining stocks
                    stock_data[ticker] = {
                        'name': details.get('name', ticker),
                        'current_price': details.get('current_price', 0),
                        'quantity': details.get('quantity', 0),
                        'purchase_price': details.get('purchase_price', 0),
                        'exchange': details.get('exchange', 'Unknown'),
                        'symbol': details.get('symbol', ticker)
                    }
            except Exception as e:
                # Use existing data if fetch fails
                stock_data[ticker] = {
                    'name': details.get('name', ticker),
                    'current_price': details.get('current_price', 0),
                    'quantity': details.get('quantity', 0),
                    'purchase_price': details.get('purchase_price', 0),
                    'exchange': details.get('exchange', 'Unknown'),
                    'symbol': details.get('symbol', ticker)
                }
        
        # Get user's mutual funds from Firebase
        mutual_funds = db.child("users").child(user_id).child("mutual_funds").get(token=token).val() or {}
        
        return render_template('dashboard.html', 
                              stocks=stock_data, 
                              mutual_funds=mutual_funds,
                              token=token)
    except Exception as e:
        return redirect(url_for('index'))

@app.route('/stocks')
def stocks():
    token = request.args.get('token')
    if not token:
        return redirect(url_for('index'))
    
    try:
        # Verify the token
        user = auth_firebase.get_account_info(token)
        user_id = user['users'][0]['localId']
        
        # Get user's stocks from Firebase
        user_stocks = db.child("users").child(user_id).child("stocks").get(token=token).val() or {}
        
        # Get updated stock information
        stock_data = {}
        
        # Process stocks one by one to avoid rate limiting
        # We'll update at most 5 stocks per page load
        stock_count = 0
        max_stocks_to_update = 5
        
        for ticker, details in user_stocks.items():
            try:
                # Check if we should update this stock or use existing data
                should_update = stock_count < max_stocks_to_update
                
                if should_update:
                    # Use the stored symbol if available
                    symbol_to_use = details.get('symbol', ticker)
                    
                    # Get current stock data
                    stock_info = get_stock_data(symbol_to_use)
                    stock_count += 1
                    
                    stock_data[ticker] = {
                        'name': details.get('name', stock_info['name']),
                        'current_price': stock_info['current_price'],
                        'quantity': details.get('quantity', 0),
                        'purchase_price': details.get('purchase_price', 0),
                        'exchange': details.get('exchange', stock_info['exchange']),
                        'symbol': details.get('symbol', symbol_to_use)
                    }
                else:
                    # Use existing data for remaining stocks
                    stock_data[ticker] = {
                        'name': details.get('name', ticker),
                        'current_price': details.get('current_price', 0),
                        'quantity': details.get('quantity', 0),
                        'purchase_price': details.get('purchase_price', 0),
                        'exchange': details.get('exchange', 'Unknown'),
                        'symbol': details.get('symbol', ticker)
                    }
            except Exception as e:
                # Use existing data if fetch fails
                stock_data[ticker] = {
                    'name': details.get('name', ticker),
                    'current_price': details.get('current_price', 0),
                    'quantity': details.get('quantity', 0),
                    'purchase_price': details.get('purchase_price', 0),
                    'exchange': details.get('exchange', 'Unknown'),
                    'symbol': details.get('symbol', ticker)
                }
        
        return render_template('stocks.html', stocks=stock_data, token=token)
    except Exception as e:
        return redirect(url_for('index'))

@app.route('/get_stock_info', methods=['POST'])
def get_stock_info():
    ticker = request.form.get('ticker')
    if not ticker:
        return jsonify({'error': 'No ticker provided'})
    
    try:
        print(f"Fetching stock info for: {ticker}")
        stock_info = get_stock_data(ticker)
        print(f"Stock info result: {stock_info}")
        return jsonify(stock_info)
    except Exception as e:
        print(f"Error in get_stock_info route: {str(e)}")
        traceback.print_exc()
        return jsonify({'error': f"Failed to fetch stock information: {str(e)}"})

@app.route('/add_stock', methods=['POST'])
def add_stock():
    token = request.form.get('token')
    if not token:
        return redirect(url_for('index'))
    
    try:
        # Verify the token
        user = auth_firebase.get_account_info(token)
        user_id = user['users'][0]['localId']
        
        ticker = request.form.get('ticker')
        symbol = request.form.get('symbol')  # Get the full symbol including exchange suffix
        quantity = float(request.form.get('quantity'))
        purchase_price = float(request.form.get('purchase_price'))
        
        # Use the symbol if provided, otherwise use ticker
        stock_ticker = symbol if symbol else ticker
        
        # Get stock info using the helper function
        stock_info = get_stock_data(stock_ticker)
        
        if stock_info['current_price'] == 0:
            flash(f"Error: Could not find stock information for {ticker}")
            return redirect(url_for('stocks', token=token))
            
        # Save to Firebase
        stock_data = {
            'name': stock_info['name'],
            'quantity': quantity,
            'purchase_price': purchase_price,
            'exchange': stock_info['exchange'],
            'symbol': stock_info['symbol']
        }
        
        # Use the base ticker (without .NS or .BO) as the key
        base_ticker = ticker.strip().upper()
        if base_ticker.endswith('.NS') or base_ticker.endswith('.BO'):
            base_ticker = base_ticker[:-3]
            
        db.child("users").child(user_id).child("stocks").child(base_ticker).set(stock_data, token=token)
        
        flash(f"Stock {stock_info['name']} added successfully!")
        return redirect(url_for('stocks', token=token))
    except Exception as e:
        flash(f"Error adding stock: {str(e)}")
        return redirect(url_for('stocks', token=token))

@app.route('/mutual_funds')
def mutual_funds():
    token = request.args.get('token')
    if not token:
        return redirect(url_for('index'))
    
    try:
        # Verify the token
        user = auth_firebase.get_account_info(token)
        user_id = user['users'][0]['localId']
        
        # Get user's mutual funds from Firebase
        user_funds = db.child("users").child(user_id).child("mutual_funds").get(token=token).val() or {}
        
        # Get updated mutual fund information
        fund_data = {}
        for scheme_code, details in user_funds.items():
            try:
                response = requests.get(f"https://api.mfapi.in/mf/{scheme_code}")
                if response.status_code == 200:
                    fund_info = response.json()
                    scheme_name = fund_info.get('meta', {}).get('scheme_name', f"Fund {scheme_code}")
                    current_nav = float(fund_info.get('data', [{}])[0].get('nav', 0))
                    
                    fund_data[scheme_code] = {
                        'name': scheme_name,
                        'current_nav': current_nav,
                        'units': details.get('units', 0),
                        'purchase_nav': details.get('purchase_nav', 0)
                    }
                else:
                    fund_data[scheme_code] = details
            except Exception as e:
                fund_data[scheme_code] = {
                    'name': f"Fund {scheme_code}",
                    'current_nav': 0,
                    'units': details.get('units', 0),
                    'purchase_nav': details.get('purchase_nav', 0),
                    'error': str(e)
                }
        
        return render_template('mutual_funds.html', funds=fund_data, token=token)
    except Exception as e:
        return redirect(url_for('index'))

@app.route('/add_mutual_fund', methods=['POST'])
def add_mutual_fund():
    token = request.form.get('token')
    if not token:
        return redirect(url_for('index'))
    
    try:
        # Verify the token
        user = auth_firebase.get_account_info(token)
        user_id = user['users'][0]['localId']
        
        scheme_code = request.form.get('scheme_code')
        units = float(request.form.get('units'))
        purchase_nav = float(request.form.get('purchase_nav'))
        
        # Verify mutual fund exists
        response = requests.get(f"https://api.mfapi.in/mf/{scheme_code}")
        if response.status_code == 200:
            fund_info = response.json()
            scheme_name = fund_info.get('meta', {}).get('scheme_name', f"Fund {scheme_code}")
            
            # Save to Firebase
            fund_data = {
                'name': scheme_name,
                'units': units,
                'purchase_nav': purchase_nav
            }
            
            db.child("users").child(user_id).child("mutual_funds").child(scheme_code).set(fund_data, token=token)
            
            return redirect(url_for('mutual_funds', token=token))
        else:
            flash(f"Error: Mutual fund scheme code {scheme_code} not found")
            return redirect(url_for('mutual_funds', token=token))
    except Exception as e:
        flash(f"Error adding mutual fund: {str(e)}")
        return redirect(url_for('mutual_funds', token=token))

@app.route('/logout')
def logout():
    return redirect(url_for('index'))

@app.route('/api/fetch_stock_data', methods=['POST'])
def fetch_stock_data():
    ticker = request.form.get('ticker', '').strip()
    if not ticker:
        return jsonify({'error': 'No ticker provided'}), 400
    
    try:
        # Check if we've made too many API calls recently (basic rate limiting)
        current_time = datetime.now()
        last_api_call = getattr(app, 'last_api_call', None)
        
        # If we made an API call in the last 3 seconds, return a rate limit message
        if last_api_call and (current_time - last_api_call).total_seconds() < 3:
            return jsonify({
                'error': 'Rate limit exceeded. Please try again in a few seconds.'
            }), 429
        
        # Update the last API call time
        app.last_api_call = current_time
        
        # Get stock data
        stock_data = get_stock_data(ticker)
        
        if stock_data['current_price'] == 0:
            return jsonify({
                'error': f"Could not fetch data for {ticker}. Please verify the ticker symbol."
            }), 404
        
        return jsonify({
            'success': True,
            'data': stock_data
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True) 