# Telegram Account Management Bot - Date Handling Utility
# Handle date formatting and parsing for account categorization

from datetime import datetime, date
from typing import Tuple, Optional
from pathlib import Path


def get_today_date() -> str:
    """Get today's date in YYYY-MM-DD format"""
    return datetime.utcnow().strftime('%Y-%m-%d')


def get_current_year() -> str:
    """Get current year as string"""
    return str(datetime.utcnow().year)


def get_current_month() -> str:
    """Get current month as zero-padded string"""
    return str(datetime.utcnow().month).zfill(2)


def get_current_day() -> str:
    """Get current day as zero-padded string"""
    return str(datetime.utcnow().day).zfill(2)


def format_date(input_date: date, format: str = 'YYYY/MM/DD') -> str:
    """
    Format a date in the specified format.
    
    Args:
        input_date: Date object to format
        format: Output format ('YYYY/MM/DD', 'YYYY-MM-DD', 'DD/MM/YYYY', etc.)
        
    Returns:
        Formatted date string
    """
    year = str(input_date.year)
    month = str(input_date.month).zfill(2)
    day = str(input_date.day).zfill(2)
    
    if format == 'YYYY/MM/DD':
        return f"{year}/{month}/{day}"
    elif format == 'YYYY-MM-DD':
        return f"{year}-{month}-{day}"
    elif format == 'DD/MM/YYYY':
        return f"{day}/{month}/{year}"
    elif format == 'MM/DD/YYYY':
        return f"{month}/{day}/{year}"
    elif format == 'YYYY':
        return year
    elif format == 'MM':
        return month
    elif format == 'DD':
        return day
    else:
        return f"{year}-{month}-{day}"


def parse_date_string(date_str: str) -> Optional[date]:
    """
    Parse a date string in various formats.
    
    Supported formats:
    - YYYY-MM-DD
    - YYYY/MM/DD
    - DD/MM/YYYY
    - MM/DD/YYYY
    
    Args:
        date_str: Date string to parse
        
    Returns:
        Date object or None if parsing fails
    """
    formats = [
        '%Y-%m-%d',
        '%Y/%m/%d',
        '%d/%m/%Y',
        '%m/%d/%Y',
        '%Y%m%d',
    ]
    
    for fmt in formats:
        try:
            return datetime.strptime(date_str, fmt).date()
        except ValueError:
            continue
    
    return None


def get_date_components(date_str: str) -> Tuple[str, str, str]:
    """
    Extract year, month, day from a date string.
    
    Args:
        date_str: Date string in YYYY-MM-DD or YYYY/MM/DD format
        
    Returns:
        Tuple of (year, month, day) as strings
    """
    parsed = parse_date_string(date_str)
    
    if not parsed:
        raise ValueError(f"Invalid date format: {date_str}")
    
    return (
        str(parsed.year),
        str(parsed.month).zfill(2),
        str(parsed.day).zfill(2)
    )


def create_date_path(year: str, month: str, day: str) -> Path:
    """
    Create a Path object for date-based organization.
    
    Args:
        year: Year string (YYYY)
        month: Month string (MM)
        day: Day string (DD)
        
    Returns:
        Path object for the date directory
    """
    base_dir = Path(__file__).parent.parent.parent / 'data' / 'sessions'
    return base_dir / year / month / day


def get_date_range(start_date: date, end_date: date) -> list:
    """
    Get a list of dates between start and end dates.
    
    Args:
        start_date: Start date
        end_date: End date
        
    Returns:
        List of dates in the range
    """
    dates = []
    current = start_date
    
    while current <= end_date:
        dates.append(current)
        current = date.fromordinal(current.toordinal() + 1)
    
    return dates


def format_date_for_display(date_str: str) -> str:
    """
    Format a date string for human-readable display.
    
    Args:
        date_str: Date string in YYYY-MM-DD format
        
    Returns:
        Formatted date string for display
    """
    parsed = parse_date_string(date_str)
    
    if not parsed:
        return date_str
    
    return parsed.strftime('%B %d, %Y')


def get_relative_date(date_str: str) -> str:
    """
    Get a relative date description.
    
    Args:
        date_str: Date string in YYYY-MM-DD format
        
    Returns:
        Relative date description (e.g., "Today", "Yesterday", "3 days ago")
    """
    parsed = parse_date_string(date_str)
    
    if not parsed:
        return date_str
    
    today = date.today()
    delta = (today - parsed).days
    
    if delta == 0:
        return "Today"
    elif delta == 1:
        return "Yesterday"
    elif delta == -1:
        return "Tomorrow"
    elif delta < 7:
        return f"{delta} days ago"
    elif delta < 14:
        return "Last week"
    elif delta < 30:
        return f"{delta // 7} weeks ago"
    elif delta < 60:
        return "Last month"
    elif delta < 365:
        return f"{delta // 30} months ago"
    else:
        return f"{delta // 365} years ago"


if __name__ == '__main__':
    # Test the module
    today = get_today_date()
    print(f"Today: {today}")
    
    components = get_date_components(today)
    print(f"Components: {components}")
    
    print(f"Formatted for display: {format_date_for_display(today)}")
    print(f"Relative: {get_relative_date(today)}")
    
    # Test date range
    start = date(2024, 1, 1)
    end = date(2024, 1, 5)
    date_range = get_date_range(start, end)
    print(f"Date range: {[d.isoformat() for d in date_range]}")
