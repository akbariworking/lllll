import sqlite3
import os
import pandas as pd
import streamlit as st
from datetime import datetime

# Database file
DB_FILE = "gym_management.db"

def get_connection():
    """Create and return a database connection"""
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row  # This enables accessing columns by name
    return conn

def init_db():
    """Initialize the database with necessary tables if they don't exist"""
    conn = get_connection()
    cursor = conn.cursor()
    
    # Create users table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        display_name TEXT NOT NULL,
        password TEXT NOT NULL,
        user_type TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        profile_complete BOOLEAN DEFAULT FALSE,
        trainer_approval_required BOOLEAN DEFAULT FALSE,
        trainer_approved BOOLEAN DEFAULT FALSE,
        trainer_approval_date TIMESTAMP,
        membership_expiry_date TIMESTAMP,
        manually_registered BOOLEAN DEFAULT FALSE
    )
    ''')
    
    # Create gym_details table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS gym_details (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        gym_name TEXT,
        license_document BLOB,
        license_verified BOOLEAN DEFAULT FALSE,
        address TEXT,
        contact_number TEXT,
        email TEXT,
        FOREIGN KEY (user_id) REFERENCES users(id)
    )
    ''')
    
    # Create trainer_details table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS trainer_details (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        full_name TEXT,
        certification_document BLOB,
        certification_verified BOOLEAN DEFAULT FALSE,
        specialization TEXT,
        experience INTEGER,
        gym_id INTEGER,
        FOREIGN KEY (user_id) REFERENCES users(id),
        FOREIGN KEY (gym_id) REFERENCES gym_details(id)
    )
    ''')
    
    # Create athlete_details table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS athlete_details (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        full_name TEXT,
        age INTEGER,
        gender TEXT,
        weight REAL,
        height REAL,
        goals TEXT,
        medical_conditions TEXT,
        gym_id INTEGER,
        trainer_id INTEGER,
        FOREIGN KEY (user_id) REFERENCES users(id),
        FOREIGN KEY (gym_id) REFERENCES gym_details(id),
        FOREIGN KEY (trainer_id) REFERENCES trainer_details(id)
    )
    ''')
    
    # Create membership_plans table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS membership_plans (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        gym_id INTEGER NOT NULL,
        plan_name TEXT NOT NULL,
        duration INTEGER NOT NULL, -- duration in months
        price REAL NOT NULL,
        description TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (gym_id) REFERENCES gym_details(id)
    )
    ''')
    
    # Create memberships table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS memberships (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        athlete_id INTEGER NOT NULL,
        plan_id INTEGER NOT NULL,
        start_date DATE NOT NULL,
        end_date DATE NOT NULL,
        payment_status TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (athlete_id) REFERENCES athlete_details(id),
        FOREIGN KEY (plan_id) REFERENCES membership_plans(id)
    )
    ''')
    
    # Create gym_visits table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS gym_visits (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        athlete_id INTEGER NOT NULL,
        gym_id INTEGER NOT NULL,
        check_in_time TIMESTAMP NOT NULL,
        check_out_time TIMESTAMP,
        FOREIGN KEY (athlete_id) REFERENCES athlete_details(id),
        FOREIGN KEY (gym_id) REFERENCES gym_details(id)
    )
    ''')
    
    # Create reviews table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS reviews (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        athlete_id INTEGER NOT NULL,
        gym_id INTEGER,
        trainer_id INTEGER,
        rating INTEGER NOT NULL,
        comment TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (athlete_id) REFERENCES athlete_details(id),
        FOREIGN KEY (gym_id) REFERENCES gym_details(id),
        FOREIGN KEY (trainer_id) REFERENCES trainer_details(id)
    )
    ''')
    
    # Create chat_messages table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS chat_messages (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        sender_id INTEGER NOT NULL,
        receiver_id INTEGER NOT NULL,
        message TEXT NOT NULL,
        read BOOLEAN DEFAULT FALSE,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (sender_id) REFERENCES users(id),
        FOREIGN KEY (receiver_id) REFERENCES users(id)
    )
    ''')
    
    # Create support_tickets table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS support_tickets (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        athlete_id INTEGER NOT NULL,
        gym_id INTEGER NOT NULL,
        subject TEXT NOT NULL,
        message TEXT NOT NULL,
        status TEXT DEFAULT 'open',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (athlete_id) REFERENCES athlete_details(id),
        FOREIGN KEY (gym_id) REFERENCES gym_details(id)
    )
    ''')
    
    # Create support_responses table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS support_responses (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        ticket_id INTEGER NOT NULL,
        responder_id INTEGER NOT NULL,
        message TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (ticket_id) REFERENCES support_tickets(id),
        FOREIGN KEY (responder_id) REFERENCES users(id)
    )
    ''')
    
    conn.commit()
    conn.close()

def get_user_data(username, user_type):
    """Retrieve user data by username and user type"""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute(
        "SELECT id, username, user_type, profile_complete FROM users WHERE username = ? AND user_type = ?",
        (username, user_type)
    )
    user = cursor.fetchone()
    
    conn.close()
    
    if user:
        return dict(user)
    return None

def get_user_by_id(user_id):
    """Retrieve user data by user ID"""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute(
        "SELECT id, username, user_type, profile_complete FROM users WHERE id = ?",
        (user_id,)
    )
    user = cursor.fetchone()
    
    conn.close()
    
    if user:
        return dict(user)
    return None

def save_gym_details(user_id, gym_name, license_document, address, contact_number, email):
    """Save or update gym details"""
    conn = get_connection()
    cursor = conn.cursor()
    
    # Check if gym details already exist for this user
    cursor.execute("SELECT id FROM gym_details WHERE user_id = ?", (user_id,))
    gym = cursor.fetchone()
    
    if gym:
        # Update existing gym details
        cursor.execute(
            """
            UPDATE gym_details 
            SET gym_name = ?, license_document = ?, address = ?, 
                contact_number = ?, email = ?
            WHERE user_id = ?
            """,
            (gym_name, license_document, address, contact_number, email, user_id)
        )
    else:
        # Insert new gym details
        cursor.execute(
            """
            INSERT INTO gym_details 
            (user_id, gym_name, license_document, address, contact_number, email)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (user_id, gym_name, license_document, address, contact_number, email)
        )
    
    # Update profile_complete in users table
    cursor.execute(
        "UPDATE users SET profile_complete = TRUE WHERE id = ?",
        (user_id,)
    )
    
    conn.commit()
    conn.close()
    
    return True

def get_gym_details(user_id):
    """Get gym details for a gym manager"""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute(
        """
        SELECT id, gym_name, license_verified, address, contact_number, email
        FROM gym_details WHERE user_id = ?
        """,
        (user_id,)
    )
    gym = cursor.fetchone()
    
    conn.close()
    
    if gym:
        return dict(gym)
    return None

def save_trainer_details(user_id, full_name, certification_document, specialization, experience, gym_id=None):
    """Save or update trainer details"""
    conn = get_connection()
    cursor = conn.cursor()
    
    # Check if trainer details already exist for this user
    cursor.execute("SELECT id FROM trainer_details WHERE user_id = ?", (user_id,))
    trainer = cursor.fetchone()
    
    if trainer:
        # Update existing trainer details
        cursor.execute(
            """
            UPDATE trainer_details 
            SET full_name = ?, certification_document = ?, specialization = ?, 
                experience = ?, gym_id = ?
            WHERE user_id = ?
            """,
            (full_name, certification_document, specialization, experience, gym_id, user_id)
        )
    else:
        # Insert new trainer details
        cursor.execute(
            """
            INSERT INTO trainer_details 
            (user_id, full_name, certification_document, specialization, experience, gym_id)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (user_id, full_name, certification_document, specialization, experience, gym_id)
        )
    
    # Update profile_complete in users table
    cursor.execute(
        "UPDATE users SET profile_complete = TRUE WHERE id = ?",
        (user_id,)
    )
    
    conn.commit()
    conn.close()
    
    return True

def get_trainer_details(user_id):
    """Get trainer details for a trainer"""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute(
        """
        SELECT t.id, t.full_name, t.certification_verified, t.specialization, t.experience, 
               t.gym_id, g.gym_name
        FROM trainer_details t
        LEFT JOIN gym_details g ON t.gym_id = g.id
        WHERE t.user_id = ?
        """,
        (user_id,)
    )
    trainer = cursor.fetchone()
    
    conn.close()
    
    if trainer:
        return dict(trainer)
    return None

def save_athlete_details(user_id, full_name, age, gender, weight, height, goals, medical_conditions, gym_id=None, trainer_id=None):
    """Save or update athlete details"""
    conn = get_connection()
    cursor = conn.cursor()
    
    # Check if athlete details already exist for this user
    cursor.execute("SELECT id FROM athlete_details WHERE user_id = ?", (user_id,))
    athlete = cursor.fetchone()
    
    if athlete:
        # Update existing athlete details
        cursor.execute(
            """
            UPDATE athlete_details 
            SET full_name = ?, age = ?, gender = ?, weight = ?, height = ?,
                goals = ?, medical_conditions = ?, gym_id = ?, trainer_id = ?
            WHERE user_id = ?
            """,
            (full_name, age, gender, weight, height, goals, medical_conditions, gym_id, trainer_id, user_id)
        )
    else:
        # Insert new athlete details
        cursor.execute(
            """
            INSERT INTO athlete_details 
            (user_id, full_name, age, gender, weight, height, goals, medical_conditions, gym_id, trainer_id)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (user_id, full_name, age, gender, weight, height, goals, medical_conditions, gym_id, trainer_id)
        )
    
    # Update profile_complete in users table
    cursor.execute(
        "UPDATE users SET profile_complete = TRUE WHERE id = ?",
        (user_id,)
    )
    
    conn.commit()
    conn.close()
    
    return True

def get_athlete_details(user_id):
    """Get athlete details for an athlete"""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute(
        """
        SELECT a.id, a.full_name, a.age, a.gender, a.weight, a.height, a.goals, a.medical_conditions,
               a.gym_id, g.gym_name, a.trainer_id, t.full_name as trainer_name
        FROM athlete_details a
        LEFT JOIN gym_details g ON a.gym_id = g.id
        LEFT JOIN trainer_details t ON a.trainer_id = t.id
        WHERE a.user_id = ?
        """,
        (user_id,)
    )
    athlete = cursor.fetchone()
    
    conn.close()
    
    if athlete:
        return dict(athlete)
    return None

def get_all_gyms():
    """Get a list of all gyms"""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute(
        """
        SELECT id, gym_name, address
        FROM gym_details
        """
    )
    gyms = cursor.fetchall()
    
    conn.close()
    
    return [dict(gym) for gym in gyms]

def get_trainers_by_gym(gym_id):
    """Get a list of all trainers for a specific gym"""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute(
        """
        SELECT id, full_name, specialization, experience
        FROM trainer_details
        WHERE gym_id = ?
        """,
        (gym_id,)
    )
    trainers = cursor.fetchall()
    
    conn.close()
    
    return [dict(trainer) for trainer in trainers]

def save_membership_plan(gym_id, plan_name, duration, price, description):
    """Save a new membership plan"""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute(
        """
        INSERT INTO membership_plans
        (gym_id, plan_name, duration, price, description)
        VALUES (?, ?, ?, ?, ?)
        """,
        (gym_id, plan_name, duration, price, description)
    )
    
    conn.commit()
    conn.close()
    
    return True

def get_membership_plans(gym_id):
    """Get all membership plans for a gym"""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute(
        """
        SELECT id, plan_name, duration, price, description
        FROM membership_plans
        WHERE gym_id = ?
        """,
        (gym_id,)
    )
    plans = cursor.fetchall()
    
    conn.close()
    
    return [dict(plan) for plan in plans]

def record_gym_visit(athlete_id, gym_id):
    """Record a gym visit (check-in)"""
    conn = get_connection()
    cursor = conn.cursor()
    
    check_in_time = datetime.now()
    
    cursor.execute(
        """
        INSERT INTO gym_visits
        (athlete_id, gym_id, check_in_time)
        VALUES (?, ?, ?)
        """,
        (athlete_id, gym_id, check_in_time)
    )
    
    conn.commit()
    conn.close()
    
    return True

def checkout_gym_visit(visit_id):
    """Record a gym checkout"""
    conn = get_connection()
    cursor = conn.cursor()
    
    check_out_time = datetime.now()
    
    cursor.execute(
        """
        UPDATE gym_visits
        SET check_out_time = ?
        WHERE id = ?
        """,
        (check_out_time, visit_id)
    )
    
    conn.commit()
    conn.close()
    
    return True

def get_active_visits(athlete_id):
    """Get active (not checked out) gym visits for an athlete"""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute(
        """
        SELECT v.id, v.check_in_time, g.gym_name
        FROM gym_visits v
        JOIN gym_details g ON v.gym_id = g.id
        WHERE v.athlete_id = ? AND v.check_out_time IS NULL
        """,
        (athlete_id,)
    )
    visits = cursor.fetchall()
    
    conn.close()
    
    return [dict(visit) for visit in visits]

def get_visit_history(athlete_id, limit=10):
    """Get gym visit history for an athlete"""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute(
        """
        SELECT v.id, v.check_in_time, v.check_out_time, g.gym_name
        FROM gym_visits v
        JOIN gym_details g ON v.gym_id = g.id
        WHERE v.athlete_id = ? AND v.check_out_time IS NOT NULL
        ORDER BY v.check_in_time DESC
        LIMIT ?
        """,
        (athlete_id, limit)
    )
    visits = cursor.fetchall()
    
    conn.close()
    
    return [dict(visit) for visit in visits]

def add_review(athlete_id, gym_id=None, trainer_id=None, rating=None, comment=None):
    """Add a review for a gym or trainer"""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute(
        """
        INSERT INTO reviews
        (athlete_id, gym_id, trainer_id, rating, comment)
        VALUES (?, ?, ?, ?, ?)
        """,
        (athlete_id, gym_id, trainer_id, rating, comment)
    )
    
    conn.commit()
    conn.close()
    
    return True

def get_gym_reviews(gym_id):
    """Get reviews for a specific gym"""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute(
        """
        SELECT r.id, r.rating, r.comment, r.created_at, a.full_name as athlete_name
        FROM reviews r
        JOIN athlete_details a ON r.athlete_id = a.id
        WHERE r.gym_id = ?
        ORDER BY r.created_at DESC
        """,
        (gym_id,)
    )
    reviews = cursor.fetchall()
    
    conn.close()
    
    return [dict(review) for review in reviews]

def get_trainer_reviews(trainer_id):
    """Get reviews for a specific trainer"""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute(
        """
        SELECT r.id, r.rating, r.comment, r.created_at, a.full_name as athlete_name
        FROM reviews r
        JOIN athlete_details a ON r.athlete_id = a.id
        WHERE r.trainer_id = ?
        ORDER BY r.created_at DESC
        """,
        (trainer_id,)
    )
    reviews = cursor.fetchall()
    
    conn.close()
    
    return [dict(review) for review in reviews]

def send_message(sender_id, receiver_id, message):
    """Send a chat message"""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute(
        """
        INSERT INTO chat_messages
        (sender_id, receiver_id, message)
        VALUES (?, ?, ?)
        """,
        (sender_id, receiver_id, message)
    )
    
    conn.commit()
    conn.close()
    
    return True

def get_messages(user1_id, user2_id, limit=50):
    """Get chat messages between two users"""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute(
        """
        SELECT id, sender_id, receiver_id, message, created_at
        FROM chat_messages
        WHERE (sender_id = ? AND receiver_id = ?) OR (sender_id = ? AND receiver_id = ?)
        ORDER BY created_at DESC
        LIMIT ?
        """,
        (user1_id, user2_id, user2_id, user1_id, limit)
    )
    messages = cursor.fetchall()
    
    # Mark messages as read
    cursor.execute(
        """
        UPDATE chat_messages
        SET read = TRUE
        WHERE receiver_id = ? AND sender_id = ? AND read = FALSE
        """,
        (user1_id, user2_id)
    )
    
    conn.commit()
    conn.close()
    
    messages = [dict(message) for message in messages]
    messages.reverse()  # Show oldest messages first
    
    return messages

def get_contacts(user_id):
    """Get a list of contacts (people the user has chatted with)"""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute(
        """
        SELECT DISTINCT 
            CASE
                WHEN sender_id = ? THEN receiver_id
                ELSE sender_id
            END as contact_id
        FROM chat_messages
        WHERE sender_id = ? OR receiver_id = ?
        """,
        (user_id, user_id, user_id)
    )
    contact_ids = [row['contact_id'] for row in cursor.fetchall()]
    
    contacts = []
    for contact_id in contact_ids:
        # Get user info
        cursor.execute(
            """
            SELECT u.id, u.username, u.user_type
            FROM users u
            WHERE u.id = ?
            """,
            (contact_id,)
        )
        user = cursor.fetchone()
        
        if user:
            contact_info = dict(user)
            
            # Get additional info based on user type
            if user['user_type'] == 'Gym Manager':
                cursor.execute(
                    "SELECT gym_name FROM gym_details WHERE user_id = ?",
                    (contact_id,)
                )
                gym = cursor.fetchone()
                if gym:
                    contact_info['name'] = gym['gym_name']
                else:
                    contact_info['name'] = user['username']
                    
            elif user['user_type'] == 'Trainer':
                cursor.execute(
                    "SELECT full_name FROM trainer_details WHERE user_id = ?",
                    (contact_id,)
                )
                trainer = cursor.fetchone()
                if trainer:
                    contact_info['name'] = trainer['full_name']
                else:
                    contact_info['name'] = user['username']
                    
            elif user['user_type'] == 'Athlete':
                cursor.execute(
                    "SELECT full_name FROM athlete_details WHERE user_id = ?",
                    (contact_id,)
                )
                athlete = cursor.fetchone()
                if athlete:
                    contact_info['name'] = athlete['full_name']
                else:
                    contact_info['name'] = user['username']
            
            # Get unread messages count
            cursor.execute(
                """
                SELECT COUNT(*) as unread_count
                FROM chat_messages
                WHERE sender_id = ? AND receiver_id = ? AND read = FALSE
                """,
                (contact_id, user_id)
            )
            unread = cursor.fetchone()
            contact_info['unread_count'] = unread['unread_count']
            
            contacts.append(contact_info)
    
    conn.close()
    
    return contacts

def create_support_ticket(athlete_id, gym_id, subject, message):
    """Create a new support ticket"""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute(
        """
        INSERT INTO support_tickets
        (athlete_id, gym_id, subject, message)
        VALUES (?, ?, ?, ?)
        """,
        (athlete_id, gym_id, subject, message)
    )
    
    conn.commit()
    conn.close()
    
    return True

def get_support_tickets(gym_id=None, athlete_id=None):
    """Get support tickets for a gym or athlete"""
    conn = get_connection()
    cursor = conn.cursor()
    
    if gym_id:
        cursor.execute(
            """
            SELECT t.id, t.subject, t.message, t.status, t.created_at,
                   a.full_name as athlete_name
            FROM support_tickets t
            JOIN athlete_details a ON t.athlete_id = a.id
            WHERE t.gym_id = ?
            ORDER BY t.created_at DESC
            """,
            (gym_id,)
        )
    elif athlete_id:
        cursor.execute(
            """
            SELECT t.id, t.subject, t.message, t.status, t.created_at,
                   g.gym_name
            FROM support_tickets t
            JOIN gym_details g ON t.gym_id = g.id
            WHERE t.athlete_id = ?
            ORDER BY t.created_at DESC
            """,
            (athlete_id,)
        )
    else:
        return []
    
    tickets = cursor.fetchall()
    
    conn.close()
    
    return [dict(ticket) for ticket in tickets]

def respond_to_ticket(ticket_id, responder_id, message):
    """Add a response to a support ticket"""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute(
        """
        INSERT INTO support_responses
        (ticket_id, responder_id, message)
        VALUES (?, ?, ?)
        """,
        (ticket_id, responder_id, message)
    )
    
    conn.commit()
    conn.close()
    
    return True

def update_ticket_status(ticket_id, status):
    """Update a support ticket status"""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute(
        """
        UPDATE support_tickets
        SET status = ?
        WHERE id = ?
        """,
        (status, ticket_id)
    )
    
    conn.commit()
    conn.close()
    
    return True

def get_ticket_responses(ticket_id):
    """Get responses for a support ticket"""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute(
        """
        SELECT r.id, r.message, r.created_at, u.username, u.user_type
        FROM support_responses r
        JOIN users u ON r.responder_id = u.id
        WHERE r.ticket_id = ?
        ORDER BY r.created_at ASC
        """,
        (ticket_id,)
    )
    responses = cursor.fetchall()
    
    conn.close()
    
    return [dict(response) for response in responses]

def get_statistics_for_gym(gym_id):
    """Get statistics for a gym dashboard"""
    conn = get_connection()
    cursor = conn.cursor()
    
    # Get total members count
    cursor.execute(
        """
        SELECT COUNT(*) as total_members
        FROM athlete_details
        WHERE gym_id = ?
        """,
        (gym_id,)
    )
    members_count = cursor.fetchone()['total_members']
    
    # Get total trainers count
    cursor.execute(
        """
        SELECT COUNT(*) as total_trainers
        FROM trainer_details
        WHERE gym_id = ?
        """,
        (gym_id,)
    )
    trainers_count = cursor.fetchone()['total_trainers']
    
    # Get average rating
    cursor.execute(
        """
        SELECT AVG(rating) as avg_rating
        FROM reviews
        WHERE gym_id = ?
        """,
        (gym_id,)
    )
    avg_rating = cursor.fetchone()['avg_rating'] or 0
    
    # Get visits per day for last 7 days
    cursor.execute(
        """
        SELECT date(check_in_time) as visit_date, COUNT(*) as visit_count
        FROM gym_visits
        WHERE gym_id = ? AND check_in_time >= date('now', '-7 days')
        GROUP BY date(check_in_time)
        ORDER BY visit_date ASC
        """,
        (gym_id,)
    )
    visits_data = cursor.fetchall()
    visits_data = [dict(row) for row in visits_data]
    
    # Get athletes per trainer
    cursor.execute(
        """
        SELECT t.id, t.full_name, COUNT(a.id) as athlete_count
        FROM trainer_details t
        LEFT JOIN athlete_details a ON t.id = a.trainer_id
        WHERE t.gym_id = ?
        GROUP BY t.id
        """,
        (gym_id,)
    )
    athletes_per_trainer = cursor.fetchall()
    athletes_per_trainer = [dict(row) for row in athletes_per_trainer]
    
    conn.close()
    
    return {
        'members_count': members_count,
        'trainers_count': trainers_count,
        'avg_rating': avg_rating,
        'visits_data': visits_data,
        'athletes_per_trainer': athletes_per_trainer
    }

def get_statistics_for_trainer(trainer_id):
    """Get statistics for a trainer dashboard"""
    conn = get_connection()
    cursor = conn.cursor()
    
    # Get total athletes count
    cursor.execute(
        """
        SELECT COUNT(*) as total_athletes
        FROM athlete_details
        WHERE trainer_id = ?
        """,
        (trainer_id,)
    )
    athletes_count = cursor.fetchone()['total_athletes']
    
    # Get average rating
    cursor.execute(
        """
        SELECT AVG(rating) as avg_rating
        FROM reviews
        WHERE trainer_id = ?
        """,
        (trainer_id,)
    )
    avg_rating = cursor.fetchone()['avg_rating'] or 0
    
    # Get list of athletes
    cursor.execute(
        """
        SELECT id, full_name, age, gender, goals
        FROM athlete_details
        WHERE trainer_id = ?
        """,
        (trainer_id,)
    )
    athletes = cursor.fetchall()
    athletes = [dict(row) for row in athletes]
    
    conn.close()
    
    return {
        'athletes_count': athletes_count,
        'avg_rating': avg_rating,
        'athletes': athletes
    }

def get_statistics_for_athlete(athlete_id):
    """Get statistics for an athlete dashboard"""
    conn = get_connection()
    cursor = conn.cursor()
    
    # Get total visits count
    cursor.execute(
        """
        SELECT COUNT(*) as total_visits
        FROM gym_visits
        WHERE athlete_id = ?
        """,
        (athlete_id,)
    )
    visits_count = cursor.fetchone()['total_visits']
    
    # Get visits per day for last 7 days
    cursor.execute(
        """
        SELECT date(check_in_time) as visit_date, COUNT(*) as visit_count
        FROM gym_visits
        WHERE athlete_id = ? AND check_in_time >= date('now', '-7 days')
        GROUP BY date(check_in_time)
        ORDER BY visit_date ASC
        """,
        (athlete_id,)
    )
    visits_data = cursor.fetchall()
    visits_data = [dict(row) for row in visits_data]
    
    # Get average time spent in gym
    cursor.execute(
        """
        SELECT AVG((julianday(check_out_time) - julianday(check_in_time)) * 24 * 60) as avg_minutes
        FROM gym_visits
        WHERE athlete_id = ? AND check_out_time IS NOT NULL
        """,
        (athlete_id,)
    )
    avg_time = cursor.fetchone()['avg_minutes'] or 0
    
    conn.close()
    
    return {
        'visits_count': visits_count,
        'avg_time': avg_time,
        'visits_data': visits_data
    }

def get_gym_id_from_user_id(user_id):
    """Get the gym_id for a gym manager user"""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute(
        "SELECT id FROM gym_details WHERE user_id = ?",
        (user_id,)
    )
    gym = cursor.fetchone()
    
    conn.close()
    
    if gym:
        return gym['id']
    return None

def get_trainer_id_from_user_id(user_id):
    """Get the trainer_id for a trainer user"""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute(
        "SELECT id FROM trainer_details WHERE user_id = ?",
        (user_id,)
    )
    trainer = cursor.fetchone()
    
    conn.close()
    
    if trainer:
        return trainer['id']
    return None

def get_athlete_id_from_user_id(user_id):
    """Get the athlete_id for an athlete user"""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute(
        "SELECT id FROM athlete_details WHERE user_id = ?",
        (user_id,)
    )
    athlete = cursor.fetchone()
    
    conn.close()
    
    if athlete:
        return athlete['id']
    return None
