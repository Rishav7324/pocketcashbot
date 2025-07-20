I want to build a Telegram bot using Python and Telebot. The bot's name is PocketCashBot. It should show users random earning offers like:

Open Demat Account & Earn ₹300

Apply for Credit Card & Get ₹500

Buy Term Insurance & Earn ₹400


Each offer will have:

Accept & Get Link button (link opens offer)

Refresh button (to show next random offer)




The bot must use this Telegram Bot Token: 8019925796:AAHgnzy5JtkZujwB370woBsNnmBczE2hpx8
Admin Telegram ID is: 6565013470


---

🧩 Prompt Part 2: User Tracking (Phase 2)

> Add user tracking to the bot. When someone starts the bot, store their:

Telegram user ID

Name

Username

Date of joining




This user data should be saved to a connected Google Sheet (I'll provide the link & credentials). Also, send a notification to admin when a new user joins.


---

🧩 Prompt Part 3: Referral System (Phase 3)

> Add referral system:

When a user joins with a referral link, store who invited them.

Give ₹10 bonus per referral.

Each user gets a unique referral link like https://t.me/PocketCashBot?start=6565013470




Show their referral count and earnings using /balance command.


---

🧩 Prompt Part 4: Rewards System (Phase 4)

> Add rewards system:

Track when user clicks on an offer (log that click)

Track completed actions manually by admin (like account opened)

When user completes any offer (verified by admin), update their reward balance in Google Sheet

Add “Withdraw” button when balance reaches ₹500

On withdraw request, collect:

Full Name

Mobile Number

Email ID

UPI ID


Save this data in Google Sheet and notify admin





---

🧩 Prompt Part 5: Admin Panel (Phase 5)

> Add admin functionality:

Admin can see full user list

Admin can mark offer actions as completed for any user

Admin can see pending withdrawal requests

Admin can edit balances manually from Google Sheet





---

🧩 Prompt Part 6: Deployment (Phase 6)

> Finally, give me the steps to host this bot on Replit and run it in Termux, with persistent background running.
Also make sure it auto-restarts if it crashes.




---

✅ Final Output Should Include:

1. main.py file (working)


2. requirements.txt file


3. client_secret.json sample for Google Sheets


4. Hosting steps (for Termux or Replit)


5. Google Sheet format example
