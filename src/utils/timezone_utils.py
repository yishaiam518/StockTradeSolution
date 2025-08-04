#!/usr/bin/env python3
"""
Unified timezone utilities for consistent datetime handling across the system.
"""

import pandas as pd
from datetime import datetime, timezone
import pytz

# Default timezone for the system
DEFAULT_TIMEZONE = 'UTC'

def get_system_timezone():
    """Get the system timezone."""
    return DEFAULT_TIMEZONE

def make_timezone_naive(dt):
    """Convert any datetime to timezone-naive UTC."""
    if dt is None:
        return None
    
    # If it's already naive, assume it's UTC
    if dt.tzinfo is None:
        return dt
    
    # Convert to UTC and remove timezone info
    utc_dt = dt.astimezone(timezone.utc)
    return utc_dt.replace(tzinfo=None)

def make_timezone_aware(dt, tz=None):
    """Convert datetime to timezone-aware."""
    if dt is None:
        return None
    
    if tz is None:
        tz = get_system_timezone()
    
    # If already timezone-aware, convert to target timezone
    if dt.tzinfo is not None:
        return dt.astimezone(pytz.timezone(tz))
    
    # If naive, assume UTC and convert to target timezone
    utc_dt = dt.replace(tzinfo=timezone.utc)
    return utc_dt.astimezone(pytz.timezone(tz))

def normalize_dataframe_dates(df, date_column='date'):
    """Normalize all dates in a dataframe to timezone-naive UTC."""
    if df.empty or date_column not in df.columns:
        return df
    
    # Convert to datetime if needed
    if not pd.api.types.is_datetime64_any_dtype(df[date_column]):
        df[date_column] = pd.to_datetime(df[date_column])
    
    # Make all dates timezone-naive UTC
    df[date_column] = df[date_column].apply(make_timezone_naive)
    
    return df

def normalize_index_dates(df):
    """Normalize dataframe index dates to timezone-naive UTC."""
    if df.empty or not isinstance(df.index, pd.DatetimeIndex):
        return df
    
    # Convert index to timezone-naive UTC
    df.index = df.index.map(make_timezone_naive)
    
    return df

def safe_date_comparison(date1, date2):
    """Safely compare two dates by normalizing them first."""
    if date1 is None or date2 is None:
        return False
    
    # Normalize both dates
    norm_date1 = make_timezone_naive(date1)
    norm_date2 = make_timezone_naive(date2)
    
    return norm_date1 == norm_date2

def safe_date_range_filter(df, start_date, end_date, date_column='date'):
    """Safely filter dataframe by date range with timezone normalization."""
    if df.empty:
        return df
    
    # Normalize the dataframe dates
    df = normalize_dataframe_dates(df, date_column)
    
    # Normalize the filter dates
    start_date = make_timezone_naive(start_date)
    end_date = make_timezone_naive(end_date)
    
    # Apply filter
    mask = (df[date_column] >= start_date) & (df[date_column] <= end_date)
    return df[mask]

def format_date_for_display(dt, format_str='%Y-%m-%d'):
    """Format a datetime for display, handling timezone conversion."""
    if dt is None:
        return ""
    
    # Convert to system timezone for display
    display_dt = make_timezone_aware(dt)
    return display_dt.strftime(format_str)

def parse_date_string(date_str, format_str='%Y-%m-%d'):
    """Parse a date string and return timezone-naive UTC datetime."""
    if not date_str:
        return None
    
    dt = datetime.strptime(date_str, format_str)
    return make_timezone_naive(dt) 