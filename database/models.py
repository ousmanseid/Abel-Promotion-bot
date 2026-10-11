"""
Data models and dataclasses for Abel Promotion bot.
"""

from dataclasses import dataclass
from typing import Optional

@dataclass
class User:
    id: int
    telegram_id: int
    username: Optional[str]
    first_name: Optional[str]
    language: str = "en"
    created_at: Optional[str] = None
    is_blocked: bool = False

@dataclass
class Admin:
    id: int
    telegram_id: int
    role: str = "admin"
    created_at: Optional[str] = None
    is_active: bool = True

@dataclass
class Service:
    id: int
    name_en: str
    name_am: str
    platform: str
    description_en: Optional[str]
    description_am: Optional[str]
    price: float
    pricing_type: str = "fixed"
    minimum_quantity: int = 1
    maximum_quantity: int = 100000
    estimated_duration_en: str = "1-2 business days"
    estimated_duration_am: str = "1-2 የሥራ ቀናት"
    is_active: bool = True
    created_at: Optional[str] = None
    updated_at: Optional[str] = None

    def get_name(self, lang: str = "en") -> str:
        return self.name_am if lang == "am" else self.name_en

    def get_description(self, lang: str = "en") -> str:
        return self.description_am if lang == "am" else (self.description_en or "")

    def get_duration(self, lang: str = "en") -> str:
        return self.estimated_duration_am if lang == "am" else self.estimated_duration_en

@dataclass
class Order:
    id: int
    order_code: str
    user_id: int
    service_id: int
    service_name_snapshot: str
    unit_price_snapshot: float
    quantity: int
    total_price: float
    target_link: str
    customer_notes: Optional[str]
    status: str = "pending_payment"
    approved_by: Optional[int] = None
    approved_at: Optional[str] = None
    rejection_reason: Optional[str] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None

@dataclass
class Payment:
    id: int
    order_id: int
    payment_method: str
    expected_amount: float
    transaction_reference: Optional[str]
    screenshot_file_id: Optional[str]
    status: str = "submitted"
    submitted_at: Optional[str] = None
    verified_by: Optional[int] = None
    verified_at: Optional[str] = None
    verification_notes: Optional[str] = None
    rejection_reason: Optional[str] = None

@dataclass
class PaymentMethod:
    id: int
    method_code: str
    method_name: str
    account_holder: str
    account_number: str
    instructions_en: Optional[str]
    instructions_am: Optional[str]
    is_active: bool = True

    def get_instructions(self, lang: str = "en") -> str:
        return self.instructions_am if lang == "am" else (self.instructions_en or "")

@dataclass
class OrderStatusHistory:
    id: int
    order_id: int
    previous_status: Optional[str]
    new_status: str
    changed_by: Optional[int]
    reason: Optional[str]
    created_at: Optional[str] = None

@dataclass
class OrderMessage:
    id: int
    order_id: int
    sender_id: int
    sender_role: str  # 'admin' or 'customer'
    message_text: str
    created_at: Optional[str] = None

@dataclass
class SupportTicket:
    id: int
    ticket_code: str
    user_id: int
    order_id: Optional[int]
    message: str
    admin_response: Optional[str]
    status: str = "Open"
    created_at: Optional[str] = None
    closed_at: Optional[str] = None

@dataclass
class AuditLog:
    id: int
    admin_telegram_id: int
    action: str
    entity_type: Optional[str]
    entity_id: Optional[str]
    details: Optional[str]
    created_at: Optional[str] = None
