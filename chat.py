import streamlit as st
from database import (
    get_contacts, get_messages, send_message, get_user_by_id,
    get_trainer_details, get_athlete_details, get_gym_details,
    get_connection
)
from utils import format_time_ago, check_session

def show_chat():
    """Show the chat interface"""
    check_session()
    
    st.title("Messages")
    
    # Initialize chat_with in session state if not present
    if 'chat_with' not in st.session_state:
        st.session_state.chat_with = None
    
    user_id = st.session_state.user_id
    
    # Get contacts
    contacts = get_contacts(user_id)
    
    # Create two columns for contacts and messages
    col1, col2 = st.columns([1, 3])
    
    with col1:
        st.subheader("Contacts")
        
        if contacts:
            for contact in contacts:
                # Create button for each contact
                button_label = f"{contact['name']} ({contact['unread_count']})" if contact['unread_count'] > 0 else contact['name']
                
                if st.button(button_label, key=f"contact_{contact['id']}"):
                    st.session_state.chat_with = contact['id']
                    st.rerun()
        else:
            st.info("No conversations yet.")
            
        # New message button
        if st.button("New Message"):
            st.session_state.chat_with = "new"
            st.rerun()
    
    with col2:
        # Show messages with selected contact or new message form
        if st.session_state.chat_with == "new":
            show_new_message_form(user_id)
        elif st.session_state.chat_with:
            show_conversation(user_id, st.session_state.chat_with)
        else:
            st.info("Select a contact to view messages or start a new conversation.")

def show_new_message_form(user_id):
    """Show form to start a new conversation"""
    st.subheader("New Message")
    
    # Get user details
    user_details = get_user_by_id(user_id)
    
    if not user_details:
        st.error("User details not found.")
        return
    
    # Based on user type, show appropriate contacts
    user_type = user_details['user_type']
    
    if user_type == "Gym Manager":
        # Get gym details
        gym_details = get_gym_details(user_id)
        
        if not gym_details:
            st.warning("Please complete your gym profile first.")
            return
        
        gym_id = gym_details['id']
        
        # Show athletes from this gym
        st.write("Send a message to one of your gym members:")
        
        # Use imported get_connection
        conn = get_connection()
        cursor = conn.cursor()
        
        cursor.execute(
            """
            SELECT a.id, a.user_id, a.full_name
            FROM athlete_details a
            WHERE a.gym_id = ?
            ORDER BY a.full_name
            """,
            (gym_id,)
        )
        athletes = cursor.fetchall()
        
        conn.close()
        
        if athletes:
            for athlete in athletes:
                if st.button(f"Message {athlete['full_name']}", key=f"new_msg_{athlete['user_id']}"):
                    st.session_state.chat_with = athlete['user_id']
                    st.rerun()
        else:
            st.info("No athletes in your gym yet.")
    
    elif user_type == "Trainer":
        # Get trainer details
        trainer_details = get_trainer_details(user_id)
        
        if not trainer_details:
            st.warning("Please complete your trainer profile first.")
            return
        
        # Show athletes assigned to this trainer
        st.write("Send a message to one of your athletes:")
        
        # Use imported get_connection
        conn = get_connection()
        cursor = conn.cursor()
        
        cursor.execute(
            """
            SELECT a.id, a.user_id, a.full_name
            FROM athlete_details a
            WHERE a.trainer_id = ?
            ORDER BY a.full_name
            """,
            (trainer_details['id'],)
        )
        athletes = cursor.fetchall()
        
        conn.close()
        
        if athletes:
            for athlete in athletes:
                if st.button(f"Message {athlete['full_name']}", key=f"new_msg_{athlete['user_id']}"):
                    st.session_state.chat_with = athlete['user_id']
                    st.rerun()
        else:
            st.info("No athletes assigned to you yet.")
        
        # Show gym manager if trainer is affiliated with a gym
        if trainer_details['gym_id']:
            st.write("Contact your gym:")
            
            # Use imported get_connection
            conn = get_connection()
            cursor = conn.cursor()
            
            cursor.execute(
                """
                SELECT u.id, g.gym_name
                FROM gym_details g
                JOIN users u ON g.user_id = u.id
                WHERE g.id = ?
                """,
                (trainer_details['gym_id'],)
            )
            gym = cursor.fetchone()
            
            conn.close()
            
            if gym:
                if st.button(f"Message {gym['gym_name']}", key=f"new_msg_{gym['id']}"):
                    st.session_state.chat_with = gym['id']
                    st.rerun()
    
    elif user_type == "Athlete":
        # Get athlete details
        athlete_details = get_athlete_details(user_id)
        
        if not athlete_details:
            st.warning("Please complete your profile first.")
            return
        
        # Show trainer if athlete has one
        if athlete_details['trainer_id']:
            st.write("Contact your trainer:")
            
            # Use imported get_connection
            conn = get_connection()
            cursor = conn.cursor()
            
            cursor.execute(
                """
                SELECT u.id, t.full_name
                FROM trainer_details t
                JOIN users u ON t.user_id = u.id
                WHERE t.id = ?
                """,
                (athlete_details['trainer_id'],)
            )
            trainer = cursor.fetchone()
            
            conn.close()
            
            if trainer:
                if st.button(f"Message {trainer['full_name']}", key=f"new_msg_{trainer['id']}"):
                    st.session_state.chat_with = trainer['id']
                    st.rerun()
        
        # Show gym manager if athlete is affiliated with a gym
        if athlete_details['gym_id']:
            st.write("Contact your gym:")
            
            # Use imported get_connection
            conn = get_connection()
            cursor = conn.cursor()
            
            cursor.execute(
                """
                SELECT u.id, g.gym_name
                FROM gym_details g
                JOIN users u ON g.user_id = u.id
                WHERE g.id = ?
                """,
                (athlete_details['gym_id'],)
            )
            gym = cursor.fetchone()
            
            conn.close()
            
            if gym:
                if st.button(f"Message {gym['gym_name']}", key=f"new_msg_{gym['id']}"):
                    st.session_state.chat_with = gym['id']
                    st.rerun()
    
    # Cancel button
    if st.button("Cancel"):
        st.session_state.chat_with = None
        st.rerun()

def show_conversation(user_id, contact_id):
    """Show conversation with a contact"""
    # Get contact details
    contact = get_user_by_id(contact_id)
    
    if not contact:
        st.error("Contact not found.")
        return
    
    # Get additional details based on contact type
    contact_name = contact['username']
    
    if contact['user_type'] == "Gym Manager":
        gym_details = get_gym_details(contact_id)
        if gym_details:
            contact_name = gym_details['gym_name']
    elif contact['user_type'] == "Trainer":
        trainer_details = get_trainer_details(contact_id)
        if trainer_details:
            contact_name = trainer_details['full_name']
    elif contact['user_type'] == "Athlete":
        athlete_details = get_athlete_details(contact_id)
        if athlete_details:
            contact_name = athlete_details['full_name']
    
    st.subheader(f"Chat with {contact_name}")
    
    # Get messages
    messages = get_messages(user_id, contact_id)
    
    # Display messages
    message_container = st.container()
    
    with message_container:
        for message in messages:
            if message['sender_id'] == user_id:
                message_alignment = "right"
                message_bg = "#ddd"
            else:
                message_alignment = "left"
                message_bg = "#f0f0f0"
            
            st.markdown(
                f"""
                <div style="text-align: {message_alignment};">
                    <div style="display: inline-block; background-color: {message_bg}; padding: 10px; border-radius: 10px; max-width: 70%;">
                        {message['message']}
                        <div style="font-size: 0.8em; color: gray;">{format_time_ago(message['created_at'])}</div>
                    </div>
                </div>
                """,
                unsafe_allow_html=True
            )
    
    # Input for new message
    with st.form("send_message_form", clear_on_submit=True):
        new_message = st.text_area("Type your message", height=100)
        
        col1, col2 = st.columns([3, 1])
        
        with col1:
            submit_button = st.form_submit_button("Send")
        
        with col2:
            back_button = st.form_submit_button("Back")
        
        if submit_button and new_message:
            success = send_message(user_id, contact_id, new_message)
            
            if success:
                st.rerun()
            else:
                st.error("Failed to send message. Please try again.")
        
        if back_button:
            st.session_state.chat_with = None
            st.rerun()