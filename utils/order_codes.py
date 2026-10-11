"""
Unique order and ticket code generation utilities.
"""

import time
import random

def format_order_code(order_id: int) -> str:
    """Format numeric internal ID into standard AB-1001 format."""
    return f"AB-{1000 + order_id}"

def format_ticket_code(ticket_id: int) -> str:
    """Format numeric internal ID into standard TICKET-101 format."""
    return f"TICKET-{100 + ticket_id}"

def generate_fallback_order_code() -> str:
    """Generate a pseudo-unique code if pre-insert generation is needed."""
    timestamp_suffix = str(int(time.time()))[-4:]
    rand_suffix = random.randint(10, 99)
    return f"AB-{timestamp_suffix}{rand_suffix}"
