"""
Utility functions for the finance application
"""
from datetime import datetime
from typing import Union, List
import json
from pathlib import Path

from .config import DATE_FORMAT, DATETIME_FORMAT, CURRENCY_SYMBOL, CSV_DATE_FORMATS


def format_currency(amount: float, symbol: str = CURRENCY_SYMBOL) -> str:
    """Format number as currency"""
    return f"{symbol}{abs(amount):,.2f}"


def format_percentage(value: float) -> str:
    """Format number as percentage"""
    return f"{value:.1f}%"


def parse_date(date_str: str) -> datetime:
    """Parse date string with multiple format support"""
    for fmt in CSV_DATE_FORMATS:
        try:
            return datetime.strptime(date_str, fmt)
        except ValueError:
            continue
    
    # Try ISO format
    try:
        return datetime.fromisoformat(date_str)
    except ValueError:
        raise ValueError(f"Unable to parse date: {date_str}")


def format_date(date: datetime, format_str: str = DATE_FORMAT) -> str:
    """Format datetime object to string"""
    return date.strftime(format_str)


def calculate_percentage_change(old_value: float, new_value: float) -> float:
    """Calculate percentage change between two values"""
    if old_value == 0:
        return 0 if new_value == 0 else 100
    return ((new_value - old_value) / abs(old_value)) * 100


def export_to_json(data: Union[dict, list], filepath: Path):
    """Export data to JSON file"""
    with open(filepath, 'w') as f:
        json.dump(data, f, indent=2, default=str)


def import_from_json(filepath: Path) -> Union[dict, list]:
    """Import data from JSON file"""
    with open(filepath, 'r') as f:
        return json.load(f)


def validate_amount(amount: Union[str, float]) -> float:
    """Validate and convert amount to float"""
    try:
        value = float(amount)
        if value == 0:
            raise ValueError("Amount cannot be zero")
        return value
    except (ValueError, TypeError):
        raise ValueError(f"Invalid amount: {amount}")


def sanitize_merchant_name(merchant: str) -> str:
    """Clean up merchant name"""
    # Remove extra whitespace
    merchant = ' '.join(merchant.split())
    # Capitalize properly
    merchant = merchant.title()
    return merchant


def chunk_list(lst: List, chunk_size: int) -> List[List]:
    """Split list into chunks"""
    return [lst[i:i + chunk_size] for i in range(0, len(lst), chunk_size)]


def get_date_range_display(start_date: datetime, end_date: datetime) -> str:
    """Get human-readable date range"""
    if start_date.date() == end_date.date():
        return format_date(start_date)
    
    if start_date.year == end_date.year:
        if start_date.month == end_date.month:
            return f"{start_date.strftime('%b %d')} - {end_date.strftime('%d, %Y')}"
        return f"{start_date.strftime('%b %d')} - {end_date.strftime('%b %d, %Y')}"
    
    return f"{format_date(start_date)} - {format_date(end_date)}"


def calculate_days_between(date1: datetime, date2: datetime) -> int:
    """Calculate days between two dates"""
    return abs((date2 - date1).days)


def is_valid_email(email: str) -> bool:
    """Basic email validation"""
    import re
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))


def truncate_string(text: str, max_length: int = 50, suffix: str = "...") -> str:
    """Truncate string to max length"""
    if len(text) <= max_length:
        return text
    return text[:max_length - len(suffix)] + suffix


def safe_divide(numerator: float, denominator: float, default: float = 0) -> float:
    """Safely divide two numbers"""
    try:
        return numerator / denominator if denominator != 0 else default
    except (TypeError, ZeroDivisionError):
        return default


def get_month_name(month: int) -> str:
    """Get month name from number (1-12)"""
    months = [
        "January", "February", "March", "April", "May", "June",
        "July", "August", "September", "October", "November", "December"
    ]
    return months[month - 1] if 1 <= month <= 12 else "Invalid"


def get_quarter(date: datetime) -> int:
    """Get quarter (1-4) from date"""
    return (date.month - 1) // 3 + 1


def get_financial_year(date: datetime, start_month: int = 1) -> int:
    """Get financial year based on start month"""
    if date.month >= start_month:
        return date.year
    return date.year - 1