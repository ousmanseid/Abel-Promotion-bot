import os
from pathlib import Path
from typing import Set
from dotenv import load_dotenv

# Load environment variables from .env file if present
load_dotenv()

BASE_DIR = Path(__file__).resolve().parent

# Bot credentials
BOT_TOKEN: str = os.getenv("BOT_TOKEN", "").strip()

# Admin IDs
def _parse_admin_ids(raw_ids: str) -> Set[int]:
    ids: Set[int] = set()
    if not raw_ids:
        return ids
    for part in raw_ids.split(","):
        part = part.strip()
        if part.isdigit():
            ids.add(int(part))
    return ids

ADMIN_IDS: Set[int] = _parse_admin_ids(os.getenv("ADMIN_IDS", ""))

_raw_owner = os.getenv("OWNER_ID", "").strip()
OWNER_ID: int = int(_raw_owner) if _raw_owner.isdigit() else (next(iter(ADMIN_IDS)) if ADMIN_IDS else 0)

# Always ensure owner is in ADMIN_IDS
if OWNER_ID > 0:
    ADMIN_IDS.add(OWNER_ID)

# Database
DATABASE_PATH: Path = BASE_DIR / os.getenv("DATABASE_PATH", "data/abel_promotion.db")

# Default language
DEFAULT_LANGUAGE: str = os.getenv("DEFAULT_LANGUAGE", "en").strip().lower()
if DEFAULT_LANGUAGE not in ("en", "am"):
    DEFAULT_LANGUAGE = "en"

# Support contact info
SUPPORT_HANDLE: str = os.getenv("SUPPORT_CHANNEL", "@AbelPromotionSupport").strip()

def is_admin(user_id: int) -> bool:
    """Check if given Telegram user ID is an authorized administrator."""
    return user_id in ADMIN_IDS

def is_owner(user_id: int) -> bool:
    """Check if given Telegram user ID is the owner."""
    return OWNER_ID > 0 and user_id == OWNER_ID
