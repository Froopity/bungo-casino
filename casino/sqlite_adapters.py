from datetime import datetime
import sqlite3

def adapt_datetime(dt):
    """Converts datetime objects to strings for storage."""
    return dt.strftime('%Y-%m-%d %H:%M:%S')

def convert_datetime(s):
    """Converts strings back to datetime objects."""
    return datetime.strptime(s.decode('utf-8'), '%Y-%m-%d %H:%M:%S')

def register_adapters():
  sqlite3.register_adapter(datetime, adapt_datetime)
  sqlite3.register_converter('timestamp', convert_datetime)
