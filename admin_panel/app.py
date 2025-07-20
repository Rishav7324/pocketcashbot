from flask import Flask, render_template, request, redirect, url_for, flash, Response
from flask_bcrypt import Bcrypt
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
import json
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import pandas as pd
import io
import time
from main import bot as telegram_bot

# --- App Setup ---
app = Flask(__name__)
app.config['SECRET_KEY'] = 'a_very_secret_key_that_should_be_changed'
bcrypt = Bcrypt(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'
login_manager.login_message_category = 'info'

# --- Google Sheets Setup ---
try:
    scope = ["https://spreadsheets.google.com/feeds", 'https://www.googleapis.com/auth/spreadsheets',
             "https://www.googleapis.com/auth/drive.file", "https://www.googleapis.com/auth/drive"]
    creds = ServiceAccountCredentials.from_json_keyfile_name("tenant-3c5c7-167f5774acd0.json", scope)
    client = gspread.authorize(creds)
    user_sheet = client.open("PocketCashBotDB").worksheet("Users")
    print("Google Sheets connected successfully for Admin Panel.")
except Exception as e:
    print(f"Error connecting to Google Sheets for Admin Panel: {e}")
    user_sheet = None

# --- User Model ---
class User(UserMixin):
    def __init__(self, id, username, password):
        self.id = id
        self.username = username
        self.password = password

def get_user_by_username(username):
    with open('admin_panel/users.json', 'r') as f:
        users = json.load(f)
    if username in users:
        user_data = users[username]
        return User(id=username, username=username, password=user_data['password'])
    return None

@login_manager.user_loader
def load_user(user_id):
    with open('admin_panel/users.json', 'r') as f:
        users = json.load(f)
    if user_id in users:
        return User(id=user_id, username=user_id, password=users[user_id]['password'])
    return None

# --- Routes ---
@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        user = get_user_by_username(username)
        
        if user and bcrypt.check_password_hash(user.password, password):
            login_user(user)
            flash('Login successful!', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('Login Unsuccessful. Please check username and password', 'danger')
            
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('login'))

# --- Helper Functions for Offer Management ---
def get_all_offers():
    try:
        with open('admin_panel/offers.json', 'r') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return []

def save_all_offers(offers):
    with open('admin_panel/offers.json', 'w') as f:
        json.dump(offers, f, indent=4)

def get_offer_by_id(offer_id):
    offers = get_all_offers()
    for offer in offers:
        if offer['id'] == offer_id:
            return offer
    return None

# --- Main Routes ---
@app.route('/')
@app.route('/dashboard')
@login_required
def dashboard():
    # Update the dashboard to link to the new pages
    return render_template('dashboard.html', username=current_user.username)

# --- Withdrawal Management Routes ---
@app.route('/withdrawals')
@login_required
def manage_withdrawals():
    if not user_sheet: # Re-using user_sheet to check connection
        flash('Google Sheets not connected. Cannot fetch withdrawals.', 'danger')
        return render_template('withdrawals.html', requests=[])

    # This assumes withdrawal_sheet is available from the initial setup
    withdrawal_sheet = client.open("PocketCashBotDB").worksheet("Withdrawals")
    requests = withdrawal_sheet.get_all_records()
    
    return render_template('withdrawals.html', requests=requests)

@app.route('/withdrawals/update/<int:row_id>/<string:status>', methods=['POST'])
@login_required
def update_withdrawal_status(row_id, status):
    if not user_sheet: # Re-using user_sheet to check connection
        flash('Google Sheets not connected.', 'danger')
        return redirect(url_for('manage_withdrawals'))

    try:
        withdrawal_sheet = client.open("PocketCashBotDB").worksheet("Withdrawals")
        # Column G (7) is the Status column
        withdrawal_sheet.update_cell(row_id, 7, status.upper())
        flash(f'Request #{row_id} has been marked as {status.upper()}.', 'success')
    except Exception as e:
        flash(f'An error occurred: {e}', 'danger')
        
    return redirect(url_for('manage_withdrawals'))

# --- User Management Routes ---
@app.route('/users')
@login_required
def manage_users():
    if not user_sheet:
        flash('Google Sheets not connected. Cannot fetch users.', 'danger')
        return render_template('users.html', users=[])

    users = user_sheet.get_all_records()
    
    search_query = request.args.get('search', '').lower()
    if search_query:
        users = [
            user for user in users if
            search_query in str(user.get('UserID', '')).lower() or
            search_query in str(user.get('Username', '')).lower()
        ]

    return render_template('users.html', users=users, search_query=search_query)

@app.route('/users/toggle_block/<string:user_id>', methods=['POST'])
@login_required
def toggle_block_user(user_id):
    if not user_sheet:
        flash('Google Sheets not connected.', 'danger')
        return redirect(url_for('manage_users'))
        
    try:
        cell = user_sheet.find(user_id)
        if cell:
            current_status = user_sheet.cell(cell.row, 8).value # Column H for Status
            new_status = "blocked" if current_status == "active" else "active"
            user_sheet.update_cell(cell.row, 8, new_status)
            flash(f'User {user_id} has been {new_status}.', 'success')
        else:
            flash('User not found.', 'danger')
    except Exception as e:
        flash(f'An error occurred: {e}', 'danger')
        
    return redirect(url_for('manage_users'))

@app.route('/users/export')
@login_required
def export_users():
    if not user_sheet:
        flash('Google Sheets not connected.', 'danger')
        return redirect(url_for('manage_users'))
        
    users = user_sheet.get_all_records()
    df = pd.DataFrame(users)
    
    output = io.StringIO()
    df.to_csv(output, index=False)
    output.seek(0)
    
    return Response(
        output,
        mimetype="text/csv",
        headers={"Content-Disposition": "attachment;filename=users.csv"}
    )

@app.route('/users/add_bonus/<string:user_id>', methods=['POST'])
@login_required
def add_bonus(user_id):
    if not user_sheet:
        flash('Google Sheets not connected.', 'danger')
        return redirect(url_for('manage_users'))
        
    try:
        bonus_amount = float(request.form.get('bonus_amount', 0))
        if bonus_amount <= 0:
            flash('Bonus amount must be positive.', 'danger')
            return redirect(url_for('manage_users'))

        cell = user_sheet.find(user_id)
        if cell:
            # Column E (5) is Balance
            current_balance = float(user_sheet.cell(cell.row, 5).value)
            new_balance = current_balance + bonus_amount
            user_sheet.update_cell(cell.row, 5, new_balance)
            flash(f'Added ₹{bonus_amount} bonus to user {user_id}. New balance is ₹{new_balance}.', 'success')
        else:
            flash('User not found.', 'danger')
    except Exception as e:
        flash(f'An error occurred: {e}', 'danger')
        
    return redirect(url_for('manage_users'))

# --- Settings Management ---
def get_settings():
    try:
        with open('admin_panel/settings.json', 'r') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {"min_withdrawal": 500, "referral_bonus": 10}

def save_settings(settings_data):
    with open('admin_panel/settings.json', 'w') as f:
        json.dump(settings_data, f, indent=4)

@app.route('/settings', methods=['GET', 'POST'])
@login_required
def manage_settings():
    if request.method == 'POST':
        if 'new_password' in request.form:
            # Handle password change
            new_password = request.form['new_password']
            if len(new_password) < 6:
                flash('Password must be at least 6 characters long.', 'danger')
            else:
                hashed_password = bcrypt.generate_password_hash(new_password).decode('utf-8')
                with open('admin_panel/users.json', 'r+') as f:
                    users = json.load(f)
                    users[current_user.id]['password'] = hashed_password
                    f.seek(0)
                    json.dump(users, f, indent=4)
                flash('Password updated successfully!', 'success')

        else:
            # Handle settings change
            settings = get_settings()
            settings['min_withdrawal'] = int(request.form['min_withdrawal'])
            settings['referral_bonus'] = int(request.form['referral_bonus'])
            settings['referral_system_enabled'] = True if request.form.get('referral_system_enabled') == 'on' else False
            save_settings(settings)
            flash('Settings updated successfully!', 'success')
            
        return redirect(url_for('manage_settings'))

    settings = get_settings()
    return render_template('settings.html', settings=settings)

# --- Referral Tree ---
@app.route('/referral-tree')
@login_required
def referral_tree():
    if not user_sheet:
        flash('Google Sheets not connected.', 'danger')
        return render_template('referral_tree.html', tree={})

    try:
        users = user_sheet.get_all_records()
        
        # Create a dictionary of users for easy lookup
        users_by_id = {str(u['UserID']): u for u in users}
        
        # Build the tree
        tree = {}
        for user_id, user_data in users_by_id.items():
            user_data['children'] = []
            parent_id = str(user_data.get('InvitedBy'))
            
            if parent_id and parent_id in users_by_id:
                # This is a hacky way to append to a list within a dict
                # A proper DB would be better.
                parent = users_by_id[parent_id]
                if 'children' not in parent:
                    parent['children'] = []
                parent['children'].append(user_data)
            else:
                # This is a root node (no referrer or invalid referrer)
                tree[user_id] = user_data

    except Exception as e:
        flash(f'An error occurred while building the tree: {e}', 'danger')
        tree = {}

    return render_template('referral_tree.html', tree=tree)


# --- Broadcast System ---
@app.route('/broadcast', methods=['GET', 'POST'])
@login_required
def broadcast():
    if request.method == 'POST':
        message_text = request.form.get('message')
        target_group = request.form.get('target_group')

        if not message_text:
            flash('Message cannot be empty.', 'danger')
            return redirect(url_for('broadcast'))

        if not user_sheet:
            flash('Google Sheets not connected.', 'danger')
            return redirect(url_for('broadcast'))

        try:
            users = user_sheet.get_all_records()
            target_users = []
            if target_group == 'all':
                target_users = users
            elif target_group == 'active':
                target_users = [u for u in users if u.get('Status') == 'active']
            elif target_group == 'blocked':
                target_users = [u for u in users if u.get('Status') == 'blocked']

            sent_count = 0
            for user in target_users:
                try:
                    telegram_bot.send_message(user['UserID'], message_text)
                    sent_count += 1
                    time.sleep(0.1) # To avoid hitting rate limits
                except Exception as e:
                    print(f"Failed to send message to {user['UserID']}: {e}")
            
            flash(f'Broadcast sent to {sent_count} out of {len(target_users)} users.', 'success')

        except Exception as e:
            flash(f'An error occurred during broadcast: {e}', 'danger')

        return redirect(url_for('broadcast'))

    return render_template('broadcast.html')

# --- Offer Management Routes ---
@app.route('/offers')
@login_required
def manage_offers():
    offers = get_all_offers()
    return render_template('offers.html', offers=offers)

@app.route('/offers/add', methods=['GET', 'POST'])
@login_required
def add_offer():
    if request.method == 'POST':
        offers = get_all_offers()
        new_id = max([offer['id'] for offer in offers]) + 1 if offers else 1
        new_offer = {
            "id": new_id,
            "title": request.form['title'],
            "description": request.form['description'],
            "link": request.form['link'],
            "category": request.form['category'],
            "reward": float(request.form['reward']),
            "status": request.form['status']
        }
        offers.append(new_offer)
        save_all_offers(offers)
        flash('Offer added successfully!', 'success')
        return redirect(url_for('manage_offers'))
    
    return render_template('offer_form.html', title="Add New Offer")

@app.route('/offers/edit/<int:offer_id>', methods=['GET', 'POST'])
@login_required
def edit_offer(offer_id):
    offer = get_offer_by_id(offer_id)
    if not offer:
        flash('Offer not found.', 'danger')
        return redirect(url_for('manage_offers'))

    if request.method == 'POST':
        offers = get_all_offers()
        for i, o in enumerate(offers):
            if o['id'] == offer_id:
                offers[i] = {
                    "id": offer_id,
                    "title": request.form['title'],
                    "description": request.form['description'],
                    "link": request.form['link'],
                    "category": request.form['category'],
                    "reward": float(request.form['reward']),
                    "status": request.form['status']
                }
                break
        save_all_offers(offers)
        flash('Offer updated successfully!', 'success')
        return redirect(url_for('manage_offers'))

    return render_template('offer_form.html', title="Edit Offer", offer=offer)

@app.route('/offers/delete/<int:offer_id>', methods=['POST'])
@login_required
def delete_offer(offer_id):
    offers = get_all_offers()
    offers = [offer for offer in offers if offer['id'] != offer_id]
    save_all_offers(offers)
    flash('Offer deleted successfully!', 'success')
    return redirect(url_for('manage_offers'))


if __name__ == '__main__':
    # Note: This will run the admin panel on a different port than the bot
    app.run(debug=True, port=5001)
