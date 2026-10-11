"""
Async SQLite Database Connection and Schema Initialization for Abel Promotion.
"""

import aiosqlite
from pathlib import Path
from typing import AsyncGenerator
import config

DB_SCHEMA = """
-- Users table
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    telegram_id INTEGER UNIQUE NOT NULL,
    username TEXT,
    first_name TEXT,
    language TEXT DEFAULT 'en',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_blocked INTEGER DEFAULT 0
);

-- Admins table
CREATE TABLE IF NOT EXISTS admins (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    telegram_id INTEGER UNIQUE NOT NULL,
    role TEXT DEFAULT 'admin',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_active INTEGER DEFAULT 1
);

-- Services catalog table
CREATE TABLE IF NOT EXISTS services (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name_en TEXT NOT NULL,
    name_am TEXT NOT NULL,
    platform TEXT NOT NULL,
    description_en TEXT,
    description_am TEXT,
    price REAL NOT NULL,
    pricing_type TEXT DEFAULT 'fixed',
    minimum_quantity INTEGER DEFAULT 1,
    maximum_quantity INTEGER DEFAULT 100000,
    estimated_duration_en TEXT DEFAULT '1-2 business days',
    estimated_duration_am TEXT DEFAULT '1-2 የሥራ ቀናት',
    is_active INTEGER DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Orders table
CREATE TABLE IF NOT EXISTS orders (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    order_code TEXT UNIQUE,
    user_id INTEGER NOT NULL,
    service_id INTEGER NOT NULL,
    service_name_snapshot TEXT NOT NULL,
    unit_price_snapshot REAL NOT NULL,
    quantity INTEGER DEFAULT 1,
    total_price REAL NOT NULL,
    target_link TEXT NOT NULL,
    customer_notes TEXT,
    status TEXT DEFAULT 'pending_payment',
    approved_by INTEGER,
    approved_at TIMESTAMP,
    rejection_reason TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(user_id) REFERENCES users(telegram_id),
    FOREIGN KEY(service_id) REFERENCES services(id)
);

-- Payments table
CREATE TABLE IF NOT EXISTS payments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    order_id INTEGER NOT NULL,
    payment_method TEXT NOT NULL,
    expected_amount REAL NOT NULL,
    transaction_reference TEXT,
    screenshot_file_id TEXT,
    status TEXT DEFAULT 'submitted',
    submitted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    verified_by INTEGER,
    verified_at TIMESTAMP,
    verification_notes TEXT,
    rejection_reason TEXT,
    FOREIGN KEY(order_id) REFERENCES orders(id)
);

-- Payment Methods configuration table
CREATE TABLE IF NOT EXISTS payment_methods (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    method_code TEXT UNIQUE NOT NULL,
    method_name TEXT NOT NULL,
    account_holder TEXT NOT NULL,
    account_number TEXT NOT NULL,
    instructions_en TEXT,
    instructions_am TEXT,
    is_active INTEGER DEFAULT 1
);

-- Order Status History
CREATE TABLE IF NOT EXISTS order_status_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    order_id INTEGER NOT NULL,
    previous_status TEXT,
    new_status TEXT NOT NULL,
    changed_by INTEGER,
    reason TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(order_id) REFERENCES orders(id)
);

-- Direct Order Messages between Admin and Customer
CREATE TABLE IF NOT EXISTS order_messages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    order_id INTEGER NOT NULL,
    sender_id INTEGER NOT NULL,
    sender_role TEXT NOT NULL,
    message_text TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(order_id) REFERENCES orders(id)
);

-- Support Tickets
CREATE TABLE IF NOT EXISTS support_tickets (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ticket_code TEXT UNIQUE,
    user_id INTEGER NOT NULL,
    order_id INTEGER,
    message TEXT NOT NULL,
    admin_response TEXT,
    status TEXT DEFAULT 'Open',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    closed_at TIMESTAMP,
    FOREIGN KEY(user_id) REFERENCES users(telegram_id)
);

-- Audit Logs
CREATE TABLE IF NOT EXISTS audit_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    admin_telegram_id INTEGER NOT NULL,
    action TEXT NOT NULL,
    entity_type TEXT,
    entity_id TEXT,
    details TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_users_telegram_id ON users(telegram_id);
CREATE INDEX IF NOT EXISTS idx_orders_user_id ON orders(user_id);
CREATE INDEX IF NOT EXISTS idx_orders_status ON orders(status);
CREATE INDEX IF NOT EXISTS idx_orders_order_code ON orders(order_code);
CREATE INDEX IF NOT EXISTS idx_payments_order_id ON payments(order_id);
CREATE INDEX IF NOT EXISTS idx_payments_ref ON payments(transaction_reference);
CREATE INDEX IF NOT EXISTS idx_services_platform ON services(platform);
CREATE INDEX IF NOT EXISTS idx_order_messages_order_id ON order_messages(order_id);
"""

from contextlib import asynccontextmanager
from database.migrations import run_migrations

@asynccontextmanager
async def get_db_connection():
    """Context manager for async database connection with row factory enabled."""
    config.DATABASE_PATH.parent.mkdir(parents=True, exist_ok=True)
    async with aiosqlite.connect(config.DATABASE_PATH) as db:
        db.row_factory = aiosqlite.Row
        await db.execute("PRAGMA foreign_keys = ON;")
        yield db

async def init_db() -> None:
    """Create all tables, run migrations, and seed essential default data if empty."""
    config.DATABASE_PATH.parent.mkdir(parents=True, exist_ok=True)
    async with aiosqlite.connect(config.DATABASE_PATH) as db:
        await db.execute("PRAGMA foreign_keys = ON;")
        await db.executescript(DB_SCHEMA)
        await run_migrations(db)

        # 1. Seed Payment Methods if table empty
        async with db.execute("SELECT COUNT(*) FROM payment_methods") as cursor:
            count = (await cursor.fetchone())[0]
            if count == 0:
                await db.execute("""
                    INSERT INTO payment_methods (method_code, method_name, account_holder, account_number, instructions_en, instructions_am, is_active)
                    VALUES 
                    ('cbe', 'Commercial Bank of Ethiopia (CBE)', 'Abel Promotion / Abel Tesfaye', '1000123456789',
                     'Transfer via CBE Mobile Banking or CBE Birr. Attach screenshot & FT reference.',
                     'በ CBE Mobile Banking ወይም በ CBE Birr ያስተላልፉ። የደረሰኝ ስክሪንሾት እና የ FT ቁጥር ያያይዙ።', 1),
                    ('telebirr', 'Telebirr', 'Abel Promotion / Abel Tesfaye', '0911223344',
                     'Transfer via Telebirr App or *127#. Attach screenshot & transaction reference.',
                     'በቴሌብር መተግበሪያ ወይም በ *127# ይላኩ። የደረሰኝ ስክሪንሾት እና የትራንዛክሽን መለያ ቁጥር ያያይዙ።', 1)
                """)

        # 2. Seed Services if table empty
        async with db.execute("SELECT COUNT(*) FROM services") as cursor:
            service_count = (await cursor.fetchone())[0]
            if service_count == 0:
                services_seed = [
                    # Instagram
                    ("Instagram Profile Optimization", "የኢንስታግራም ገጽ ማሻሻያ እና አደረጃጀት", "Instagram",
                     "Improve visual layout, bio, and business presentation of your Instagram profile.",
                     "የኢንስታግራም ገጽዎን አቀራረብ፣ ባዮ እና የቢዝነስ ገጽታ ማሻሻል እና ማስተካከል", 300.0, "fixed", 1, 1, "1-2 working days", "1-2 የሥራ ቀናት"),
                    ("Instagram Content Planning", "የኢንስታግራም ይዘት (ኮንተንት) እቅድ", "Instagram",
                     "Strategic content calendar and creative guidance for business reach.",
                     "ለተከታታይ የቢዝነስ እድገት የሚሆን የልጥፍ እና የይዘት እቅድ ዝግጅት", 500.0, "fixed", 1, 1, "2-3 working days", "2-3 የሥራ ቀናት"),
                    ("Instagram Advertising Campaign Assistance", "የኢንስታግራም ማስታወቂያ እገዛ", "Instagram",
                     "Setup and audience targeting support for official Instagram sponsored ads.",
                     "በኦፊሴላዊው ኢንስታግራም ስፖንሰርድ ማስታወቂያዎች ተገቢውን ታዳሚ የመድረስ እገዛ", 800.0, "fixed", 1, 1, "3-5 working days", "3-5 የሥራ ቀናት"),
                    ("Instagram Growth Consultation", "የኢንስታግራም እድገት ምክክር", "Instagram",
                     "Personalized consultation on authentic audience growth and engagement techniques.",
                     "ትክክለኛ ታዳሚዎችን ለመሳብ እና ተሳትፎን ለማሳደግ የሚሰጥ ሙያዊ ምክክር", 400.0, "fixed", 1, 1, "1-2 working days", "1-2 የሥራ ቀናት"),

                    # Facebook
                    ("Facebook Page Setup & Optimization", "የፌስቡክ ገጽ ማዋቀር እና ማሻሻል", "Facebook",
                     "Professional setup of page info, call-to-actions, and branding.",
                     "የፌስቡክ ገጽ ሙሉ መረጃዎችን ማደራጀት፣ አዝራሮችን ማስተካከል እና ገጽታን ማሳመር", 350.0, "fixed", 1, 1, "1-2 working days", "1-2 የሥራ ቀናት"),
                    ("Facebook Content Planning", "የፌስቡክ ይዘት (ኮንተንት) እቅድ", "Facebook",
                     "Structured weekly content schedule and creative post outlines.",
                     "ለሳምንታዊ የገጽ ልጥፎች የሚሆን የይዘት እቅድ እና የርዕስ ዝግጅት", 450.0, "fixed", 1, 1, "2-3 working days", "2-3 የሥራ ቀናት"),
                    ("Facebook Advertising Campaign Assistance", "የፌስቡክ ማስታወቂያ ዘመቻ እገዛ", "Facebook",
                     "Meta Ads manager setup, audience definition, and campaign monitoring.",
                     "በሜታ ማስታወቂያ ማኔጀር በኩል የታለሙ ማስታወቂያዎችን የማስተካከል እገዛ", 750.0, "fixed", 1, 1, "3-5 working days", "3-5 የሥራ ቀናት"),
                    ("Facebook Business Promotion Consultation", "የፌስቡክ ቢዝነስ ማስተዋወቅ ምክክር", "Facebook",
                     "Guidance on building customer trust and organic engagement on Facebook.",
                     "በፌስቡክ ገጽዎ የታማኝ ደንበኞች ቁጥርን ለማሳደግ የሚሰጥ ተግባራዊ ምክክር", 400.0, "fixed", 1, 1, "1-2 working days", "1-2 የሥራ ቀናት"),

                    # YouTube
                    ("YouTube Channel Setup & Optimization", "የዩቲዩብ ቻናል ማዋቀር እና ማሻሻል", "YouTube",
                     "Channel branding, tags, about section, and playlist arrangement.",
                     "የቻናል ገጽታ፣ ታጎች፣ ስለ ቻናሉ የሚገልጽ ጽሁፍ እና አጫዋች ዝርዝሮችን ማስተካከል", 400.0, "fixed", 1, 1, "1-3 working days", "1-3 የሥራ ቀናት"),
                    ("YouTube Video SEO Guidance", "የዩቲዩብ ቪዲዮ SEO እገዛ", "YouTube",
                     "Title, description, and keyword optimization to rank in search results.",
                     "ቪዲዮዎች በፍለጋ ውጤቶች ውስጥ እንዲወጡ የርዕስ፣ መግለጫ እና የቁልፍ ቃላት ማስተካከያ", 350.0, "fixed", 1, 1, "1-2 working days", "1-2 የሥራ ቀናት"),
                    ("YouTube Thumbnail & Content Consultation", "የዩቲዩብ ምስል እና ይዘት ምክክር", "YouTube",
                     "Advice on high-click-through thumbnail design and viewer retention.",
                     "ተመልካችን የሚስቡ አጫጭር ምስሎችን (Thumbnails) እና ይዘቶችን የማዘጋጀት ምክክር", 300.0, "fixed", 1, 1, "1-2 working days", "1-2 የሥራ ቀናት"),
                    ("YouTube Advertising Campaign Assistance", "የዩቲዩብ ማስታወቂያ ዘመቻ እገዛ", "YouTube",
                     "Google Ads video campaign setup and budget allocation guidance.",
                     "በጉግል አድስ በኩል የዩቲዩብ ቪዲዮ ማስታወቂያዎችን የማዘጋጀት እገዛ", 850.0, "fixed", 1, 1, "3-5 working days", "3-5 የሥራ ቀናት"),
                ]

                await db.executemany("""
                    INSERT INTO services (
                        name_en, name_am, platform, description_en, description_am,
                        price, pricing_type, minimum_quantity, maximum_quantity,
                        estimated_duration_en, estimated_duration_am, is_active
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 1)
                """, services_seed)

        # 3. Seed Admins from config
        for admin_id in config.ADMIN_IDS:
            role = "owner" if config.is_owner(admin_id) else "admin"
            await db.execute("""
                INSERT OR IGNORE INTO admins (telegram_id, role, is_active)
                VALUES (?, ?, 1)
            """, (admin_id, role))

        await db.commit()
