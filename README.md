# 🌟 Abel Promotion — Telegram Automation Business System

An automated, Telegram-only business platform built with **Python 3**, **aiogram 3**, and **SQLite**, designed for social media marketing and promotion services in Ethiopia.

The entire system operates strictly inside Telegram without needing an external website, dashboard, or Mini App. Customers can browse services, place orders, receive CBE and Telebirr payment instructions, submit payment screenshots and transaction references, and track order progress in real-time. Administrators have complete operational control over the service catalog, pricing, order fulfillment, payment verification, direct customer communication, and customer support directly through Telegram.

---

## 🚀 Key Features & Workflow

### 1. Bilingual Interface (English & Amharic)
- Full dual-language support: **English (EN)** and **አማርኛ (Amharic - AM)**.
- First-time language selector and on-the-fly language switching (`/language`).
- Localized service names, descriptions, payment guidelines, order statuses, and system notifications.

### 2. Customer Order Workflow
1. Customer selects a promotional service (Instagram, Facebook, YouTube).
2. Customer provides their public profile or post link (with URL structure validation).
3. Customer confirms quantity and reviews calculated total price.
4. System creates the order, snapshots the current service price and name, and generates a unique ID (e.g. `AB-1001`).
5. Order is saved with initial status `pending_payment`.

### 3. Payment Processing (CBE & Telebirr)
- Customer selects **Commercial Bank of Ethiopia (CBE)** or **Telebirr**.
- Bot displays exact configured account holder, account number, and payment instructions.
- Customer submits a screenshot receipt and/or transaction reference code (e.g. `FT...` or Telebirr ID).
- System prevents duplicate transaction references from being submitted.
- Order transitions to `payment_under_review`, and payment status is recorded as `submitted`.

### 4. Admin Review & Payment Verification
- Administrators receive instant push notifications with customer details, order info, and payment screenshot.
- State-guarded action buttons: **Verify Payment**, **Reject Payment**, **Message Customer**, **View Order Details**.
- A screenshot alone never automatically verifies payment. Administrators manually confirm the receipt against bank records.
- When verified: Payment status becomes `verified`, Order status becomes `paid`. Customer is notified immediately.
- When rejected: Administrator provides reason. Customer is notified that payment could not be verified.

### 5. Order Approval & Rejection Workflow
- **State Guard**: Orders **cannot** be approved or started before payment is verified!
- **Approve Order**:
  - Administrator reviews order details and clicks **Approve Order**.
  - Order status updates to `approved`.
  - Customer receives instant approval notification with confirmation of processing.
- **Reject Order**:
  - Administrator enters the rejection reason.
  - Order status updates to `rejected`.
  - Customer receives instant rejection notice with the administrator's reason.
  - If payment was already verified, the payment status transitions to `refund_pending` so it can be handled under the refund policy.

### 6. Direct Two-Way Admin-to-Customer Messaging
- In any order review or detail screen, administrators can click **💬 Message Customer**.
- Admin enters a message (e.g. *"Please make your Instagram profile public so we can process your order"*).
- The bot delivers the message to the customer's private chat with the order ID and an inline **✍️ Reply to Support** button.
- Customer clicks reply, enters their response, and it is forwarded back to all administrators with full order context.
- Full communication history is permanently stored in the `order_messages` database table.
- Administrator personal accounts and phone numbers remain completely confidential.

---

## 📂 Project Structure

```text
Abel Promotion/
├── bot.py                  # Main entry point & polling orchestrator
├── config.py               # Environment configuration & admin checks
├── requirements.txt        # Python production dependencies
├── pytest.ini             # Pytest configuration
├── .env.example            # Environment variables template
├── .gitignore              # Git ignore rules (protects .env & SQLite db)
├── Dockerfile              # Production container build definition
├── .dockerignore           # Container build exclusions
├── render.yaml             # Render Blueprint configuration
├── Procfile                # Heroku / Railway worker definition
├── railway.json            # Railway deployment configuration
├── README.md               # Complete project documentation
│
├── handlers/               # aiogram 3 Telegram routers
│   ├── start.py            # /start welcome and language check
│   ├── language.py         # Language selection and updating
│   ├── menu.py             # Main reply keyboard menu navigation
│   ├── services.py         # Catalog browsing by platform
│   ├── orders.py           # Order creation, details & customer replies
│   ├── payments.py         # Payment methods & receipt submissions
│   ├── profile.py          # Customer profile summary
│   ├── support.py          # Help & support ticketing
│   ├── admin.py            # Complete Telegram admin panel & workflow
│   └── states.py           # FSM state definitions
│
├── keyboards/              # Telegram keyboard builders
│   ├── main_menu.py        # Main reply keyboard & navigation
│   ├── language.py         # Inline language picker
│   ├── services.py         # Platform & service list buttons
│   ├── orders.py           # Order confirmation & reply buttons
│   ├── payments.py         # Payment methods & evidence buttons
│   └── admin.py            # Admin action keyboards & state buttons
│
├── services/               # Business services
│   └── notification_service.py # Direct messaging & Telegram alerts
│
├── database/               # Database management
│   ├── connection.py       # Async SQLite connection & migration runner
│   ├── migrations.py       # Safe schema upgrade & status normalization
│   ├── models.py           # Entity dataclasses
│   └── repositories.py     # Database CRUD repositories
│
├── middlewares/            # aiogram middlewares
│   ├── user_context.py     # Automatic user registration & language context
│   └── admin_auth.py       # Strict admin authorization filter
│
├── utils/                  # Helper utilities
│   ├── localization.py     # Bilingual dictionaries (EN & AM)
│   ├── validators.py       # URL, quantity, and reference validators
│   └── order_codes.py      # Unique order and ticket code formatters
│
└── tests/                  # Automated test suite
    ├── test_twenty_criteria.py  # 20 required criteria end-to-end tests
    ├── test_orders.py          # Order creation and snapshots tests
    ├── test_payments.py        # Payment verification tests
    ├── test_permissions.py     # Admin auth & isolation tests
    ├── test_validators.py      # Input validation tests
    └── test_support_and_admin.py # Support tickets & catalog tests
```

---

## 🧪 Automated Testing

The project includes 27 comprehensive automated tests verifying all 20 required criteria:

```bash
# Run the entire test suite
.\venv\Scripts\pytest -v
```

All 27 tests pass:
```text
tests/test_orders.py::test_order_creation_and_snapshot PASSED
tests/test_orders.py::test_order_status_transitions PASSED
tests/test_payments.py::test_payment_submission_and_duplicate_prevention PASSED
tests/test_payments.py::test_admin_payment_verification PASSED
tests/test_permissions.py::test_admin_and_owner_permissions PASSED
tests/test_permissions.py::test_order_privacy_isolation PASSED
tests/test_support_and_admin.py::test_support_ticket_flow PASSED
tests/test_support_and_admin.py::test_language_switch_persistence PASSED
tests/test_support_and_admin.py::test_admin_service_catalog_management PASSED
tests/test_support_and_admin.py::test_payment_rejection_flow PASSED
tests/test_twenty_criteria.py::test_criterion_1_to_3_order_creation_unique_id_price_snapshot PASSED
tests/test_twenty_criteria.py::test_criterion_4_and_5_payment_evidence_and_admin_notification PASSED
tests/test_twenty_criteria.py::test_criterion_6_to_8_payment_verification_auth_and_confirmation PASSED
tests/test_twenty_criteria.py::test_criterion_9_and_10_order_approval_and_notification PASSED
tests/test_twenty_criteria.py::test_criterion_11_and_12_order_rejection_and_notification PASSED
tests/test_twenty_criteria.py::test_criterion_13_and_14_admin_customer_bidirectional_messaging PASSED
tests/test_twenty_criteria.py::test_criterion_15_order_privacy_isolation PASSED
tests/test_twenty_criteria.py::test_criterion_16_invalid_status_transitions_rejected PASSED
tests/test_twenty_criteria.py::test_criterion_17_duplicate_payment_references PASSED
tests/test_twenty_criteria.py::test_criterion_18_data_survives_application_restart PASSED
tests/test_twenty_criteria.py::test_criterion_19_database_migrations_preserve_existing_records PASSED
tests/test_twenty_criteria.py::test_criterion_20_network_failure_resilience PASSED
tests/test_validators.py::test_instagram_link_validation PASSED
tests/test_validators.py::test_facebook_link_validation PASSED
tests/test_validators.py::test_youtube_link_validation PASSED
tests/test_validators.py::test_quantity_validation PASSED
tests/test_validators.py::test_transaction_reference_validation PASSED

============================= 27 passed in 12.45s =============================
```

---

## 💻 Local Setup & Execution

### 1. Requirements
- Python 3.10, 3.11, 3.12, or 3.13
- A Telegram account and Bot Token from [@BotFather](https://t.me/BotFather)

### 2. Clone / Open Folder
```bash
cd "c:\Users\ousma\Downloads\Abel Promotion"
```

### 3. Create & Activate Virtual Environment
```bash
# Windows
python -m venv venv
.\venv\Scripts\activate

# Linux / Mac
python3 -m venv venv
source venv/bin/activate
```

### 4. Install Dependencies
```bash
pip install -r requirements.txt
```

### 5. Configure `.env`
Create `.env` file (or copy from `.env.example`):
```bash
cp .env.example .env
```
Fill in your credentials:
```env
BOT_TOKEN=8805207602:AAFL8k...YourTelegramBotToken...
ADMIN_IDS=6658528398
OWNER_ID=6658528398
DATABASE_PATH=data/abel_promotion.db
DEFAULT_LANGUAGE=en
SUPPORT_CHANNEL=@AbelPromotionSupport
```
> **How to find your numeric Telegram ID:**
> Send any message to [@userinfobot](https://t.me/userinfobot) or [@raw_data_bot](https://t.me/raw_data_bot) on Telegram. It will reply with your numeric `Id` (e.g. `6658528398`).

### 6. Start the Bot Locally
```bash
python bot.py
```

---

## ☁️ 24/7 Cloud Deployment Guide (Runs Without Your Computer)

To keep the bot running 24 hours a day, 7 days a week — even when your computer is shut down, when VS Code is closed, or when you are offline — you deploy the bot to a cloud hosting platform as a **continuous worker**.

### ⚠️ Crucial Rule for Cloud Hosting
1. **Long Polling Bot = Background Worker**: A Telegram polling bot is a background worker process, **not** a website. It does not listen on an HTTP port.
2. **Persistent Storage**: The bot uses SQLite (`data/abel_promotion.db`). If you deploy to a container service without persistent storage, every redeployment or restart will reset your database! You **must** mount a persistent disk/volume to `/app/data` so customer orders and payments are permanently preserved.
3. **Avoid Running Two Bot Instances**: Before launching the bot in the cloud, always stop any running instance on your personal computer. Telegram allows only one polling connection per bot token at a time.

---

### Option 1: Deploy on Railway (Recommended, Simplest)

[Railway](https://railway.app) allows you to deploy Docker containers with persistent volumes in a few minutes.

#### Step 1: Push your project to GitHub
1. Create a private repository on [GitHub](https://github.com) named `abel-promotion-bot`.
2. Push your project code to GitHub:
   ```bash
   git init
   git add .
   git commit -m "Initial commit of Abel Promotion bot"
   git branch -M main
   git remote add origin https://github.com/YOUR_USERNAME/abel-promotion-bot.git
   git push -u origin main
   ```
   *(Note: `.env` and `data/` are in `.gitignore`, so your private bot token is never pushed to GitHub).*

#### Step 2: Create a Project in Railway
1. Go to [railway.app](https://railway.app) and sign in with your GitHub account.
2. Click **New Project** -> **Deploy from GitHub repo**.
3. Select your `abel-promotion-bot` repository.

#### Step 3: Add Persistent Volume (Preserve Database)
1. In your Railway service settings, click on the **Volumes** tab.
2. Click **Add Volume**.
3. Set the Mount Path to:
   ```text
   /app/data
   ```
4. This ensures that `data/abel_promotion.db` survives every restart, crash, or code update!

#### Step 4: Configure Environment Variables
1. Go to the **Variables** tab in Railway.
2. Add the following variables:
   - `BOT_TOKEN`: `YourTelegramBotToken`
   - `ADMIN_IDS`: `6658528398`
   - `OWNER_ID`: `6658528398`
   - `DATABASE_PATH`: `data/abel_promotion.db`
   - `DEFAULT_LANGUAGE`: `en`
3. Click **Deploy**.

#### Step 5: Check Logs
1. Click the **Deployments** tab -> click the active deployment -> **View Logs**.
2. You will see:
   ```text
   Initializing SQLite database...
   Database initialized successfully.
   Starting Abel Promotion bot long polling...
   ```
3. Your bot is now live 24/7!

---

### Option 2: Deploy on Render

[Render](https://render.com) provides managed background worker services with persistent disks.

#### Step 1: Create a Background Worker on Render
1. Push your code to GitHub (as described above).
2. Sign in to [render.com](https://render.com).
3. Click **New +** -> **Background Worker**.
4. Connect your GitHub repository.

#### Step 2: Configure Service Settings
- **Name**: `abel-promotion-bot`
- **Region**: Frankfurt (or closest to Ethiopia/Europe)
- **Environment**: `Python 3`
- **Build Command**: `pip install -r requirements.txt`
- **Start Command**: `python bot.py`
- **Plan**: Starter *(Background workers that run 24/7 continuously without sleeping require the Starter plan)*.

#### Step 3: Attach Persistent Disk
1. Scroll down to **Disks** -> click **Add Disk**.
2. **Name**: `abel-data`
3. **Mount Path**: `/app/data`
4. **Size**: `1 GB` (plenty for hundreds of thousands of SQLite records).

#### Step 4: Set Environment Variables
In the **Environment Variables** section, add:
- `BOT_TOKEN`: Your bot token
- `ADMIN_IDS`: `6658528398`
- `OWNER_ID`: `6658528398`
- `DATABASE_PATH`: `data/abel_promotion.db`
- `DEFAULT_LANGUAGE`: `en`
- `PYTHON_VERSION`: `3.11.9`

Click **Create Background Worker**. View the logs in the Render dashboard to confirm the bot starts.

---

### Option 3: Deploy on a Linux VPS (DigitalOcean / Hetzner / AWS)

If you have an Ubuntu Linux VPS server ($4–$5/month):

1. SSH into your VPS:
   ```bash
   ssh root@your_server_ip
   ```
2. Install Python and git:
   ```bash
   apt update && apt install -y python3 python3-venv git
   ```
3. Clone your repository:
   ```bash
   git clone https://github.com/YOUR_USERNAME/abel-promotion-bot.git /opt/abel-promotion
   cd /opt/abel-promotion
   ```
4. Setup virtual environment:
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```
5. Create `.env` file:
   ```bash
   nano .env
   ```
   Paste your variables and save (Ctrl+O, Enter, Ctrl+X).
6. Create a systemd service to run the bot automatically in the background and restart on crash:
   ```bash
   cat << 'EOF' > /etc/systemd/system/abel-bot.service
   [Unit]
   Description=Abel Promotion Telegram Bot
   After=network.target

   [Service]
   Type=simple
   User=root
   WorkingDirectory=/opt/abel-promotion
   ExecStart=/opt/abel-promotion/venv/bin/python bot.py
   Restart=always
   RestartSec=5
   EnvironmentFile=/opt/abel-promotion/.env

   [Install]
   WantedBy=multi-user.target
   EOF
   ```
7. Start and enable the bot service:
   ```bash
   systemctl daemon-reload
   systemctl enable abel-bot
   systemctl start abel-bot
   ```
8. View real-time logs:
   ```bash
   journalctl -u abel-bot -f
   ```

---

## 🔄 Updating Your Deployed Bot

When you make changes to the code in the future:
1. Commit and push your changes to GitHub:
   ```bash
   git add .
   git commit -m "Update feature XYZ"
   git push
   ```
2. **On Railway / Render**: The platform will automatically detect the commit and trigger a rolling redeployment. Because the database is stored on the persistent volume (`/app/data`), no customer data, orders, or payment records will be lost!
3. **On VPS**:
   ```bash
   cd /opt/abel-promotion
   git pull
   systemctl restart abel-bot
   ```

---

## 🔑 How to Rotate a Compromised Bot Token

If your bot token is accidentally leaked or exposed:
1. Open Telegram and message [@BotFather](https://t.me/BotFather).
2. Send `/mybots` -> Select **Abel Promotion** -> **API Token** -> **Revoke current token**.
3. BotFather will revoke the old token and generate a new one.
4. Go to your cloud host (Railway / Render / VPS `.env`) and update the `BOT_TOKEN` environment variable with the new token.
5. Restart or redeploy the service. The bot will immediately connect using the new token.

---

## ✅ 24/7 Verification Checklist

After deploying to your cloud host, follow this simple checklist to confirm the bot remains online without your personal computer:

1. [ ] Stop any running Python process in your local terminal (press `Ctrl + C`).
2. [ ] Turn off your computer (or put it to sleep and disconnect from Wi-Fi).
3. [ ] Open Telegram on your smartphone.
4. [ ] Send `/start` to your bot.
5. [ ] Verify that the bot replies with the main menu immediately.
6. [ ] Place a test order through the bot.
7. [ ] Send `/admin` from your administrator Telegram account.
8. [ ] Verify that the admin panel opens, showing your test order.
9. [ ] Check the cloud deployment logs to ensure no restarts or unhandled errors occurred.

Congratulations! Your **Abel Promotion** Telegram business system is now running continuously in the cloud 24 hours a day, 7 days a week!
