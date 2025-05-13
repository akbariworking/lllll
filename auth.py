import streamlit as st
import hashlib
import sqlite3
from utils import UserType

def hash_password(password):
    """Hash a password for storing."""
    return hashlib.sha256(password.encode()).hexdigest()

def authenticate(username, password, user_type):
    """
    Authenticate a user with the given credentials.
    
    Args:
        username (str): The username to check
        password (str): The password to check
        user_type (str): The type of user (Gym Manager, Trainer, or Athlete)
        
    Returns:
        bool: True if authentication successful, False otherwise
    """
    # Hash the password
    hashed_password = hash_password(password)
    
    # Connect to the database
    conn = sqlite3.connect("gym_management.db")
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    # Check credentials
    cursor.execute(
        "SELECT * FROM users WHERE username = ? AND password = ? AND user_type = ?",
        (username, hashed_password, user_type)
    )
    user = cursor.fetchone()
    
    # Additional checks for trainers - if they require approval
    trainer_approved = True
    if user and user_type == UserType.TRAINER.value:
        if user["trainer_approval_required"] and not user["trainer_approved"]:
            trainer_approved = False
    
    conn.close()
    
    if user and trainer_approved:
        # Set session state
        st.session_state.authenticated = True
        st.session_state.user_id = user["id"]
        st.session_state.username = user["username"]
        st.session_state.display_name = user["display_name"]
        st.session_state.user_type = user["user_type"]
        st.session_state.trainer_approval_required = user["trainer_approval_required"]
        st.session_state.trainer_approved = user["trainer_approved"] 
        return True
    elif user and not trainer_approved:
        # Trainer needs approval
        return "pending_approval"
    
    return False

def generate_username_suggestions(display_name, base_username):
    """
    Generate alternative username suggestions if the requested username is taken.
    
    Args:
        display_name (str): The user's display name
        base_username (str): The originally requested username
        
    Returns:
        list: List of 3 username suggestions
    """
    import random
    
    # Clean up the display name - remove spaces and special chars
    clean_name = ''.join(e for e in display_name if e.isalnum()).lower()
    
    suggestions = []
    
    # Suggestion 1: Add a random number between 1-99
    suggestions.append(f"{base_username}{random.randint(1, 99)}")
    
    # Suggestion 2: Use part of the display name + random number
    if len(clean_name) >= 3:
        suggestions.append(f"{clean_name[:3]}{base_username}{random.randint(1, 99)}")
    else:
        suggestions.append(f"{base_username}{random.randint(100, 999)}")
    
    # Suggestion 3: Add random chars
    random_chars = ''.join(random.choice('abcdefghijklmnopqrstuvwxyz') for _ in range(2))
    suggestions.append(f"{base_username}_{random_chars}")
    
    return suggestions

def is_username_taken(username):
    """
    Check if a username is already taken.
    
    Args:
        username (str): The username to check
        
    Returns:
        bool: True if username is taken, False otherwise
    """
    conn = sqlite3.connect("gym_management.db")
    cursor = conn.cursor()
    
    cursor.execute("SELECT COUNT(*) FROM users WHERE username = ?", (username,))
    count = cursor.fetchone()[0]
    
    conn.close()
    
    return count > 0

def signup(username, display_name, password, user_type, is_manually_registered=False):
    """
    Register a new user with the given credentials.
    
    Args:
        username (str): The username for the new user
        display_name (str): The display name for the new user
        password (str): The password for the new user
        user_type (str): The type of user (Gym Manager, Trainer, or Athlete)
        is_manually_registered (bool): Whether the user is being registered manually by a manager
        
    Returns:
        dict: A dictionary with results:
            - success (bool): True if registration successful, False otherwise
            - suggestions (list): Suggested usernames if the chosen one is taken
            - user_id (int): The ID of the newly created user if successful
    """
    # Hash the password
    hashed_password = hash_password(password)
    
    # Connect to the database
    conn = sqlite3.connect("gym_management.db")
    cursor = conn.cursor()
    
    # Check if username exists
    if is_username_taken(username):
        suggestions = generate_username_suggestions(display_name, username)
        return {
            "success": False, 
            "suggestions": suggestions,
            "error": "username_taken"
        }
    
    try:
        # Set approval requirements based on user type
        trainer_approval_required = False
        if user_type == UserType.TRAINER.value:
            trainer_approval_required = True
        
        # Insert new user
        cursor.execute(
            """INSERT INTO users 
               (username, display_name, password, user_type, 
                trainer_approval_required, manually_registered)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (username, display_name, hashed_password, user_type, 
             trainer_approval_required, is_manually_registered)
        )
        conn.commit()
        
        # Get the new user's ID
        cursor.execute("SELECT last_insert_rowid()")
        user_id = cursor.fetchone()[0]
        
        return {
            "success": True,
            "user_id": user_id
        }
    except sqlite3.IntegrityError:
        # Some other integrity error
        return {
            "success": False,
            "error": "database_error"
        }
    finally:
        conn.close()

def logout():
    """Log out the current user by clearing session state."""
    st.session_state.authenticated = False
    st.session_state.user_id = None
    st.session_state.username = None
    st.session_state.display_name = None
    st.session_state.user_type = None
    st.session_state.trainer_approval_required = None
    st.session_state.trainer_approved = None
    
    # Clean up any other session state variables we might have added
    keys_to_remove = []
    for key in st.session_state.keys():
        # Check if it's a string and starts with our prefixes
        if isinstance(key, str) and (key.startswith('athlete_') or 
                                   key.startswith('trainer_') or 
                                   key.startswith('gym_') or 
                                   key.startswith('chat_')):
            keys_to_remove.append(key)
    
    # Remove the keys (to avoid modifying the dictionary during iteration)
    for key in keys_to_remove:
        del st.session_state[key]
