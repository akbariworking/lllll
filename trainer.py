import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime
from database import (
    get_trainer_details, save_trainer_details, get_all_gyms,
    get_statistics_for_trainer, get_trainer_id_from_user_id,
    get_trainer_reviews, get_athlete_details, get_user_by_id,
    get_connection
)
from utils import (
    check_session, get_image_bytes_from_upload,
    create_star_rating, format_time_ago
)
from components.chat import show_chat

def show():
    """Display the trainer page"""
    check_session()
    
    # Check if trainer profile is complete
    user_id = st.session_state.user_id
    trainer_details = get_trainer_details(user_id)
    trainer_id = get_trainer_id_from_user_id(user_id)
    
    if trainer_details is None or not trainer_details['certification_verified']:
        show_profile_setup(user_id, trainer_details)
    else:
        show_dashboard(user_id, trainer_id, trainer_details)

def show_profile_setup(user_id, trainer_details):
    """Show the profile setup form for trainers"""
    st.title("Complete Your Trainer Profile")
    
    if trainer_details:
        # For the demo, automatically verify trainer certifications
        # In a real application, an admin would manually verify
        if not trainer_details['certification_verified']:
            st.warning("Your trainer profile is currently pending verification.")
            st.info("For demonstration purposes, we'll automatically verify your certification.")
            
            # Automatically verify the certification
            conn = get_connection()
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE trainer_details SET certification_verified = TRUE WHERE user_id = ?",
                (user_id,)
            )
            conn.commit()
            conn.close()
            
            st.success("Your certification has been verified! Please refresh the page to access your dashboard.")
            
            refresh_button_container = st.empty()
            if refresh_button_container.button("Refresh"):
                st.rerun()
            
            return
            
        # Show the current profile for review if somehow we get here
        st.subheader("Your Trainer Profile")
        st.write(f"**Full Name:** {trainer_details['full_name']}")
        st.write(f"**Specialization:** {trainer_details['specialization']}")
        st.write(f"**Experience:** {trainer_details['experience']} years")
        
        if trainer_details['gym_name']:
            st.write(f"**Gym:** {trainer_details['gym_name']}")
        
        st.write("Your profile is verified. You should be redirected to the dashboard.")
        
        dashboard_button_container = st.empty()
        if dashboard_button_container.button("Go to Dashboard"):
            st.rerun()
    
    else:
        # Initialize session state for the trainer profile steps
        if 'trainer_setup_step' not in st.session_state:
            st.session_state.trainer_setup_step = 1
            
        st.write("Welcome to the Gym Management System! As a trainer, you can manage your clients, track progress, and more.")
        
        # Step 1: Personal Information
        if st.session_state.trainer_setup_step == 1:
            st.subheader("Step 1: Personal & Professional Information")
            
            with st.form("trainer_personal_info_form"):
                full_name = st.text_input("Full Name*")
                specialization = st.text_input("Specialization*", placeholder="E.g., Strength Training, Weight Loss, Yoga, etc.")
                experience = st.number_input("Years of Experience*", min_value=0, step=1)
                
                about_me = st.text_area("About Me / Bio", 
                                       placeholder="Tell potential clients about yourself, your training philosophy, and your approach.")
                
                next_button = st.form_submit_button("Next: Choose Gym & Upload Certification")
                
                if next_button:
                    if not full_name or not specialization or experience < 0:
                        st.error("Please fill all required fields marked with *")
                    else:
                        # Store data in session state
                        st.session_state.trainer_full_name = full_name
                        st.session_state.trainer_specialization = specialization
                        st.session_state.trainer_experience = experience
                        st.session_state.trainer_about_me = about_me
                        
                        # Move to step 2
                        st.session_state.trainer_setup_step = 2
                        st.rerun()
        
        # Step 2: Gym Selection and Certification
        elif st.session_state.trainer_setup_step == 2:
            st.subheader("Step 2: Gym Affiliation & Certification")
            
            # Get available gyms
            gyms = get_all_gyms()
            
            # Display available gyms
            st.write("### Select Your Gym (if applicable)")
            
            if not gyms:
                st.warning("No gyms are currently registered in the system.")
                st.write("You can still continue without selecting a gym and join one later.")
                selected_gym = None
            else:
                st.write("Select a gym you're affiliated with or choose 'Not affiliated with a gym yet':")
                
                # Add the "None" option
                gym_options = [(-1, "Not affiliated with a gym yet")] + [(gym['id'], gym['gym_name']) for gym in gyms]
                
                # Create a radio button for gym selection
                gym_selection = st.radio(
                    "Choose a gym:",
                    options=range(len(gym_options)),
                    format_func=lambda x: gym_options[x][1],
                    key="gym_selection_radio"
                )
                
                selected_gym = None if gym_options[gym_selection][0] == -1 else gym_options[gym_selection][0]
                
                if selected_gym:
                    st.success(f"You selected: {gym_options[gym_selection][1]}")
            
            st.markdown("---")
            st.write("### Upload Your Certification")
            st.write("Please upload your training certification for verification:")
            certification_doc = st.file_uploader("Certification Document*", type=["pdf", "jpg", "jpeg", "png"])
            
            col1, col2 = st.columns([1, 3])
            
            with col1:
                if st.button("← Back"):
                    st.session_state.trainer_setup_step = 1
                    st.rerun()
            
            if certification_doc:
                if st.button("Complete Registration", type="primary"):
                    # Convert file to bytes for storage
                    certification_bytes = get_image_bytes_from_upload(certification_doc)
                    
                    # Save trainer details
                    success = save_trainer_details(
                        user_id, 
                        st.session_state.trainer_full_name, 
                        certification_bytes, 
                        st.session_state.trainer_specialization, 
                        st.session_state.trainer_experience, 
                        selected_gym
                    )
                    
                    if success:
                        st.success("Profile submitted successfully!")
                        
                        # Auto-verify for demo purposes
                        conn = get_connection()
                        cursor = conn.cursor()
                        cursor.execute(
                            "UPDATE trainer_details SET certification_verified = TRUE WHERE user_id = ?",
                            (user_id,)
                        )
                        conn.commit()
                        conn.close()
                        
                        st.success("Your certification has been automatically verified for demonstration purposes.")
                        
                        # Move the button outside the form context
                        st.session_state.pop('trainer_setup_step', None)
                        st.rerun()
                    else:
                        st.error("An error occurred. Please try again.")
            else:
                st.warning("Please upload your certification document to complete registration.")

def show_dashboard(user_id, trainer_id, trainer_details):
    """Show the main dashboard for trainers"""
    # Sidebar navigation
    with st.sidebar:
        st.subheader("Navigation")
        page = st.radio(
            "Go to",
            ["Dashboard", "My Athletes", "Reviews", "Messages"]
        )
    
    # Display selected page
    if page == "Dashboard":
        show_trainer_dashboard(user_id, trainer_id, trainer_details)
    elif page == "My Athletes":
        show_athletes(trainer_id)
    elif page == "Reviews":
        show_reviews(trainer_id)
    elif page == "Messages":
        show_chat()

def show_trainer_dashboard(user_id, trainer_id, trainer_details):
    """Show the main dashboard with statistics"""
    st.title(f"Welcome, {trainer_details['full_name']}!")
    
    # Get statistics
    stats = get_statistics_for_trainer(trainer_id)
    
    # Display summary cards
    col1, col2 = st.columns(2)
    
    with col1:
        st.metric("Total Athletes", stats['athletes_count'])
    
    with col2:
        st.metric("Average Rating", f"{stats['avg_rating']:.1f} / 5.0")
    
    # Gym affiliation
    st.subheader("Gym Affiliation")
    if trainer_details['gym_name']:
        st.success(f"You are affiliated with: {trainer_details['gym_name']}")
    else:
        st.warning("You are not affiliated with any gym yet.")
        
        # Show available gyms
        gyms = get_all_gyms()
        
        if gyms:
            with st.expander("Join a gym"):
                with st.form("join_gym_form"):
                    gym_id = st.selectbox(
                        "Select a gym to join",
                        options=[g['id'] for g in gyms],
                        format_func=lambda x: next((g['gym_name'] for g in gyms if g['id'] == x), x)
                    )
                    
                    submit_button = st.form_submit_button("Join Gym")
                    
                    if submit_button:
                        # Update trainer with selected gym
                        success = save_trainer_details(
                            user_id, 
                            trainer_details['full_name'],
                            None,  # Keep existing certification document
                            trainer_details['specialization'],
                            trainer_details['experience'],
                            gym_id
                        )
                        
                        if success:
                            st.success("Gym affiliation updated successfully!")
                            st.rerun()
                        else:
                            st.error("An error occurred. Please try again.")
        else:
            st.info("No gyms available to join at the moment.")
    
    # Recent athletes
    st.subheader("Recent Athletes")
    if stats['athletes']:
        for athlete in stats['athletes'][:5]:  # Show only the first 5
            st.write(f"**{athlete['full_name']}** ({athlete['age']} years, {athlete['gender']})")
            st.write(f"Goals: {athlete['goals']}")
            st.write("---")
    else:
        st.info("You don't have any athletes yet.")

def show_athletes(trainer_id):
    """Show all athletes assigned to this trainer"""
    st.title("My Athletes")
    
    # Get statistics
    stats = get_statistics_for_trainer(trainer_id)
    
    if stats['athletes']:
        # Create tabs for all, male, and female athletes
        all_tab, male_tab, female_tab = st.tabs(["All Athletes", "Male Athletes", "Female Athletes"])
        
        with all_tab:
            display_athletes(stats['athletes'])
        
        with male_tab:
            male_athletes = [a for a in stats['athletes'] if a['gender'] == 'Male']
            if male_athletes:
                display_athletes(male_athletes)
            else:
                st.info("No male athletes.")
        
        with female_tab:
            female_athletes = [a for a in stats['athletes'] if a['gender'] == 'Female']
            if female_athletes:
                display_athletes(female_athletes)
            else:
                st.info("No female athletes.")
    else:
        st.info("You don't have any athletes yet.")

def display_athletes(athletes):
    """Helper function to display a list of athletes"""
    for athlete in athletes:
        with st.expander(f"{athlete['full_name']} ({athlete['age']} years, {athlete['gender']})"):
            # Get full profile
            complete_profile = get_athlete_details(athlete['user_id']) if 'user_id' in athlete else None
            
            if complete_profile:
                st.write(f"**Age:** {complete_profile['age']} years")
                st.write(f"**Gender:** {complete_profile['gender']}")
                st.write(f"**Weight:** {complete_profile['weight']} kg")
                st.write(f"**Height:** {complete_profile['height']} cm")
                st.write(f"**Goals:** {complete_profile['goals']}")
                st.write(f"**Medical Conditions:** {complete_profile['medical_conditions'] or 'None'}")
            else:
                st.write(f"**Age:** {athlete['age']} years")
                st.write(f"**Gender:** {athlete['gender']}")
                st.write(f"**Goals:** {athlete['goals']}")
            
            # Add button to send a message
            user = get_user_by_id(athlete['user_id']) if 'user_id' in athlete else None
            if user and st.button(f"Message {athlete['full_name']}", key=f"msg_{athlete['id']}"):
                st.session_state.chat_with = user['id']
                st.rerun()

def show_reviews(trainer_id):
    """Show trainer reviews"""
    st.title("My Reviews")
    
    # Get reviews
    reviews = get_trainer_reviews(trainer_id)
    
    if reviews:
        # Display overall rating
        total_rating = sum(review['rating'] for review in reviews)
        avg_rating = total_rating / len(reviews)
        
        st.subheader(f"Overall Rating: {avg_rating:.1f}/5.0")
        
        # Display rating distribution
        ratings = [review['rating'] for review in reviews]
        rating_counts = {i: ratings.count(i) for i in range(1, 6)}
        
        rating_df = pd.DataFrame({
            'Rating': list(rating_counts.keys()),
            'Count': list(rating_counts.values())
        })
        
        fig = px.bar(
            rating_df,
            x='Rating',
            y='Count',
            title='Rating Distribution',
            labels={'Rating': 'Star Rating', 'Count': 'Number of Reviews'}
        )
        st.plotly_chart(fig, use_container_width=True)
        
        # Display individual reviews
        st.subheader("Individual Reviews")
        
        for review in reviews:
            with st.expander(f"{review['athlete_name']} - {create_star_rating(review['rating'])} - {format_time_ago(review['created_at'])}"):
                st.write(f"**Rating:** {create_star_rating(review['rating'])}")
                st.write(f"**Comment:** {review['comment'] if review['comment'] else 'No comment provided'}")
                st.write(f"**Date:** {format_time_ago(review['created_at'])}")
    else:
        st.info("No reviews available.")
