import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime
from database import (
    get_athlete_details, save_athlete_details, get_all_gyms,
    get_trainers_by_gym, get_statistics_for_athlete,
    get_athlete_id_from_user_id, get_active_visits, get_visit_history,
    record_gym_visit, checkout_gym_visit, add_review, get_gym_reviews,
    get_trainer_reviews, create_support_ticket, get_support_tickets,
    get_ticket_responses
)
from utils import (
    check_session, create_star_rating, format_time_ago,
    format_datetime, calculate_duration
)
from components.chat import show_chat
from components.support import show_support

def show():
    """Display the athlete page"""
    check_session()
    
    # Check if athlete profile is complete
    user_id = st.session_state.user_id
    athlete_details = get_athlete_details(user_id)
    athlete_id = get_athlete_id_from_user_id(user_id)
    
    if athlete_details is None:
        show_profile_setup(user_id)
    else:
        show_dashboard(user_id, athlete_id, athlete_details)

def show_profile_setup(user_id):
    """Show the profile setup form for athletes"""
    st.title("Complete Your Profile")
    st.write("Welcome to the Gym Management System! Please complete your profile to continue.")
    
    # Initialize the step in session state if not already present
    if 'athlete_setup_step' not in st.session_state:
        st.session_state.athlete_setup_step = 1
    
    # Step 1: Personal Information
    if st.session_state.athlete_setup_step == 1:
        st.subheader("Step 1: Personal Information")
        
        with st.form("athlete_personal_info_form"):
            full_name = st.text_input("Full Name*")
            
            col1, col2 = st.columns(2)
            with col1:
                age = st.number_input("Age*", min_value=1, max_value=100, step=1, value=25)
            with col2:
                gender = st.selectbox("Gender*", ["Male", "Female", "Other"])
            
            col1, col2 = st.columns(2)
            with col1:
                weight = st.number_input("Weight (kg)*", min_value=1.0, max_value=300.0, step=0.1, value=70.0)
            with col2:
                height = st.number_input("Height (cm)*", min_value=1.0, max_value=300.0, step=0.1, value=170.0)
            
            goals = st.text_area("Fitness Goals*", 
                                placeholder="Example: Build muscle, lose weight, improve endurance, etc.")
            medical_conditions = st.text_area("Medical Conditions (if any)", 
                                           placeholder="Any health conditions the trainer should know about")
            
            next_button = st.form_submit_button("Next: Choose Your Gym")
            
            if next_button:
                if not full_name or age < 1 or not gender or weight < 1 or height < 1 or not goals:
                    st.error("Please fill all required fields marked with *")
                else:
                    # Store data in session state
                    st.session_state.athlete_full_name = full_name
                    st.session_state.athlete_age = age
                    st.session_state.athlete_gender = gender
                    st.session_state.athlete_weight = weight
                    st.session_state.athlete_height = height
                    st.session_state.athlete_goals = goals
                    st.session_state.athlete_medical_conditions = medical_conditions
                    
                    # Move to step 2
                    st.session_state.athlete_setup_step = 2
                    st.rerun()
    
    # Step 2: Gym Selection
    elif st.session_state.athlete_setup_step == 2:
        st.subheader("Step 2: Choose Your Gym")
        
        # Get all available gyms
        gyms = get_all_gyms()
        
        if not gyms:
            st.warning("No gyms are registered in the system yet.")
            
            # Option to go back
            col1, col2 = st.columns([1, 4])
            with col1:
                if st.button("← Back"):
                    st.session_state.athlete_setup_step = 1
                    st.rerun()
            
            st.markdown("---")
            st.subheader("Would you like to check back later or continue without a gym?")
            
            col1, col2 = st.columns(2)
            with col1:
                if st.button("Save Profile & Continue Without Gym"):
                    # Save athlete details without gym or trainer
                    success = save_athlete_details(
                        user_id, 
                        st.session_state.athlete_full_name, 
                        st.session_state.athlete_age, 
                        st.session_state.athlete_gender, 
                        st.session_state.athlete_weight, 
                        st.session_state.athlete_height, 
                        st.session_state.athlete_goals, 
                        st.session_state.athlete_medical_conditions, 
                        None, None
                    )
                    
                    if success:
                        st.success("Profile saved successfully! You can select a gym later.")
                        st.session_state.pop('athlete_setup_step', None)
                        st.rerun()
                    else:
                        st.error("An error occurred. Please try again.")
            
            return
        
        # Display available gyms as cards
        st.write("Please select a gym from the available options:")
        
        # Create a container for gym cards
        gym_container = st.container()
        
        with gym_container:
            # Display gyms in rows of 2
            for i in range(0, len(gyms), 2):
                col1, col2 = st.columns(2)
                
                # First gym in the row
                with col1:
                    if i < len(gyms):
                        with st.container(border=True):
                            st.subheader(gyms[i]['gym_name'])
                            st.write(f"📍 {gyms[i]['address'] or 'Address not provided'}")
                            if st.button(f"Select {gyms[i]['gym_name']}", key=f"gym_{gyms[i]['id']}"):
                                st.session_state.athlete_selected_gym = gyms[i]['id']
                                st.session_state.athlete_setup_step = 3
                                st.rerun()
                
                # Second gym in the row
                with col2:
                    if i + 1 < len(gyms):
                        with st.container(border=True):
                            st.subheader(gyms[i+1]['gym_name'])
                            st.write(f"📍 {gyms[i+1]['address'] or 'Address not provided'}")
                            if st.button(f"Select {gyms[i+1]['gym_name']}", key=f"gym_{gyms[i+1]['id']}"):
                                st.session_state.athlete_selected_gym = gyms[i+1]['id']
                                st.session_state.athlete_setup_step = 3
                                st.rerun()
        
        # Navigation buttons
        col1, col2 = st.columns([1, 4])
        with col1:
            if st.button("← Back"):
                st.session_state.athlete_setup_step = 1
                st.rerun()
    
    # Step 3: Trainer Selection
    elif st.session_state.athlete_setup_step == 3:
        st.subheader("Step 3: Choose Your Trainer (Optional)")
        
        selected_gym = st.session_state.athlete_selected_gym
        
        # Get gym name for display
        gym_name = "Selected Gym"
        for gym in get_all_gyms():
            if gym['id'] == selected_gym:
                gym_name = gym['gym_name']
                break
        
        st.write(f"Selected Gym: **{gym_name}**")
        
        # Get trainers for selected gym
        trainers = get_trainers_by_gym(selected_gym)
        
        if not trainers:
            st.info("No trainers are available at this gym yet.")
            
            col1, col2, col3 = st.columns([1, 1, 3])
            with col1:
                if st.button("← Back"):
                    st.session_state.athlete_setup_step = 2
                    st.rerun()
            with col2:
                if st.button("Finish Without Trainer"):
                    # Save athlete details with gym but without trainer
                    success = save_athlete_details(
                        user_id, 
                        st.session_state.athlete_full_name, 
                        st.session_state.athlete_age, 
                        st.session_state.athlete_gender, 
                        st.session_state.athlete_weight, 
                        st.session_state.athlete_height, 
                        st.session_state.athlete_goals, 
                        st.session_state.athlete_medical_conditions, 
                        selected_gym, None
                    )
                    
                    if success:
                        st.success("Profile saved successfully! You can select a trainer later.")
                        st.session_state.pop('athlete_setup_step', None)
                        st.rerun()
                    else:
                        st.error("An error occurred. Please try again.")
            
            return
        
        # Display available trainers as cards
        st.write("Choose a trainer or continue without one:")
        
        # Create a container for trainer cards
        trainer_container = st.container()
        
        with trainer_container:
            # Display trainers in rows of 2
            for i in range(0, len(trainers), 2):
                col1, col2 = st.columns(2)
                
                # First trainer in the row
                with col1:
                    if i < len(trainers):
                        with st.container(border=True):
                            st.subheader(trainers[i]['full_name'])
                            st.write(f"**Specialization:** {trainers[i]['specialization'] or 'General'}")
                            st.write(f"**Experience:** {trainers[i]['experience'] or 0} years")
                            if st.button(f"Select {trainers[i]['full_name']}", key=f"trainer_{trainers[i]['id']}"):
                                # Save athlete details with gym and trainer
                                success = save_athlete_details(
                                    user_id, 
                                    st.session_state.athlete_full_name, 
                                    st.session_state.athlete_age, 
                                    st.session_state.athlete_gender, 
                                    st.session_state.athlete_weight, 
                                    st.session_state.athlete_height, 
                                    st.session_state.athlete_goals, 
                                    st.session_state.athlete_medical_conditions, 
                                    selected_gym, trainers[i]['id']
                                )
                                
                                if success:
                                    st.success(f"Profile saved successfully! You've selected {trainers[i]['full_name']} as your trainer.")
                                    st.session_state.pop('athlete_setup_step', None)
                                    st.rerun()
                                else:
                                    st.error("An error occurred. Please try again.")
                
                # Second trainer in the row
                with col2:
                    if i + 1 < len(trainers):
                        with st.container(border=True):
                            st.subheader(trainers[i+1]['full_name'])
                            st.write(f"**Specialization:** {trainers[i+1]['specialization'] or 'General'}")
                            st.write(f"**Experience:** {trainers[i+1]['experience'] or 0} years")
                            if st.button(f"Select {trainers[i+1]['full_name']}", key=f"trainer_{trainers[i+1]['id']}"):
                                # Save athlete details with gym and trainer
                                success = save_athlete_details(
                                    user_id, 
                                    st.session_state.athlete_full_name, 
                                    st.session_state.athlete_age, 
                                    st.session_state.athlete_gender, 
                                    st.session_state.athlete_weight, 
                                    st.session_state.athlete_height, 
                                    st.session_state.athlete_goals, 
                                    st.session_state.athlete_medical_conditions, 
                                    selected_gym, trainers[i+1]['id']
                                )
                                
                                if success:
                                    st.success(f"Profile saved successfully! You've selected {trainers[i+1]['full_name']} as your trainer.")
                                    st.session_state.pop('athlete_setup_step', None)
                                    st.rerun()
                                else:
                                    st.error("An error occurred. Please try again.")
        
        # Navigation and completion buttons
        col1, col2 = st.columns([1, 3])
        with col1:
            if st.button("← Back"):
                st.session_state.athlete_setup_step = 2
                st.rerun()
        
        if st.button("Continue Without Trainer"):
            # Save athlete details with gym but without trainer
            success = save_athlete_details(
                user_id, 
                st.session_state.athlete_full_name, 
                st.session_state.athlete_age, 
                st.session_state.athlete_gender, 
                st.session_state.athlete_weight, 
                st.session_state.athlete_height, 
                st.session_state.athlete_goals, 
                st.session_state.athlete_medical_conditions, 
                selected_gym, None
            )
            
            if success:
                st.success("Profile saved successfully! You can select a trainer later.")
                st.session_state.pop('athlete_setup_step', None)
                st.rerun()
            else:
                st.error("An error occurred. Please try again.")

def show_dashboard(user_id, athlete_id, athlete_details):
    """Show the main dashboard for athletes"""
    
    # Sidebar navigation with enhanced styling
    with st.sidebar:
        st.markdown('<h3 style="color: #3A0CA3; margin-top: 1rem;">Navigation</h3>', unsafe_allow_html=True)
        
        # Create a more visually appealing navigation
        nav_options = {
            "Dashboard": "📊",
            "Profile": "👤", 
            "Gym Visits": "🏋️",
            "Reviews": "⭐",
            "Messages": "💬",
            "Support": "🆘"
        }
        
        # Get current page
        if 'athlete_current_page' not in st.session_state:
            st.session_state.athlete_current_page = "Dashboard"
        
        # Create styled navigation menu
        for nav_label, nav_icon in nav_options.items():
            # Create clickable navigation item
            if st.button(
                f"{nav_icon} {nav_label}", 
                key=f"nav_{nav_label}",
                use_container_width=True,
                type="primary" if st.session_state.athlete_current_page == nav_label else "secondary"
            ):
                st.session_state.athlete_current_page = nav_label
                st.rerun()
    
    # Display current page
    page = st.session_state.athlete_current_page
    
    # Page header
    st.markdown(f"""
    <div style="border-bottom: 1px solid #E9ECEF; margin-bottom: 1.5rem; padding-bottom: 0.5rem;">
        <h1 style="color: #4361EE; font-weight: 800;">{nav_options.get(page, "")} {page}</h1>
    </div>
    """, unsafe_allow_html=True)
    
    # Render the appropriate page content
    if page == "Dashboard":
        show_athlete_dashboard(user_id, athlete_id, athlete_details)
    elif page == "Profile":
        show_profile_edit(user_id, athlete_details)
    elif page == "Gym Visits":
        show_gym_visits(athlete_id, athlete_details)
    elif page == "Reviews":
        show_reviews(athlete_id, athlete_details)
    elif page == "Messages":
        show_chat()
    elif page == "Support":
        show_support(athlete_id, athlete_details)

def show_athlete_dashboard(user_id, athlete_id, athlete_details):
    """Show the main dashboard with statistics"""
    
    # Get statistics
    stats = get_statistics_for_athlete(athlete_id)
    
    # Profile summary section
    st.markdown(f"""
    <div style="background-color: #F8F9FA; border-radius: 10px; padding: 1.5rem; margin-bottom: 1.5rem;">
        <div style="display: flex; align-items: center;">
            <div style="background-color: #4361EE; color: white; width: 60px; height: 60px; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-size: 1.8rem; margin-right: 1rem;">
                👤
            </div>
            <div>
                <h2 style="margin: 0; color: #212529;">Welcome back, {athlete_details['full_name']}</h2>
                <p style="margin: 0; color: #6C757D;">Let's check your fitness journey</p>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # Stats cards with enhanced styling
    st.markdown('<div style="margin-bottom: 1.5rem;">', unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        # Check if there are active visits for status card
        active_visits = get_active_visits(athlete_id)
        status = "Checked In" if active_visits else "Not Checked In"
        status_color = "#10B981" if active_visits else "#6C757D"
        status_icon = "✅" if active_visits else "⏱️"
        
        st.markdown(f"""
        <div style="background-color: {status_color}; border-radius: 8px; padding: 1.5rem; text-align: center; color: white;">
            <div style="font-size: 1.5rem; margin-bottom: 0.5rem;">{status_icon}</div>
            <div style="font-size: 1.8rem; font-weight: 700; margin-bottom: 0.5rem;">{status}</div>
            <div style="font-size: 0.9rem; opacity: 0.9;">Current Status</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown(f"""
        <div style="background-color: #4361EE; border-radius: 8px; padding: 1.5rem; text-align: center; color: white;">
            <div style="font-size: 1.5rem; margin-bottom: 0.5rem;">🏋️</div>
            <div style="font-size: 1.8rem; font-weight: 700; margin-bottom: 0.5rem;">{stats['visits_count']}</div>
            <div style="font-size: 0.9rem; opacity: 0.9;">Total Gym Visits</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        avg_time_minutes = stats['avg_time']
        if avg_time_minutes > 0:
            hours = int(avg_time_minutes // 60)
            minutes = int(avg_time_minutes % 60)
            time_str = f"{hours}h {minutes}m" if hours > 0 else f"{minutes}m"
        else:
            time_str = "N/A"
            
        st.markdown(f"""
        <div style="background-color: #3A0CA3; border-radius: 8px; padding: 1.5rem; text-align: center; color: white;">
            <div style="font-size: 1.5rem; margin-bottom: 0.5rem;">⏱️</div>
            <div style="font-size: 1.8rem; font-weight: 700; margin-bottom: 0.5rem;">{time_str}</div>
            <div style="font-size: 0.9rem; opacity: 0.9;">Average Session Duration</div>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Quick actions section
    st.markdown('<h3 style="color: #3A0CA3; font-weight: 700; margin: 1.5rem 0 1rem 0;">Quick Actions</h3>', unsafe_allow_html=True)
    
    action1, action2, action3 = st.columns(3)
    
    with action1:
        if active_visits:
            if st.button("📤 Check Out", key="checkout_action", use_container_width=True):
                # First active visit found
                visit_id = active_visits[0]['id']
                checkout_gym_visit(visit_id)
                st.success("Successfully checked out!")
                st.rerun()
        else:
            if st.button("📥 Check In", key="checkin_action", use_container_width=True):
                if athlete_details['gym_id']:
                    record_gym_visit(athlete_id, athlete_details['gym_id'])
                    st.success("Successfully checked in!")
                    st.rerun()
                else:
                    st.error("You need to select a gym first.")
    
    with action2:
        if st.button("👥 Find Trainer", key="find_trainer_action", use_container_width=True):
            st.session_state.athlete_current_page = "Profile"
            st.rerun()
    
    with action3:
        if st.button("🗣️ Get Support", key="get_support_action", use_container_width=True):
            st.session_state.athlete_current_page = "Support"
            st.rerun()
    
    # Display visit data chart in a styled container
    st.markdown('<div style="background-color: white; border-radius: 10px; padding: 1.5rem; margin: 1.5rem 0; box-shadow: 0 4px 6px rgba(0, 0, 0, 0.05);">', unsafe_allow_html=True)
    st.markdown('<h3 style="color: #3A0CA3; font-weight: 700; margin-bottom: 1rem;">Your Gym Visits (Last 7 Days)</h3>', unsafe_allow_html=True)
    
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
        
        # Format dates for display
        complete_df['formatted_date'] = pd.to_datetime(complete_df['visit_date']).dt.strftime('%a, %b %d')
        
        # Create bar chart with improved styling
        fig = px.bar(
            complete_df,
            x='formatted_date',
            y='visit_count',
            labels={'formatted_date': 'Date', 'visit_count': 'Visits'},
            text='visit_count'
        )
        
        # Customize chart appearance
        fig.update_traces(
            marker_color='#4361EE',
            textposition='outside',
            hovertemplate='Date: %{x}<br>Visits: %{y}'
        )
        
        fig.update_layout(
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            margin=dict(l=20, r=20, t=30, b=20),
            xaxis_title=None,
            yaxis_title="Number of Visits",
            showlegend=False,
            height=300,
            xaxis=dict(
                showgrid=False,
                tickfont=dict(size=12)
            ),
            yaxis=dict(
                showgrid=True,
                gridcolor='rgba(233,236,239,0.5)',
                tickfont=dict(size=12)
            )
        )
        
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.markdown("""
        <div style="text-align: center; padding: 2rem 0;">
            <div style="font-size: 2rem; color: #E9ECEF; margin-bottom: 1rem;">📊</div>
            <h4 style="color: #6C757D; margin-bottom: 0.5rem;">No Activity Data Yet</h4>
            <p style="color: #6C757D;">Start visiting your gym to see your activity chart here.</p>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Gym and trainer information in a styled container
    st.markdown('<div style="background-color: white; border-radius: 10px; padding: 1.5rem; margin: 1.5rem 0; box-shadow: 0 4px 6px rgba(0, 0, 0, 0.05);">', unsafe_allow_html=True)
    st.markdown('<h3 style="color: #3A0CA3; font-weight: 700; margin-bottom: 1rem;">Your Gym & Trainer</h3>', unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    
    with col1:
        if athlete_details['gym_name']:
            st.markdown(f"""
            <div style="background-color: #F8F9FA; border-radius: 10px; padding: 1.5rem; height: 100%;">
                <h4 style="color: #3A0CA3; margin-bottom: 0.5rem;">🏢 Your Gym</h4>
                <div style="background-color: white; border-left: 4px solid #4361EE; padding: 1rem; border-radius: 4px; margin-bottom: 1rem;">
                    <p style="font-weight: 600; font-size: 1.1rem; margin-bottom: 0;">{athlete_details['gym_name']}</p>
                </div>
                <div style="text-align: center; margin-top: 0.5rem;">
                    <p style="color: #6C757D; font-size: 0.9rem;">Membership is active</p>
                </div>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown("""
            <div style="background-color: #F8F9FA; border-radius: 10px; padding: 1.5rem; height: 100%; text-align: center;">
                <h4 style="color: #3A0CA3; margin-bottom: 1rem;">🏢 Your Gym</h4>
                <div style="background-color: #FFF3CD; border-left: 4px solid #FFC107; padding: 1rem; border-radius: 4px; margin-bottom: 1.5rem;">
                    <p style="font-weight: 600; margin-bottom: 0;">No gym selected</p>
                </div>
            </div>
            """, unsafe_allow_html=True)
            
            if st.button("Find a Gym", key="find_gym_btn", use_container_width=True):
                st.session_state.athlete_current_page = "Profile"
                st.rerun()
    
    with col2:
        if athlete_details['trainer_name']:
            st.markdown(f"""
            <div style="background-color: #F8F9FA; border-radius: 10px; padding: 1.5rem; height: 100%;">
                <h4 style="color: #3A0CA3; margin-bottom: 0.5rem;">👤 Your Trainer</h4>
                <div style="background-color: white; border-left: 4px solid #4361EE; padding: 1rem; border-radius: 4px; margin-bottom: 1rem;">
                    <p style="font-weight: 600; font-size: 1.1rem; margin-bottom: 0;">{athlete_details['trainer_name']}</p>
                </div>
            </div>
            """, unsafe_allow_html=True)
            
            # Add button to message trainer
            if st.button("💬 Message Your Trainer", key="msg_trainer_btn", use_container_width=True):
                # Find the user_id associated with the trainer
                st.session_state.chat_with = athlete_details['trainer_id']
                st.session_state.athlete_current_page = "Messages"
                st.rerun()
        else:
            st.markdown("""
            <div style="background-color: #F8F9FA; border-radius: 10px; padding: 1.5rem; height: 100%; text-align: center;">
                <h4 style="color: #3A0CA3; margin-bottom: 1rem;">👤 Your Trainer</h4>
                <div style="background-color: #FFF3CD; border-left: 4px solid #FFC107; padding: 1rem; border-radius: 4px; margin-bottom: 1.5rem;">
                    <p style="font-weight: 600; margin-bottom: 0;">No trainer selected</p>
                </div>
            </div>
            """, unsafe_allow_html=True)
            
            if athlete_details['gym_id']:
                # Show available trainers
                trainers = get_trainers_by_gym(athlete_details['gym_id'])
                
                if trainers:
                    with st.expander("👥 Available Trainers at Your Gym"):
                        st.markdown('<div style="max-height: 300px; overflow-y: auto;">', unsafe_allow_html=True)
                        
                        for trainer in trainers:
                            st.markdown(f"""
                            <div style="background-color: white; border-radius: 8px; padding: 1rem; margin-bottom: 1rem; border: 1px solid #E9ECEF;">
                                <h4 style="color: #3A0CA3; margin-bottom: 0.5rem;">{trainer['full_name']}</h4>
                                <p style="margin-bottom: 0.3rem;"><span style="color: #6C757D;">Specialization:</span> {trainer['specialization'] or 'General'}</p>
                                <p style="margin-bottom: 0.5rem;"><span style="color: #6C757D;">Experience:</span> {trainer['experience'] or 0} years</p>
                            </div>
                            """, unsafe_allow_html=True)
                            
                            if st.button(f"Select {trainer['full_name']}", key=f"select_{trainer['id']}", use_container_width=True):
                                # Update athlete with selected trainer
                                success = save_athlete_details(
                                    user_id,
                                    athlete_details['full_name'],
                                    athlete_details['age'],
                                    athlete_details['gender'],
                                    athlete_details['weight'],
                                    athlete_details['height'],
                                    athlete_details['goals'],
                                    athlete_details['medical_conditions'],
                                    athlete_details['gym_id'],
                                    trainer['id']
                                )
                                
                                if success:
                                    st.success(f"You've selected {trainer['full_name']} as your trainer!")
                                    st.rerun()
                                else:
                                    st.error("An error occurred. Please try again.")
                        
                        st.markdown('</div>', unsafe_allow_html=True)
                else:
                    st.info("No trainers available at your gym.")
                    
            else:
                if st.button("Find a Trainer", key="find_trainer_btn", use_container_width=True):
                    st.session_state.athlete_current_page = "Profile"
                    st.rerun()
                    
    # Close the container div
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Tips or motivation section
    st.markdown("""
    <div style="background-color: #F8F9FA; border-radius: 10px; padding: 1.5rem; margin-top: 1.5rem;">
        <h4 style="color: #4361EE; margin-bottom: 0.5rem;">💡 Fitness Tip of the Day</h4>
        <p style="margin-bottom: 0;">Consistency is key! Even a short workout is better than no workout. Aim for at least 30 minutes of activity most days of the week.</p>
    </div>
    """, unsafe_allow_html=True)

def show_profile_edit(user_id, athlete_details):
    """Show the profile edit form for athletes"""
    st.title("Your Profile")
    
    with st.form("edit_profile_form"):
        full_name = st.text_input("Full Name*", value=athlete_details['full_name'])
        
        col1, col2 = st.columns(2)
        with col1:
            age = st.number_input("Age*", min_value=1, max_value=100, step=1, value=athlete_details['age'])
        with col2:
            gender = st.selectbox("Gender*", ["Male", "Female", "Other"], index=["Male", "Female", "Other"].index(athlete_details['gender']))
        
        col1, col2 = st.columns(2)
        with col1:
            weight = st.number_input("Weight (kg)*", min_value=1.0, max_value=300.0, step=0.1, value=athlete_details['weight'])
        with col2:
            height = st.number_input("Height (cm)*", min_value=1.0, max_value=300.0, step=0.1, value=athlete_details['height'])
        
        goals = st.text_area("Fitness Goals*", value=athlete_details['goals'])
        medical_conditions = st.text_area("Medical Conditions (if any)", value=athlete_details['medical_conditions'] or "")
        
        # Get all available gyms
        gyms = get_all_gyms()
        
        # Gym selection
        selected_gym = st.selectbox(
            "Select Your Gym*",
            options=[g['id'] for g in gyms],
            index=[i for i, g in enumerate(gyms) if g['id'] == athlete_details['gym_id']][0] if athlete_details['gym_id'] in [g['id'] for g in gyms] else 0,
            format_func=lambda x: next((g['gym_name'] for g in gyms if g['id'] == x), x)
        )
        
        # Get trainers for selected gym
        trainers = get_trainers_by_gym(selected_gym)
        
        # Trainer selection
        if trainers:
            trainer_options = [("None", "No trainer")] + [(str(t['id']), f"{t['full_name']} - {t['specialization']} ({t['experience']} years)") for t in trainers]
            
            default_index = 0
            if athlete_details['trainer_id'] is not None:
                # Find index of the current trainer
                for i, (tid, _) in enumerate(trainer_options):
                    if tid != "None" and int(tid) == athlete_details['trainer_id']:
                        default_index = i
                        break
            
            selected_trainer = st.selectbox(
                "Select Your Trainer (if applicable)",
                options=[t[0] for t in trainer_options],
                index=default_index,
                format_func=lambda x: next((t[1] for t in trainer_options if t[0] == x), x)
            )
        else:
            st.info("No trainers available in this gym yet.")
            selected_trainer = "None"
        
        submit_button = st.form_submit_button("Update Profile")
        
        if submit_button:
            if not full_name or age < 1 or not gender or weight < 1 or height < 1 or not goals:
                st.error("Please fill all required fields.")
            else:
                # Process trainer selection
                trainer_id = None if selected_trainer == "None" else int(selected_trainer)
                
                # Save athlete details
                success = save_athlete_details(
                    user_id, full_name, age, gender, weight, height, 
                    goals, medical_conditions, selected_gym, trainer_id
                )
                
                if success:
                    st.success("Profile updated successfully!")
                    st.rerun()
                else:
                    st.error("An error occurred. Please try again.")

def show_gym_visits(athlete_id, athlete_details):
    """Show gym visits and check-in/check-out functionality"""
    st.title("Gym Visits")
    
    # Check for active visits
    active_visits = get_active_visits(athlete_id)
    
    if active_visits:
        st.subheader("You're Currently Checked In")
        
        for visit in active_visits:
            with st.expander(f"Checked in at {visit['gym_name']} - {format_datetime(visit['check_in_time'])}", expanded=True):
                st.write(f"Check-in time: {format_datetime(visit['check_in_time'])}")
                st.write(f"Duration so far: {calculate_duration(visit['check_in_time'])}")
                
                if st.button(f"Check Out from {visit['gym_name']}", key=f"checkout_{visit['id']}"):
                    success = checkout_gym_visit(visit['id'])
                    
                    if success:
                        st.success("Checked out successfully!")
                        st.rerun()
                    else:
                        st.error("An error occurred. Please try again.")
    else:
        st.subheader("Check In to Gym")
        
        if athlete_details['gym_id']:
            if st.button(f"Check In to {athlete_details['gym_name']}"):
                success = record_gym_visit(athlete_id, athlete_details['gym_id'])
                
                if success:
                    st.success("Checked in successfully!")
                    st.rerun()
                else:
                    st.error("An error occurred. Please try again.")
        else:
            st.warning("You need to select a gym in your profile first.")
    
    # Visit history
    st.subheader("Visit History")
    
    visit_history = get_visit_history(athlete_id)
    
    if visit_history:
        for visit in visit_history:
            with st.expander(f"{visit['gym_name']} - {format_datetime(visit['check_in_time'])}"):
                st.write(f"Check-in: {format_datetime(visit['check_in_time'])}")
                st.write(f"Check-out: {format_datetime(visit['check_out_time'])}")
                st.write(f"Duration: {calculate_duration(visit['check_in_time'], visit['check_out_time'])}")
    else:
        st.info("No visit history available.")

def show_reviews(athlete_id, athlete_details):
    """Show and add reviews for gyms and trainers"""
    st.title("Reviews")
    
    # Create tabs for gym reviews and trainer reviews
    gym_tab, trainer_tab = st.tabs(["Gym Reviews", "Trainer Reviews"])
    
    with gym_tab:
        st.subheader("Review Your Gym")
        
        if athlete_details['gym_id']:
            # Show existing reviews for this gym
            gym_reviews = get_gym_reviews(athlete_details['gym_id'])
            
            # Form to add a new review
            with st.form("add_gym_review"):
                st.write(f"Add a review for {athlete_details['gym_name']}")
                
                rating = st.slider("Rating", 1, 5, 5)
                comment = st.text_area("Comment")
                
                submit_button = st.form_submit_button("Submit Review")
                
                if submit_button:
                    success = add_review(athlete_id, gym_id=athlete_details['gym_id'], rating=rating, comment=comment)
                    
                    if success:
                        st.success("Review submitted successfully!")
                        st.rerun()
                    else:
                        st.error("An error occurred. Please try again.")
            
            # Display existing reviews
            if gym_reviews:
                st.subheader(f"Reviews for {athlete_details['gym_name']}")
                
                for review in gym_reviews:
                    with st.expander(f"{review['athlete_name']} - {create_star_rating(review['rating'])} - {format_time_ago(review['created_at'])}"):
                        st.write(f"**Rating:** {create_star_rating(review['rating'])}")
                        st.write(f"**Comment:** {review['comment'] if review['comment'] else 'No comment provided'}")
                        st.write(f"**Date:** {format_time_ago(review['created_at'])}")
            else:
                st.info("No reviews available for this gym.")
        else:
            st.warning("You need to select a gym in your profile first.")
    
    with trainer_tab:
        st.subheader("Review Your Trainer")
        
        if athlete_details['trainer_id']:
            # Show existing reviews for this trainer
            trainer_reviews = get_trainer_reviews(athlete_details['trainer_id'])
            
            # Form to add a new review
            with st.form("add_trainer_review"):
                st.write(f"Add a review for {athlete_details['trainer_name']}")
                
                rating = st.slider("Rating", 1, 5, 5, key="trainer_rating")
                comment = st.text_area("Comment", key="trainer_comment")
                
                submit_button = st.form_submit_button("Submit Review")
                
                if submit_button:
                    success = add_review(athlete_id, trainer_id=athlete_details['trainer_id'], rating=rating, comment=comment)
                    
                    if success:
                        st.success("Review submitted successfully!")
                        st.rerun()
                    else:
                        st.error("An error occurred. Please try again.")
            
            # Display existing reviews
            if trainer_reviews:
                st.subheader(f"Reviews for {athlete_details['trainer_name']}")
                
                for review in trainer_reviews:
                    with st.expander(f"{review['athlete_name']} - {create_star_rating(review['rating'])} - {format_time_ago(review['created_at'])}"):
                        st.write(f"**Rating:** {create_star_rating(review['rating'])}")
                        st.write(f"**Comment:** {review['comment'] if review['comment'] else 'No comment provided'}")
                        st.write(f"**Date:** {format_time_ago(review['created_at'])}")
            else:
                st.info("No reviews available for this trainer.")
        else:
            st.warning("You need to select a trainer in your profile first.")
