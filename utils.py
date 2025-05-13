import streamlit as st
import pandas as pd
import io
from enum import Enum
from datetime import datetime, timedelta
from PIL import Image

class UserType(Enum):
    GYM_MANAGER = "Gym Manager"
    TRAINER = "Trainer"
    ATHLETE = "Athlete"

def check_session():
    """Check if user is authenticated and return to login if not."""
    if not st.session_state.get("authenticated", False):
        st.error("You need to login first.")
        st.stop()

def user_redirect():
    """Redirect user to appropriate page based on user type."""
    if not st.session_state.get("authenticated", False):
        return "login"
    
    user_type = st.session_state.get("user_type", None)
    
    if user_type == UserType.GYM_MANAGER.value:
        return "gym_manager"
    elif user_type == UserType.TRAINER.value:
        return "trainer"
    elif user_type == UserType.ATHLETE.value:
        return "athlete"
    else:
        return "login"

def format_time_ago(timestamp_str):
    """Format a timestamp as a human-readable 'time ago' string."""
    if not timestamp_str:
        return ""
    
    try:
        timestamp = datetime.strptime(timestamp_str, "%Y-%m-%d %H:%M:%S.%f")
    except ValueError:
        timestamp = datetime.strptime(timestamp_str, "%Y-%m-%d %H:%M:%S")
    
    now = datetime.now()
    diff = now - timestamp
    
    if diff < timedelta(minutes=1):
        return "just now"
    elif diff < timedelta(hours=1):
        minutes = int(diff.total_seconds() / 60)
        return f"{minutes} minute{'s' if minutes != 1 else ''} ago"
    elif diff < timedelta(days=1):
        hours = int(diff.total_seconds() / 3600)
        return f"{hours} hour{'s' if hours != 1 else ''} ago"
    elif diff < timedelta(days=7):
        days = int(diff.total_seconds() / 86400)
        return f"{days} day{'s' if days != 1 else ''} ago"
    else:
        return timestamp.strftime("%b %d, %Y")

def format_datetime(timestamp_str):
    """Format a timestamp as a human-readable datetime string."""
    if not timestamp_str:
        return ""
    
    try:
        timestamp = datetime.strptime(timestamp_str, "%Y-%m-%d %H:%M:%S.%f")
    except ValueError:
        timestamp = datetime.strptime(timestamp_str, "%Y-%m-%d %H:%M:%S")
    
    return timestamp.strftime("%b %d, %Y %I:%M %p")

def calculate_duration(start_time_str, end_time_str=None):
    """Calculate duration between two timestamps."""
    if not start_time_str:
        return ""
    
    try:
        start_time = datetime.strptime(start_time_str, "%Y-%m-%d %H:%M:%S.%f")
    except ValueError:
        start_time = datetime.strptime(start_time_str, "%Y-%m-%d %H:%M:%S")
    
    if end_time_str:
        try:
            end_time = datetime.strptime(end_time_str, "%Y-%m-%d %H:%M:%S.%f")
        except ValueError:
            end_time = datetime.strptime(end_time_str, "%Y-%m-%d %H:%M:%S")
    else:
        end_time = datetime.now()
    
    diff = end_time - start_time
    hours, remainder = divmod(diff.total_seconds(), 3600)
    minutes, seconds = divmod(remainder, 60)
    
    return f"{int(hours)}h {int(minutes)}m"

def get_image_bytes_from_upload(uploaded_file):
    """Convert uploaded file to bytes for database storage."""
    if uploaded_file is None:
        return None
    
    return uploaded_file.getvalue()

def get_image_from_bytes(image_bytes):
    """Convert image bytes from database to PIL Image for display."""
    if image_bytes is None:
        return None
    
    return Image.open(io.BytesIO(image_bytes))

def create_star_rating(rating, max_rating=5):
    """Create a star rating display."""
    if rating is None:
        rating = 0
    
    full_stars = int(rating)
    half_star = rating - full_stars >= 0.5
    empty_stars = max_rating - full_stars - (1 if half_star else 0)
    
    stars = "★" * full_stars
    if half_star:
        stars += "½"
    stars += "☆" * empty_stars
    
    return stars

def create_progress_bar(value, max_value=100):
    """Create a progress bar with percentage."""
    percentage = min(100, int((value / max_value) * 100)) if max_value > 0 else 0
    
    return f"{percentage}% | {'▓' * (percentage // 5)}{'░' * ((100 - percentage) // 5)}"
