Build a secure and advanced Admin Panel for my Telegram bot project called "PocketCashBot".

The bot is a task/offer based earning platform. I want the admin panel to include the following core features, divided into logical phases:

---

🟨 Phase 1: Authentication & Security

- Admin login page (username + password based)
- Store hashed passwords securely using bcrypt or similar
- Logout functionality
- Middleware/auth check for all protected admin routes

---

🟩 Phase 2: Offer Management (Add/Edit/Delete)

- Add New Offer:
  - Title
    - Description
      - Target link
        - Offer category (Demat, Credit Card, Insurance, etc.)
          - Reward amount (₹)
            - Offer status (active/inactive)
            - View All Offers (Paginated)
            - Edit Offer details
            - Delete offer

            ---

            🟦 Phase 3: User Management

            - View All Registered Users:
              - Telegram ID
                - Username
                  - Joined date
                    - Referral count
                      - Earnings
                        - UPI details
                        - Block/Unblock any user
                        - Search by Telegram ID or Username
                        - Export user data as CSV

                        ---

                        🟧 Phase 4: Withdrawal Requests

                        - View pending withdrawal requests:
                          - User details
                            - Amount requested
                              - UPI ID
                              - Approve or Reject withdrawal
                              - Mark as paid (with timestamp)
                              - Auto-update Google Sheet or Firebase entry

                              ---

                              🟥 Phase 5: Referral System Management

                              - View referral tree (who referred whom)
                              - Set referral reward amount (₹ per invite)
                              - Enable/disable referral system
                              - Manually add bonus to any user

                              ---

                              🟪 Phase 6: Push Notification System

                              - Send custom broadcast message to all users
                              - Select group: All / Active / Inactive / Blocked
                              - Option to schedule messages
                              - Store logs of sent notifications

                              ---

                              🟫 Phase 7: Admin Settings & Logs

                              - Admin profile update (name, password)
                              - Set global bot settings:
                                - Minimum withdrawal amount
                                  - Bonus on first task
                                    - Offer refresh frequency
                                    - Action logs:
                                      - Offer changes
                                        - User actions
                                          - Withdrawals

                                          ---

                                          Use a clean responsive UI like AdminLTE or Tailwind Admin Kit. Backend can be built in Flask (Python) or Express (Node.js) and should be easy to deploy on Replit, Vercel, or Railway. Store data using Google Sheets or Firebase or MongoDB (whichever is available).

                                          The final admin panel must be connected to the Telegram bot backend using a shared database or API.