import telebot
import random
import gspread
import pandas as pd
import io
from flask import Flask
from threading import Thread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
import json

# ----------------- SETTINGS -----------------
def get_settings():
    try:
        with open('admin_panel/settings.json', 'r') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {"min_withdrawal": 500, "referral_bonus": 10}

# ----------------- KEEP-ALIVE (FOR REPLIT) -----------------
app = Flask('')

@app.route('/')
def home():
    return "I'm alive"

def run():
  app.run(host='0.0.0.0',port=8080)

def keep_alive():
    t = Thread(target=run)
    t.start()

# ----------------- BOT CONFIGURATION -----------------
BOT_TOKEN = "8019925796:AAHgnzy5JtkZujwB370woBsNnmBczE2hpx8"
ADMIN_ID = 6565013470
bot = telebot.TeleBot(BOT_TOKEN)

# ----------------- GOOGLE SHEETS CONFIGURATION -----------------
try:
    scope = ["https://spreadsheets.google.com/feeds", 'https://www.googleapis.com/auth/spreadsheets',
             "https://www.googleapis.com/auth/drive.file", "https://www.googleapis.com/auth/drive"]
    creds = ServiceAccountCredentials.from_json_keyfile_name("tenant-3c5c7-167f5774acd0.json", scope)
    client = gspread.authorize(creds)
    db = client.open("PocketCashBotDB")
    user_sheet = db.worksheet("Users")
    click_sheet = db.worksheet("Clicks")
    withdrawal_sheet = db.worksheet("Withdrawals")
    print("Google Sheets connected successfully.")
except Exception as e:
    print(f"Error connecting to Google Sheets: {e}")
    user_sheet = None
    click_sheet = None
    withdrawal_sheet = None

# -----------------  OFFERS (TEMPORARY) -----------------
OFFERS = [
    {"text": "Open Demat Account & Earn ₹300", "link": "https://example.com/demat"},
    {"text": "Apply for Credit Card & Get ₹500", "link": "https://example.com/creditcard"},
    {"text": "Buy Term Insurance & Earn ₹400", "link": "https://example.com/insurance"},
    {"text": "Signup on App & Get ₹100", "link": "https://example.com/app-signup"},
    {"text": "Complete a Survey & Earn ₹50", "link": "https://example.com/survey"},
]

# ----------------- KEYBOARD MARKUPS -----------------
def create_offer_markup(offer_text, offer_link):
    """Creates an inline keyboard for an offer."""
    markup = InlineKeyboardMarkup()
    markup.row_width = 2
    # The callback_data is now structured to handle clicks
    callback_data = f"click_{offer_text}|{offer_link}"
    markup.add(
        InlineKeyboardButton("✅ Accept & Get Link", callback_data=callback_data),
        InlineKeyboardButton("🔄 Refresh", callback_data="refresh_offer")
    )
    return markup

# ----------------- BOT COMMAND HANDLERS -----------------
def update_sheet_cell(sheet, row, col, value):
    """Updates a specific cell in the given Google Sheet."""
    try:
        sheet.update_cell(row, col, value)
    except Exception as e:
        print(f"Error updating sheet cell ({row}, {col}): {e}")

@bot.message_handler(commands=['start'])
def send_welcome(message):
    """Handles the /start command, registers new user, and processes referrals."""
    user_id = message.from_user.id
    
    if user_sheet:
        try:
            # Check if user already exists
            user_cell = user_sheet.find(str(user_id))
            if user_cell is None:
                # New user registration
                referrer_id = None
                parts = message.text.split()
                if len(parts) > 1:
                    referrer_id = parts[1]

                # Add new user to the sheet
                user_info = [
                    str(user_id),
                    message.from_user.first_name,
                    message.from_user.username,
                    datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    0,  # Initial Balance
                    0,  # Referral Count
                    referrer_id if referrer_id else "",  # Invited By
                    "active" # Status
                ]
                user_sheet.append_row(user_info)
                
                # Notify admin about new user
                admin_message = f"🎉 New User Alert! 🎉\n\nID: {user_id}\nName: {message.from_user.first_name}\nUsername: @{message.from_user.username}"
                if referrer_id:
                    admin_message += f"\nInvited by: {referrer_id}"
                bot.send_message(ADMIN_ID, admin_message)

                # Process referral
                settings = get_settings()
                if referrer_id and settings.get('referral_system_enabled', True):
                    referrer_cell = user_sheet.find(referrer_id)
                    if referrer_cell:
                        # Update referrer's balance
                        settings = get_settings()
                        current_balance = float(user_sheet.cell(referrer_cell.row, 5).value)
                        new_balance = current_balance + settings.get('referral_bonus', 10)
                        update_sheet_cell(user_sheet, referrer_cell.row, 5, new_balance)

                        # Update referrer's referral count
                        current_ref_count = int(user_sheet.cell(referrer_cell.row, 6).value)
                        new_ref_count = current_ref_count + 1
                        update_sheet_cell(user_sheet, referrer_cell.row, 6, new_ref_count)
                        
                        # Notify referrer
                        bot.send_message(referrer_id, f"🎉 You've earned ₹10 for referring a new user! Your new balance is ₹{new_balance}.")

        except Exception as e:
            print(f"Error processing new user in Google Sheets: {e}")

    send_random_offer(message.chat.id)

def send_random_offer(chat_id):
    """Sends a random offer to the user."""
    offer = random.choice(OFFERS)
    markup = create_offer_markup(offer["text"], offer["link"])
    bot.send_message(chat_id, offer["text"], reply_markup=markup)

# ----------------- ADMIN COMMANDS -----------------
def is_admin(user_id):
    """Checks if a user is the admin."""
    return user_id == ADMIN_ID

@bot.message_handler(commands=['admin'])
def admin_commands(message):
    if not is_admin(message.from_user.id):
        return
    
    admin_menu = (
        "👑 *Admin Menu* 👑\n\n"
        "`/allusers` - Get a CSV of all users.\n"
        "`/approve <user_id> <amount>` - Add balance to a user.\n"
        "`/pending` - View pending withdrawals.\n"
        "`/markpaid <row_number>` - Mark a withdrawal as paid."
    )
    bot.send_message(message.chat.id, admin_menu, parse_mode="Markdown")

@bot.message_handler(commands=['allusers'])
def get_all_users(message):
    if not is_admin(message.from_user.id):
        return
    
    if user_sheet:
        try:
            users = user_sheet.get_all_records()
            if not users:
                bot.send_message(ADMIN_ID, "No users found.")
                return

            df = pd.DataFrame(users)
            
            # Create an in-memory CSV file
            output = io.StringIO()
            df.to_csv(output, index=False)
            output.seek(0)
            
            # Send the file
            bot.send_document(ADMIN_ID, ("users.csv", output), caption="Here is the list of all users.")
        except Exception as e:
            print(f"Error fetching all users: {e}")
            bot.send_message(ADMIN_ID, "Failed to retrieve user list.")

@bot.message_handler(commands=['approve'])
def approve_completion(message):
    if not is_admin(message.from_user.id):
        return
    
    parts = message.text.split()
    if len(parts) != 3:
        bot.send_message(ADMIN_ID, "Usage: `/approve <user_id> <amount>`")
        return
        
    try:
        target_user_id = parts[1]
        amount = float(parts[2])
        
        if user_sheet:
            user_cell = user_sheet.find(target_user_id)
            if user_cell:
                current_balance = float(user_sheet.cell(user_cell.row, 5).value)
                new_balance = current_balance + amount
                update_sheet_cell(user_sheet, user_cell.row, 5, new_balance)
                
                # Notify admin and user
                bot.send_message(ADMIN_ID, f"✅ Approved! User {target_user_id}'s new balance is ₹{new_balance}.")
                bot.send_message(target_user_id, f"🎉 Your account has been credited with ₹{amount}! Your new balance is ₹{new_balance}.")
            else:
                bot.send_message(ADMIN_ID, "User not found.")
    except Exception as e:
        print(f"Error in /approve: {e}")
        bot.send_message(ADMIN_ID, "An error occurred during approval.")

@bot.message_handler(commands=['pending'])
def get_pending_withdrawals(message):
    if not is_admin(message.from_user.id):
        return
        
    if withdrawal_sheet:
        try:
            requests = withdrawal_sheet.get_all_records()
            pending_requests = [req for req in requests if req.get('Status') == 'PENDING']
            
            if not pending_requests:
                bot.send_message(ADMIN_ID, "No pending withdrawal requests.")
                return
            
            response = "📋 *Pending Withdrawal Requests* 📋\n\n"
            for i, req in enumerate(pending_requests, 1):
                # Find the original row number
                row_num = withdrawal_sheet.find(req['Timestamp']).row
                response += (
                    f"*Request #{row_num}*\n"
                    f"User ID: `{req['UserID']}`\n"
                    f"Name: {req['Name']}\n"
                    f"UPI: `{req['UPI']}`\n"
                    f"Timestamp: {req['Timestamp']}\n\n"
                )
            bot.send_message(ADMIN_ID, response, parse_mode="Markdown")
        except Exception as e:
            print(f"Error fetching pending requests: {e}")
            bot.send_message(ADMIN_ID, "Failed to retrieve pending requests.")

@bot.message_handler(commands=['markpaid'])
def mark_withdrawal_paid(message):
    if not is_admin(message.from_user.id):
        return
        
    parts = message.text.split()
    if len(parts) != 2:
        bot.send_message(ADMIN_ID, "Usage: `/markpaid <row_number>`")
        return
        
    try:
        row_to_update = int(parts[1])
        if withdrawal_sheet:
            # Column 7 is 'Status'
            update_sheet_cell(withdrawal_sheet, row_to_update, 7, f"PAID on {datetime.now().strftime('%Y-%m-%d')}")
            bot.send_message(ADMIN_ID, f"✅ Request #{row_to_update} has been marked as PAID.")
    except Exception as e:
        print(f"Error in /markpaid: {e}")
        bot.send_message(ADMIN_ID, "An error occurred. Make sure the row number is correct.")

@bot.message_handler(commands=['balance'])
def balance_command(message):
    """Shows user's balance, referral count, and referral link."""
    user_id = message.from_user.id
    if user_sheet:
        try:
            user_cell = user_sheet.find(str(user_id))
            if user_cell:
                user_data = user_sheet.row_values(user_cell.row)
                balance = user_data[4]
                ref_count = user_data[5]
                ref_link = f"https://t.me/{bot.get_me().username}?start={user_id}"
                
                balance_message = (
                    f"💰 Your Balance 💰\n\n"
                    f"Available Balance: ₹{balance}\n"
                    f"Total Referrals: {ref_count}\n\n"
                    f"Share your referral link to earn more:\n"
                    f"`{ref_link}`"
                )
                bot.send_message(user_id, balance_message, parse_mode="Markdown")
            else:
                bot.send_message(user_id, "You are not registered yet. Please /start the bot.")
        except Exception as e:
            print(f"Error fetching balance: {e}")
            bot.send_message(user_id, "Could not retrieve your balance. Please try again later.")

# ----------------- WITHDRAWAL COMMAND -----------------
@bot.message_handler(commands=['withdraw'])
def withdraw_command(message):
    user_id = message.from_user.id
    if user_sheet:
        try:
            user_cell = user_sheet.find(str(user_id))
            if user_cell:
                settings = get_settings()
                min_withdrawal = settings.get('min_withdrawal', 500)
                balance = float(user_sheet.cell(user_cell.row, 5).value)
                if balance >= min_withdrawal:
                    msg = bot.send_message(user_id, "To withdraw, please provide your details.\n\nWhat is your Full Name?")
                    bot.register_next_step_handler(msg, process_name_step)
                else:
                    bot.send_message(user_id, f"Your balance is ₹{balance}. You need at least ₹{min_withdrawal} to withdraw.")
        except Exception as e:
            print(f"Error during withdrawal check: {e}")
            bot.send_message(user_id, "Could not process your request. Please try again later.")

def process_name_step(message):
    try:
        user_id = message.from_user.id
        name = message.text
        # Using a simple dictionary to store withdrawal data temporarily
        user_data = {'id': user_id, 'name': name}
        msg = bot.send_message(user_id, "What is your Mobile Number?")
        bot.register_next_step_handler(msg, process_mobile_step, user_data)
    except Exception as e:
        bot.reply_to(message, 'An error occurred. Please try again.')

def process_mobile_step(message, user_data):
    try:
        mobile = message.text
        user_data['mobile'] = mobile
        msg = bot.send_message(message.chat.id, "What is your Email ID?")
        bot.register_next_step_handler(msg, process_email_step, user_data)
    except Exception as e:
        bot.reply_to(message, 'An error occurred. Please try again.')

def process_email_step(message, user_data):
    try:
        email = message.text
        user_data['email'] = email
        msg = bot.send_message(message.chat.id, "What is your UPI ID?")
        bot.register_next_step_handler(msg, process_upi_step, user_data)
    except Exception as e:
        bot.reply_to(message, 'An error occurred. Please try again.')

def process_upi_step(message, user_data):
    try:
        upi = message.text
        user_data['upi'] = upi
        
        # Save to Google Sheet
        if withdrawal_sheet:
            withdrawal_info = [
                datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                str(user_data['id']),
                user_data['name'],
                user_data['mobile'],
                user_data['email'],
                user_data['upi'],
                "PENDING"
            ]
            withdrawal_sheet.append_row(withdrawal_info)
            
            # Notify Admin
            admin_notification = (
                f"📢 New Withdrawal Request! 📢\n\n"
                f"User ID: {user_data['id']}\n"
                f"Name: {user_data['name']}\n"
                f"Mobile: {user_data['mobile']}\n"
                f"Email: {user_data['email']}\n"
                f"UPI: {user_data['upi']}"
            )
            bot.send_message(ADMIN_ID, admin_notification)
            bot.send_message(message.chat.id, "✅ Your withdrawal request has been submitted. The admin will process it shortly.")
        else:
            bot.send_message(message.chat.id, "Could not submit your request due to a server error. Please try again later.")

    except Exception as e:
        bot.reply_to(message, 'An error occurred. Please try again.')

# ----------------- CALLBACK QUERY HANDLERS -----------------
@bot.callback_query_handler(func=lambda call: call.data.startswith('click_'))
def handle_offer_click(call):
    """Logs the offer click and sends the link to the user."""
    try:
        user_id = call.from_user.id
        # Extract offer text and link from callback_data
        data_parts = call.data.split('_', 1)[1].split('|', 1)
        offer_text = data_parts[0]
        offer_link = data_parts[1]

        # Log the click to the "Clicks" sheet
        if click_sheet:
            click_info = [
                str(user_id),
                offer_text,
                datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            ]
            click_sheet.append_row(click_info)

        # Send the link to the user
        bot.send_message(user_id, f"Here is your link for the offer '{offer_text}':\n{offer_link}")
        bot.answer_callback_query(call.id, "Link received!")
    except Exception as e:
        print(f"Error handling offer click: {e}")
        bot.answer_callback_query(call.id, "Error processing click.")

@bot.callback_query_handler(func=lambda call: call.data == "refresh_offer")
def refresh_offer_callback(call):
    """Handles the 'Refresh' button callback to show a new offer."""
    try:
        bot.delete_message(call.message.chat.id, call.message.message_id)
        send_random_offer(call.message.chat.id)
        bot.answer_callback_query(call.id, "Refreshed!")
    except Exception as e:
        print(f"Error refreshing offer: {e}")
        bot.answer_callback_query(call.id, "Error refreshing offer.")

# ----------------- BOT POLLING -----------------
if __name__ == "__main__":
    print("Bot is starting...")
    keep_alive()  # Start the web server to keep the bot alive on Replit
    bot.polling(none_stop=True)
