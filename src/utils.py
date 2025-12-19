# src/utils.py

# Map statuses to Hex Colors for the Map
STATUS_COLORS = {
    "new": "#00FF00",       # Green
    "contacted": "#3366FF", # Blue
    "interested": "#FFD700",# Gold
    "closed": "#808080",    # Grey
    "ignored": "#FF0000"    # Red
}

def get_status_color(status: str) -> str:
    return STATUS_COLORS.get(status, "#00FF00")

def format_phone_link(phone: str) -> str:
    """Returns a clickable tel: link string"""
    if not phone:
        return None
    clean_phone = ''.join(filter(str.isdigit, phone))
    return f"tel:{clean_phone}"