# PocketCashBot Deployment Guide

This guide provides all the necessary steps to set up the Google Sheet, and deploy the Telegram bot on either Replit or Termux.

---

## 1. Google Sheet Setup

The bot uses a Google Sheet as its database. You must set it up correctly for the bot to function.

### Step 1: Create the Google Sheet
1.  Go to [sheets.google.com](https://sheets.google.com).
2.  Create a new blank spreadsheet.
3.  Rename the spreadsheet to **PocketCashBotDB**.

### Step 2: Create the Worksheets
You need to create three separate worksheets within the spreadsheet with the following names and headers. The headers **must be in the first row** and spelled exactly as shown below.

**Worksheet 1: `Users`**
| UserID | Name | Username | JoinDate | Balance | ReferralCount | InvitedBy | Status |
|---|---|---|---|---|---|---|---|
> **Note**: The `Status` column should be added. It can be `active` or `blocked`.

**Worksheet 2: `Clicks`**
| UserID | OfferText | Timestamp |
|---|---|---|

**Worksheet 3: `Withdrawals`**
| Timestamp | UserID | Name | Mobile | Email | UPI | Status |
|---|---|---|---|---|---|---|

### Step 3: Set up Google Cloud & Service Account
1.  Go to the [Google Cloud Console](https://console.cloud.google.com/).
2.  Create a new project.
3.  Enable the **Google Drive API** and **Google Sheets API** for your project.
4.  Create a **Service Account**.
    - Go to "IAM & Admin" -> "Service Accounts".
    - Click "Create Service Account".
    - Give it a name (e.g., "pocket-cash-bot-service").
    - Grant it the "Editor" role.
    - Click "Done".
5.  **Create JSON credentials** for the service account.
    - Find your new service account in the list.
    - Click the three dots under "Actions" and select "Manage keys".
    - Click "Add Key" -> "Create new key".
    - Select **JSON** and click "Create". A JSON file will be downloaded.
6.  **Rename the downloaded file** to `client_secret.json` and place it in your project directory.
7.  **Share the Google Sheet**:
    - Open the `client_secret.json` file and find the `client_email` address.
    - In your `PocketCashBotDB` Google Sheet, click the "Share" button.
    - Paste the `client_email` and give it "Editor" permissions.

---

## 2. Deployment on Replit (Recommended)

Replit is a free and easy way to host this bot 24/7.

### Steps:
1.  **Create a Replit Account**: Sign up at [replit.com](https://replit.com).
2.  **Create a New Repl**:
    - Click the "+" button to create a new Repl.
    - Select the **Python** template.
    - Give it a name.
3.  **Upload Files**:
    - Upload your `main.py` and `requirements.txt` files to the Repl.
4.  **Add Secrets**:
    - **Do not upload `client_secret.json` directly.**
    - In the Replit sidebar, go to the "Secrets" tab (padlock icon).
    - Create a new secret with the key `CLIENT_SECRET_JSON`.
    - For the value, copy the **entire content** of your `client_secret.json` file and paste it into the value field.
    - You will need to modify `main.py` to read this secret instead of the file. Change this line:
      ```python
      # In main.py
      creds = ServiceAccountCredentials.from_json_keyfile_name("client_secret.json", scope)
      ```
      to this:
      ```python
      import os
      import json
      # ...
      client_secret_str = os.environ['CLIENT_SECRET_JSON']
      client_secret_dict = json.loads(client_secret_str)
      creds = ServiceAccountCredentials.from_json_keyfile_dict(client_secret_dict, scope)
      ```
5.  **Install Dependencies**:
    - Go to the "Shell" tab in your Repl.
    - Run the command: `pip install -r requirements.txt`
6.  **Run the Bot**:
    - Click the "Run" button at the top.
    - The bot will start, and the Flask web server will keep it alive. You can see the web view in a new tab in your Repl.

---

## 3. Deployment on Termux (Advanced)

This method runs the bot on an Android device. It requires the device to be constantly on and connected to the internet.

### Steps:
1.  **Install Termux**: Get Termux from F-Droid.
2.  **Update Packages**:
    ```bash
    pkg update && pkg upgrade
    ```
3.  **Install Python and Git**:
    ```bash
    pkg install python git
    ```
4.  **Clone Your Project**:
    - If you have your project on GitHub, clone it:
      ```bash
      git clone <your-repo-url>
      cd <your-repo-folder>
      ```
    - Otherwise, you'll need to manually transfer the files (`main.py`, `requirements.txt`, `client_secret.json`) to your device's storage and move them into the Termux home directory.
5.  **Install Dependencies**:
    ```bash
    pip install -r requirements.txt
    ```
6.  **Run the Bot Persistently**:
    - To keep the bot running in the background even after you close Termux, use `nohup`:
      ```bash
      nohup python main.py &
      ```
    - This will start the bot and create a `nohup.out` file where all the print statements will be logged.
7.  **Auto-Restart Script (Optional but Recommended)**:
    - Create a script to check if the bot is running and restart it if it crashes.
    - Create a file named `start_bot.sh`:
      ```bash
      #!/bin/bash
      while true; do
          if ! pgrep -f "python main.py"; then
              echo "Bot is not running. Starting..."
              nohup python main.py &
          fi
          sleep 60 # Check every 60 seconds
      done
      ```
    - Make the script executable: `chmod +x start_bot.sh`
    - Run the script: `./start_bot.sh`
