# modules/schema.py
import copy

CANONICAL_SCHEMA = {
    "document_type": None,      # e.g., "Air Waybill", "Invoice", "Form"
    "document_id": None,        # Document identification string
    "date": None,               # Date string (YYYY-MM-DD format preferred)
    "shipper_name": None,       # Shipper / Vendor / Sender name
    "consignee_name": None,     # Consignee / Customer / Receiver name
    "origin": None,             # Port or city of origin
    "destination": None,        # Port or city of destination
    "total_amount": None,       # Total monetary value (float)
    "total_weight_kg": None,    # Total gross weight in kg (float)
    "line_items": [],           # List of line-item dicts
    "has_signature": False,     # Task C visual element flag
    "has_stamp": False          # Task C visual element flag
}

def get_empty_schema():
    """Returns a deep copy of the empty canonical schema template."""
    return copy.deepcopy(CANONICAL_SCHEMA)