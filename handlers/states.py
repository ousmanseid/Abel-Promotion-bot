"""
Finite State Machine (FSM) States for Abel Promotion bot.
"""

from aiogram.fsm.state import State, StatesGroup

class OrderCreationStates(StatesGroup):
    waiting_for_link = State()
    waiting_for_quantity = State()
    waiting_for_notes = State()
    confirm_order = State()

class PaymentSubmissionStates(StatesGroup):
    waiting_for_screenshot = State()
    waiting_for_reference = State()

class SupportTicketStates(StatesGroup):
    waiting_for_message = State()

class AdminServiceCreateStates(StatesGroup):
    waiting_for_platform = State()
    waiting_for_name_en = State()
    waiting_for_name_am = State()
    waiting_for_description = State()
    waiting_for_price = State()
    waiting_for_duration = State()

class AdminServicePriceStates(StatesGroup):
    waiting_for_new_price = State()

class AdminPaymentRejectStates(StatesGroup):
    waiting_for_reason = State()

class AdminOrderRejectStates(StatesGroup):
    waiting_for_reason = State()

class AdminMessageCustomerStates(StatesGroup):
    waiting_for_message = State()

class CustomerReplyMessageStates(StatesGroup):
    waiting_for_message = State()

class AdminPaymentSettingsStates(StatesGroup):
    waiting_for_holder = State()
    waiting_for_number = State()

class AdminSupportReplyStates(StatesGroup):
    waiting_for_response = State()
