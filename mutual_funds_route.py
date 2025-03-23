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
        
        # Render the mutual funds page
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
                    <h2 class="card-title">Your Mutual Fund Portfolio</h2>
                    <a href="#" class="btn" onclick="showAddFundForm()">Add New Fund</a>
                    
                    <div id="addFundForm" style="display: none; margin-top: 20px;">
                        <h3>Add a Mutual Fund</h3>
                        <form action="/add_mutual_fund" method="POST">
                            <input type="hidden" name="token" value="{token}">
                            
                            <div class="form-row">
                                <div class="form-group">
                                    <label for="fund_id" class="form-label">Fund ID/Code</label>
                                    <input type="text" id="fund_id" name="fund_id" class="form-input" placeholder="e.g., HDFC123456" required>
                                </div>
                            </div>
                            
                            <div class="form-row">
                                <div class="form-group">
                                    <label for="name" class="form-label">Fund Name</label>
                                    <input type="text" id="name" name="name" class="form-input" placeholder="e.g., HDFC Top 100 Fund" required>
                                </div>
                            </div>
                            
                            <div class="form-row">
                                <div class="form-group">
                                    <label for="units" class="form-label">Units</label>
                                    <input type="number" id="units" name="units" class="form-input" step="0.001" min="0" required>
                                </div>
                                <div class="form-group">
                                    <label for="purchase_nav" class="form-label">Purchase NAV (₹)</label>
                                    <input type="number" id="purchase_nav" name="purchase_nav" class="form-input" step="0.01" min="0" required>
                                </div>
                            </div>
                            
                            <div class="form-row">
                                <div class="form-group">
                                    <label for="current_nav" class="form-label">Current NAV (₹)</label>
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