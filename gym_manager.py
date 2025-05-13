import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import io
from database import (
    get_gym_details, save_gym_details, save_membership_plan,
    get_membership_plans, get_statistics_for_gym, get_gym_id_from_user_id,
    get_gym_reviews, get_support_tickets, respond_to_ticket, update_ticket_status,
    get_ticket_responses, get_connection
)
from utils import check_session, get_image_bytes_from_upload, create_star_rating, format_time_ago

def show():
    """Display the gym manager page"""
    check_session()
    
    # Check if gym manager profile is complete
    user_id = st.session_state.user_id
    gym_details = get_gym_details(user_id)
    gym_id = get_gym_id_from_user_id(user_id)
    
    if gym_details is None or not gym_details['license_verified']:
        show_profile_setup(user_id, gym_details)
    else:
        show_dashboard(user_id, gym_id, gym_details)

def show_profile_setup(user_id, gym_details):
    """Show the profile setup form for gym managers"""
    st.title("Complete Your Gym Profile")
    
    if gym_details:
        # For the demo, automatically verify gym licenses
        # In a real application, an admin would manually verify
        if not gym_details['license_verified']:
            st.warning("Your gym profile is currently pending verification.")
            st.info("For demonstration purposes, we'll automatically verify your gym license.")
            
            # Automatically verify the license
            conn = get_connection()
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE gym_details SET license_verified = TRUE WHERE user_id = ?",
                (user_id,)
            )
            conn.commit()
            conn.close()
            
            st.success("Your gym license has been verified! Please refresh the page to access your dashboard.")
            
            # Use a container outside the form context for the button
            refresh_button_container = st.empty()
            if refresh_button_container.button("Refresh"):
                st.rerun()
            
            return
            
        # Show the current profile for review if somehow we get here
        st.subheader("Your Gym Profile")
        st.write(f"**Gym Name:** {gym_details['gym_name']}")
        st.write(f"**Address:** {gym_details['address']}")
        st.write(f"**Contact:** {gym_details['contact_number']}")
        st.write(f"**Email:** {gym_details['email']}")
        
        st.write("Your profile is verified. You should be redirected to the dashboard.")
        
        dashboard_button_container = st.empty()
        if dashboard_button_container.button("Go to Dashboard"):
            st.rerun()
        
    else:
        # Multi-step form using tabs
        st.write("Welcome to the Gym Management System! As a gym manager, you can manage memberships, track members, and more.")
        st.write("Let's set up your gym profile to get started.")
        
        # Create a multi-step form using tabs
        step1, step2 = st.tabs(["Basic Information", "License Verification"])
        
        with step1:
            st.subheader("Step 1: Basic Information")
            
            # Store form data in session state
            if 'gym_name' not in st.session_state:
                st.session_state.gym_name = ""
            if 'gym_address' not in st.session_state:
                st.session_state.gym_address = ""
            if 'gym_contact' not in st.session_state:
                st.session_state.gym_contact = ""
            if 'gym_email' not in st.session_state:
                st.session_state.gym_email = ""
                
            with st.form("gym_basic_info_form"):
                st.session_state.gym_name = st.text_input("Gym Name*", value=st.session_state.gym_name)
                st.session_state.gym_address = st.text_input("Address*", value=st.session_state.gym_address)
                st.session_state.gym_contact = st.text_input("Contact Number*", value=st.session_state.gym_contact)
                st.session_state.gym_email = st.text_input("Email*", value=st.session_state.gym_email)
                
                submit_basic_info = st.form_submit_button("Save & Continue")
                
                if submit_basic_info:
                    if not st.session_state.gym_name or not st.session_state.gym_address or not st.session_state.gym_contact or not st.session_state.gym_email:
                        st.error("Please fill all required fields.")
                    else:
                        st.success("Basic information saved. Please proceed to license verification.")
                        # Auto-switch to next tab
                        st.rerun()
        
        with step2:
            st.subheader("Step 2: License Verification")
            
            # Check if basic info is completed
            if not st.session_state.gym_name or not st.session_state.gym_address or not st.session_state.gym_contact or not st.session_state.gym_email:
                st.warning("Please complete the Basic Information step first.")
                return
            
            st.write("Please upload your gym license for verification. This helps ensure that your gym meets local regulations.")
            st.write("Accepted formats: PDF, JPG, JPEG, PNG")
            
            with st.form("gym_license_form"):
                license_doc = st.file_uploader("Gym License*", type=["pdf", "jpg", "jpeg", "png"])
                
                submit_license = st.form_submit_button("Complete Registration")
                
                if submit_license:
                    if not license_doc:
                        st.error("Please upload your gym license document.")
                    else:
                        # Convert file to bytes for storage
                        license_bytes = get_image_bytes_from_upload(license_doc)
                        
                        # Save gym details
                        success = save_gym_details(
                            user_id, 
                            st.session_state.gym_name, 
                            license_bytes, 
                            st.session_state.gym_address, 
                            st.session_state.gym_contact, 
                            st.session_state.gym_email
                        )
                        
                        if success:
                            st.success("Profile submitted successfully!")
                            
                            # Auto-verify for demo purposes
                            conn = get_connection()
                            cursor = conn.cursor()
                            cursor.execute(
                                "UPDATE gym_details SET license_verified = TRUE WHERE user_id = ?",
                                (user_id,)
                            )
                            conn.commit()
                            conn.close()
                            
                            st.success("Your gym license has been automatically verified for demonstration purposes.")
                            
                            # We'll use form_submit_button instead of button since we're in a form
                            st.success("You'll be redirected to the dashboard after submitting.")
                            # The rerun will happen when the form is submitted
                        else:
                            st.error("An error occurred. Please try again.")

def show_dashboard(user_id, gym_id, gym_details):
    """Show the main dashboard for gym managers"""
    # Sidebar navigation
    with st.sidebar:
        st.subheader("Navigation")
        page = st.radio(
            "Go to",
            ["Dashboard", "Membership Plans", "Reviews", "Support Tickets"]
        )
    
    # Display selected page
    if page == "Dashboard":
        show_gym_dashboard(user_id, gym_id, gym_details)
    elif page == "Membership Plans":
        show_membership_plans(gym_id)
    elif page == "Reviews":
        show_reviews(gym_id)
    elif page == "Support Tickets":
        show_support_tickets(user_id, gym_id)

def show_gym_dashboard(user_id, gym_id, gym_details):
    """Show the main dashboard with statistics"""
    st.title(f"{gym_details['gym_name']} Dashboard")
    
    # Get statistics
    stats = get_statistics_for_gym(gym_id)
    
    # Display summary cards
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Total Members", stats['members_count'])
    
    with col2:
        st.metric("Total Trainers", stats['trainers_count'])
    
    with col3:
        st.metric("Average Rating", f"{stats['avg_rating']:.1f} / 5.0")
    
    # Display visit data chart
    st.subheader("Gym Visits (Last 7 Days)")
    
    if stats['visits_data']:
        # Convert to DataFrame
        visits_df = pd.DataFrame(stats['visits_data'])
        
        # Fill in missing dates
        date_range = pd.date_range(
            end=datetime.now().date(),
            periods=7
        ).strftime('%Y-%m-%d').tolist()
        
        # Create complete dataframe with all dates
        complete_df = pd.DataFrame({'visit_date': date_range})
        if not visits_df.empty:
            visits_df['visit_date'] = pd.to_datetime(visits_df['visit_date']).dt.strftime('%Y-%m-%d')
            complete_df = complete_df.merge(visits_df, on='visit_date', how='left')
        
        complete_df['visit_count'] = complete_df['visit_count'].fillna(0)
        
        # Create bar chart
        fig = px.bar(
            complete_df,
            x='visit_date',
            y='visit_count',
            labels={'visit_date': 'Date', 'visit_count': 'Number of Visits'},
            title='Daily Gym Visits'
        )
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No visit data available for the last 7 days.")
    
    # Display athletes per trainer
    st.subheader("Athletes per Trainer")
    
    if stats['athletes_per_trainer']:
        # Convert to DataFrame
        trainers_df = pd.DataFrame(stats['athletes_per_trainer'])
        
        # Create bar chart
        fig = px.bar(
            trainers_df,
            x='full_name',
            y='athlete_count',
            labels={'full_name': 'Trainer', 'athlete_count': 'Number of Athletes'},
            title='Athletes per Trainer'
        )
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No trainer data available.")

def show_membership_plans(gym_id):
    """Show and manage membership plans"""
    st.title("Membership Plans")
    
    # Get existing plans
    plans = get_membership_plans(gym_id)
    
    # Display existing plans
    if plans:
        st.subheader("Current Plans")
        
        for plan in plans:
            with st.expander(f"{plan['plan_name']} - ${plan['price']} for {plan['duration']} months"):
                st.write(f"**Description:** {plan['description']}")
                st.write(f"**Price:** ${plan['price']}")
                st.write(f"**Duration:** {plan['duration']} months")
    
    # Form to add new plan
    st.subheader("Add New Plan")
    
    with st.form("add_plan_form"):
        plan_name = st.text_input("Plan Name")
        
        duration = st.selectbox(
            "Duration (months)",
            [1, 3, 6, 8, 12],
            format_func=lambda x: f"{x} {'month' if x == 1 else 'months'}"
        )
        
        price = st.number_input("Price ($)", min_value=0.0, step=1.0)
        description = st.text_area("Description")
        
        submit_button = st.form_submit_button("Add Plan")
        
        if submit_button:
            if not plan_name or price <= 0:
                st.error("Please fill all the required fields.")
            else:
                success = save_membership_plan(gym_id, plan_name, duration, price, description)
                
                if success:
                    st.success("Plan added successfully!")
                    st.rerun()
                else:
                    st.error("An error occurred. Please try again.")

def show_reviews(gym_id):
    """Show gym reviews"""
    st.title("Gym Reviews")
    
    # Get reviews
    reviews = get_gym_reviews(gym_id)
    
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

def show_support_tickets(user_id, gym_id):
    """Show and manage support tickets"""
    st.title("Support Tickets")
    
    # Get tickets
    tickets = get_support_tickets(gym_id=gym_id)
    
    # Filter tickets by status
    status_filter = st.selectbox(
        "Filter by status",
        ["All", "open", "in progress", "closed"]
    )
    
    filtered_tickets = tickets
    if status_filter != "All":
        filtered_tickets = [t for t in tickets if t['status'] == status_filter]
    
    # Display tickets
    if filtered_tickets:
        for ticket in filtered_tickets:
            with st.expander(f"{ticket['subject']} - {ticket['status'].upper()} - {format_time_ago(ticket['created_at'])}"):
                st.write(f"**From:** {ticket['athlete_name']}")
                st.write(f"**Status:** {ticket['status'].upper()}")
                st.write(f"**Created:** {format_time_ago(ticket['created_at'])}")
                st.write(f"**Subject:** {ticket['subject']}")
                st.write(f"**Message:**")
                st.write(ticket['message'])
                
                # Get responses
                responses = get_ticket_responses(ticket['id'])
                
                if responses:
                    st.write("---")
                    st.write("**Responses:**")
                    
                    for response in responses:
                        st.write(f"{response['username']} ({response['user_type']}): {response['message']}")
                        st.write(f"*{format_time_ago(response['created_at'])}*")
                
                # Form to respond to ticket
                st.write("---")
                with st.form(f"respond_ticket_{ticket['id']}"):
                    response = st.text_area("Your response", key=f"response_{ticket['id']}")
                    
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        submit_button = st.form_submit_button("Send Response")
                    
                    with col2:
                        new_status = st.selectbox(
                            "Update status",
                            ["open", "in progress", "closed"],
                            index=["open", "in progress", "closed"].index(ticket['status'])
                        )
                    
                    if submit_button:
                        if response:
                            success = respond_to_ticket(ticket['id'], user_id, response)
                            
                            if ticket['status'] != new_status:
                                update_ticket_status(ticket['id'], new_status)
                            
                            if success:
                                st.success("Response sent successfully!")
                                st.rerun()
                            else:
                                st.error("An error occurred. Please try again.")
    else:
        st.info("No support tickets available.")
