def is_valid_name(text):
    allowed = set('abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789!@#$%')
    return all(char in allowed for char in text)


def format_ticket_id(db_id: int) -> int:
    """Convert database ID to display ticket number.
    Examples: 5 -> 105, 15 -> 115, 123 -> 1123"""
    return int(f"1{db_id:02d}")


def parse_ticket_id(display_id: int) -> int:
    """Convert display ticket number back to database ID.
    Examples: 105 -> 5, 115 -> 15, 1123 -> 123"""
    id_str = str(display_id)
    if not id_str.startswith('1') or len(id_str) < 3:
        raise ValueError(f"Invalid ticket number format: {display_id}")
    return int(id_str[1:])
