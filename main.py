import telebot
import random
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

# ----------------- BOT CONFIGURATION -----------------
BOT_TOKEN = "8019925796:AAHgnzy5JtkZujwB370woBsNnmBczE2hpx8"
ADMIN_ID = 6565013470
bot = telebot.TeleBot(BOT_TOKEN)

# ----------------- GOOGLE SHEETS CONFIGURATION -----------------
try:
    scope = ["https://spreadsheets.google.com/feeds", 'https://www.googleapis.com/auth/spreadsheets',
             "https://www.googleapis.com/auth/drive.file", "https://www.googleapis.com/auth/drive"]
    creds = ServiceAccountCredentials.from_json_keyfile_name("client_secret.json", scope)
    client = gspread.authorize(creds)
    sheet = client.open("PocketCashBotDB").worksheet("Users")
    print("Google Sheets connected successfully.")
except Exception as e:
    print(f"Error connecting to Google Sheets: {e}")
    sheet = None

# -----------------  OFFERS (TEMPORARY) -----------------
OFFERS = [
    {"text": "Open Demat Account & Earn ₹300", "link": "https://example.com/demat"},
    {"text": "Apply for Credit Card & Get ₹500", "link": "https://example.com/creditcard"},
    {"text": "Buy Term Insurance & Earn ₹400", "link": "https://example.com/insurance"},
    {"text": "Signup on App & Get ₹100", "link": "https://example.com/app-signup"},
    {"text": "Complete a Survey & Earn ₹50", "link": "https://example.com/survey"},
]

# ----------------- KEYBOARD MARKUPS -----------------
def create_offer_markup(offer_link):
    """Creates an inline keyboard for an offer."""
    markup = InlineKeyboardMarkup()
    markup.row_width = 2
    markup.add(
        InlineKeyboardButton("✅ Accept & Get Link", url=offer_link),
        InlineKeyboardButton("🔄 Refresh", callback_data="refresh_offer")
    )
    return markup

# ----------------- BOT COMMAND HANDLERS -----------------
def update_sheet_cell(row, col, value):
    """Updates a specific cell in the Google Sheet."""
    try:
        sheet.update_cell(row, col, value)
    except Exception as e:
        print(f"Error updating sheet cell ({row}, {col}): {e}")

@bot.message_handler(commands=['start'])
def send_welcome(message):
    """Handles the /start command, registers new user, and processes referrals."""
    user_id = message.from_user.id
    
    if sheet:
        try:
            # Check if user already exists
            user_cell = sheet.find(str(user_id))
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
                    referrer_id if referrer_id else ""  # Invited By
                ]
                sheet.append_row(user_info)
                
                # Notify admin about new user
                admin_message = f"🎉 New User Alert! 🎉\n\nID: {user_id}\nName: {message.from_user.first_name}\nUsername: @{message.from_user.username}"
                if referrer_id:
                    admin_message += f"\nInvited by: {referrer_id}"
                bot.send_message(ADMIN_ID, admin_message)

                # Process referral
                if referrer_id:
                    referrer_cell = sheet.find(referrer_id)
                    if referrer_cell:
                        # Update referrer's balance
                        current_balance = float(sheet.cell(referrer_cell.row, 5).value)
                        new_balance = current_balance + 10
                        update_sheet_cell(referrer_cell.row, 5, new_balance)

                        # Update referrer's referral count
                        current_ref_count = int(sheet.cell(referrer_cell.row, 6).value)
                        new_ref_count = current_ref_count + 1
                        update_sheet_cell(referrer_cell.row, 6, new_ref_count)
                        
                        # Notify referrer
                        bot.send_message(referrer_id, f"🎉 You've earned ₹10 for referring a new user! Your new balance is ₹{new_balance}.")

        except Exception as e:
            print(f"Error processing new user in Google Sheets: {e}")

    send_random_offer(message.chat.id)

def send_random_offer(chat_id):
    """Sends a random offer to the user."""
    offer = random.choice(OFFERS)
    markup = create_offer_markup(offer["link"])
    bot.send_message(chat_id, offer["text"], reply_markup=markup)

@bot.message_handler(commands=['balance'])
def balance_command(message):
    """Shows user's balance, referral count, and referral link."""
    user_id = message.from_user.id
    if sheet:
        try:
            user_cell = sheet.find(str(user_id))
            if user_cell:
                user_data = sheet.row_values(user_cell.row)
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

# ----------------- CALLBACK QUERY HANDLERS -----------------
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
    print("Bot is running...")
    bot.polling(none_stop=True)
