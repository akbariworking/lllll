import streamlit as st
import os
import sqlite3
from auth import authenticate, signup, logout
from database import init_db, get_user_data
from utils import user_redirect, UserType, check_session

# Import modules directly to avoid package conflicts
import pages.gym_manager as gym_manager
import pages.trainer as trainer
import pages.athlete as athlete

# Configure Streamlit page
st.set_page_config(
    page_title="Gym Management System",
    page_icon="💪",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Load custom CSS
def load_css():
    with open('.streamlit/style.css') as f:
        st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)

# Load custom CSS
load_css()

# Initialize database
init_db()

# Initialize session state variables if they don't exist
if 'authenticated' not in st.session_state:
    st.session_state.authenticated = False
if 'user_id' not in st.session_state:
    st.session_state.user_id = None
if 'user_type' not in st.session_state:
    st.session_state.user_type = None
if 'username' not in st.session_state:
    st.session_state.username = None

# Main application
def main():
    # Sidebar for navigation
    with st.sidebar:
        # Apply custom styling
        st.markdown('<div class="sidebar-header">', unsafe_allow_html=True)
        st.markdown('<h1 style="color: #4361EE; font-weight: 800;">💪 Gym Management System</h1>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)
        
        if st.session_state.authenticated:
            # User profile section
            st.markdown(f"""
            <div style="background-color: #E9ECEF; border-radius: 10px; padding: 1rem; margin-bottom: 1rem;">
                <h3 style="margin-bottom: 0.5rem; color: #3A0CA3;">Welcome!</h3>
                <p style="font-weight: bold; font-size: 1.2rem; margin-bottom: 0.2rem;">{st.session_state.username}</p>
                <p style="color: #6C757D; font-size: 0.9rem;">{st.session_state.user_type}</p>
            </div>
            """, unsafe_allow_html=True)
            
            # Styled logout button
            if st.button("🚪 Logout", key="logout", use_container_width=True):
                logout()
                st.rerun()
        else:
            # Create tabs for login and signup with enhanced styling
            login_tab, signup_tab = st.tabs(["🔑 Login", "✏️ Sign Up"])
            
            with login_tab:
                st.markdown('<h2 style="color: #4361EE; font-weight: 700; margin-bottom: 1.5rem;">Login</h2>', unsafe_allow_html=True)
                
                with st.container():
                    username = st.text_input("Username", key="login_username", placeholder="Enter your username")
                    password = st.text_input("Password", type="password", key="login_password", placeholder="Enter your password")
                    
                    user_type = st.selectbox(
                        "I am a:",
                        (UserType.GYM_MANAGER.value, UserType.TRAINER.value, UserType.ATHLETE.value),
                        key="login_user_type",
                        format_func=lambda x: {
                            "Gym Manager": "🏢 Gym Manager",
                            "Trainer": "👟 Trainer", 
                            "Athlete": "🏋️ Athlete"
                        }.get(x, x)
                    )
                    
                    st.markdown('<div style="height: 1rem;"></div>', unsafe_allow_html=True)
                    
                    # Styled login button
                    col1, col2 = st.columns([2, 3])
                    with col2:
                        if st.button("Login", key="login_button", use_container_width=True, type="primary"):
                            if authenticate(username, password, user_type):
                                # Show success message with animation
                                st.markdown("""
                                <div style="background-color: #D1FAE5; border-radius: 5px; padding: 1rem; border-left: 4px solid #10B981; margin: 1rem 0;">
                                    <p style="color: #047857; margin: 0; font-weight: 600;">Login successful! Redirecting...</p>
                                </div>
                                """, unsafe_allow_html=True)
                                st.rerun()
                            else:
                                # Styled error message
                                st.markdown("""
                                <div style="background-color: #FEE2E2; border-radius: 5px; padding: 1rem; border-left: 4px solid #EF4444; margin: 1rem 0;">
                                    <p style="color: #B91C1C; margin: 0; font-weight: 600;">Invalid credentials. Please try again.</p>
                                </div>
                                """, unsafe_allow_html=True)
            
            with signup_tab:
                st.markdown('<h2 style="color: #4361EE; font-weight: 700; margin-bottom: 1.5rem;">Create Account</h2>', unsafe_allow_html=True)
                
                with st.container():
                    # Initialize the session state for suggested usernames
                    if 'username_suggestions' not in st.session_state:
                        st.session_state.username_suggestions = []
                    
                    # Full name is used as display name
                    display_name = st.text_input("Full Name", key="signup_display_name", placeholder="Your full name")
                    
                    # Username with @ symbol prefix for visual indication
                    username_col, _ = st.columns([3, 1])
                    with username_col:
                        new_username = st.text_input(
                            "Username", 
                            key="signup_username", 
                            placeholder="Choose a unique username (no spaces or special characters)"
                        )
                        if new_username:
                            st.markdown(f"<p style='color: #6C757D; font-size: 0.9rem;'>Your profile will appear as: <strong>@{new_username}</strong></p>", 
                                     unsafe_allow_html=True)
                    
                    # Show username suggestions if available
                    if st.session_state.username_suggestions:
                        st.write("This username is already taken. Try one of these instead:")
                        suggestion_cols = st.columns(3)
                        for i, suggestion in enumerate(st.session_state.username_suggestions):
                            with suggestion_cols[i]:
                                if st.button(f"@{suggestion}", key=f"suggestion_{i}", use_container_width=True):
                                    st.session_state.signup_username = suggestion
                                    st.session_state.username_suggestions = []
                                    st.rerun()
                    
                    new_password = st.text_input("Create Password", type="password", key="signup_password", placeholder="Create a strong password")
                    confirm_password = st.text_input("Confirm Password", type="password", key="confirm_password", placeholder="Re-enter your password")
                    
                    new_user_type = st.selectbox(
                        "I am a:",
                        (UserType.GYM_MANAGER.value, UserType.TRAINER.value, UserType.ATHLETE.value),
                        key="signup_user_type",
                        format_func=lambda x: {
                            "Gym Manager": "🏢 Gym Manager",
                            "Trainer": "👟 Trainer", 
                            "Athlete": "🏋️ Athlete"
                        }.get(x, x)
                    )
                    
                    # Extra message for trainers about approval
                    if new_user_type == UserType.TRAINER.value:
                        st.info("As a trainer, your profile will need to be approved by a gym manager before you can use the system.")
                    
                    st.markdown('<div style="height: 1rem;"></div>', unsafe_allow_html=True)
                    
                    # Help text
                    with st.expander("Why choose this account type?"):
                        st.markdown("""
                        - **Gym Manager**: For gym owners and administrative staff who manage facilities, membership plans, and staff.
                        - **Trainer**: For fitness instructors who work with athletes and need to track client progress.
                        - **Athlete**: For gym members who want to track their workouts, find trainers, and manage their membership.
                        """)
                    
                    # Styled signup button
                    col1, col2 = st.columns([2, 3])
                    with col2:
                        if st.button("Create Account", key="signup_button", use_container_width=True, type="primary"):
                            # Validate input
                            if not display_name:
                                st.markdown("""
                                <div style="background-color: #FEE2E2; border-radius: 5px; padding: 1rem; border-left: 4px solid #EF4444; margin: 1rem 0;">
                                    <p style="color: #B91C1C; margin: 0; font-weight: 600;">Please enter your full name.</p>
                                </div>
                                """, unsafe_allow_html=True)
                            elif not new_username:
                                st.markdown("""
                                <div style="background-color: #FEE2E2; border-radius: 5px; padding: 1rem; border-left: 4px solid #EF4444; margin: 1rem 0;">
                                    <p style="color: #B91C1C; margin: 0; font-weight: 600;">Please choose a username.</p>
                                </div>
                                """, unsafe_allow_html=True)
                            elif new_password != confirm_password:
                                # Styled error message
                                st.markdown("""
                                <div style="background-color: #FEE2E2; border-radius: 5px; padding: 1rem; border-left: 4px solid #EF4444; margin: 1rem 0;">
                                    <p style="color: #B91C1C; margin: 0; font-weight: 600;">Passwords do not match!</p>
                                </div>
                                """, unsafe_allow_html=True)
                            else:
                                # Try to create the account
                                signup_result = signup(new_username, display_name, new_password, new_user_type)
                                
                                if signup_result.get("success"):
                                    # Success message with animation
                                    st.markdown("""
                                    <div style="background-color: #D1FAE5; border-radius: 5px; padding: 1rem; border-left: 4px solid #10B981; margin: 1rem 0;">
                                        <p style="color: #047857; margin: 0; font-weight: 600;">Account created successfully! Please login.</p>
                                    </div>
                                    """, unsafe_allow_html=True)
                                elif signup_result.get("error") == "username_taken":
                                    # Store suggestions in session state for display
                                    st.session_state.username_suggestions = signup_result.get("suggestions", [])
                                    st.rerun()  # Rerun to display the suggestions
                                else:
                                    # Generic error message
                                    st.markdown("""
                                    <div style="background-color: #FEE2E2; border-radius: 5px; padding: 1rem; border-left: 4px solid #EF4444; margin: 1rem 0;">
                                        <p style="color: #B91C1C; margin: 0; font-weight: 600;">An error occurred. Please try again.</p>
                                    </div>
                                    """, unsafe_allow_html=True)

    # Main content area
    if st.session_state.authenticated:
        # Redirect to appropriate page based on user type
        if st.session_state.user_type == UserType.GYM_MANAGER.value:
            gym_manager.show()
        elif st.session_state.user_type == UserType.TRAINER.value:
            trainer.show()
        elif st.session_state.user_type == UserType.ATHLETE.value:
            athlete.show()
    else:
        # Hero section
        st.markdown('<h1 class="main-title">Fitness Management System</h1>', unsafe_allow_html=True)
        st.markdown('<p class="subtitle">A complete solution for gyms, trainers, and athletes</p>', unsafe_allow_html=True)
        
        # Hero image/banner
        st.markdown("""
        <div style="background-color: #4361EE; padding: 2rem; border-radius: 10px; margin-bottom: 2rem; text-align: center;">
            <h2 style="color: white; font-weight: 800; margin-bottom: 1rem; font-size: 2rem;">Transform Your Fitness Journey</h2>
            <p style="color: white; font-size: 1.2rem; margin-bottom: 1.5rem;">Manage, track, and optimize fitness experiences for everyone in your gym ecosystem</p>
            <div style="display: flex; justify-content: center; gap: 1rem;">
                <div style="background-color: white; color: #4361EE; padding: 0.5rem 1rem; border-radius: 5px; font-weight: bold;">Setup in minutes</div>
                <div style="background-color: white; color: #4361EE; padding: 0.5rem 1rem; border-radius: 5px; font-weight: bold;">Real-time tracking</div>
                <div style="background-color: white; color: #4361EE; padding: 0.5rem 1rem; border-radius: 5px; font-weight: bold;">Seamless communication</div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        # Feature section
        st.markdown('<h2 style="color: #3A0CA3; font-weight: 700; margin-bottom: 1.5rem;">Platform Features</h2>', unsafe_allow_html=True)
        
        # Three columns for different user types with enhanced styling
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.markdown("""
            <div class="card">
                <div style="font-size: 2rem; color: #4361EE; margin-bottom: 1rem;">🏢</div>
                <h3 style="color: #3A0CA3; font-weight: 700; margin-bottom: 0.8rem;">For Gym Managers</h3>
                <div class="feature-card">📊 Comprehensive analytics dashboard</div>
                <div class="feature-card">💰 Create and manage membership plans</div>
                <div class="feature-card">👥 Oversee trainers and staff</div>
                <div class="feature-card">🔍 Monitor facility usage</div>
                <div class="feature-card">⭐ View feedback and reviews</div>
            </div>
            """, unsafe_allow_html=True)
        
        with col2:
            st.markdown("""
            <div class="card">
                <div style="font-size: 2rem; color: #4361EE; margin-bottom: 1rem;">👟</div>
                <h3 style="color: #3A0CA3; font-weight: 700; margin-bottom: 0.8rem;">For Trainers</h3>
                <div class="feature-card">📋 Manage client profiles</div>
                <div class="feature-card">📝 Track athlete progress</div>
                <div class="feature-card">💬 Direct messaging with clients</div>
                <div class="feature-card">📱 Schedule and manage sessions</div>
                <div class="feature-card">📊 Performance analytics</div>
            </div>
            """, unsafe_allow_html=True)
        
        with col3:
            st.markdown("""
            <div class="card">
                <div style="font-size: 2rem; color: #4361EE; margin-bottom: 1rem;">🏋️</div>
                <h3 style="color: #3A0CA3; font-weight: 700; margin-bottom: 0.8rem;">For Athletes</h3>
                <div class="feature-card">🔍 Find and select your gym</div>
                <div class="feature-card">👥 Choose the right trainer</div>
                <div class="feature-card">📅 Track workout sessions</div>
                <div class="feature-card">💬 Communicate with trainers</div>
                <div class="feature-card">🎯 Set and monitor fitness goals</div>
            </div>
            """, unsafe_allow_html=True)
        
        # Testimonials/trust signals
        st.markdown('<h2 style="color: #3A0CA3; font-weight: 700; margin: 2rem 0 1.5rem 0;">Why Choose Us</h2>', unsafe_allow_html=True)
        
        testimonial1, testimonial2, testimonial3 = st.columns(3)
        
        with testimonial1:
            st.markdown("""
            <div style="background-color: #F8F9FA; padding: 1.5rem; border-radius: 10px; position: relative;">
                <div style="color: #4361EE; font-size: 2rem; position: absolute; top: -15px; left: 20px;">"</div>
                <p style="font-style: italic; margin-bottom: 1rem;">This system has transformed how we manage our gym. The analytics alone have helped us optimize our membership plans and increase retention by 30%.</p>
                <p style="font-weight: 600; margin-bottom: 0;">— Sarah J.</p>
                <p style="color: #6C757D; font-size: 0.9rem;">Gym Owner</p>
            </div>
            """, unsafe_allow_html=True)
            
        with testimonial2:
            st.markdown("""
            <div style="background-color: #F8F9FA; padding: 1.5rem; border-radius: 10px; position: relative;">
                <div style="color: #4361EE; font-size: 2rem; position: absolute; top: -15px; left: 20px;">"</div>
                <p style="font-style: italic; margin-bottom: 1rem;">As a trainer, I can finally focus on my clients instead of paperwork. The progress tracking and communication tools are exceptional.</p>
                <p style="font-weight: 600; margin-bottom: 0;">— Mike T.</p>
                <p style="color: #6C757D; font-size: 0.9rem;">Fitness Trainer</p>
            </div>
            """, unsafe_allow_html=True)
            
        with testimonial3:
            st.markdown("""
            <div style="background-color: #F8F9FA; padding: 1.5rem; border-radius: 10px; position: relative;">
                <div style="color: #4361EE; font-size: 2rem; position: absolute; top: -15px; left: 20px;">"</div>
                <p style="font-style: italic; margin-bottom: 1rem;">Being able to track my progress and communicate with my trainer has made a huge difference in my fitness journey. I'm seeing better results than ever.</p>
                <p style="font-weight: 600; margin-bottom: 0;">— Elena R.</p>
                <p style="color: #6C757D; font-size: 0.9rem;">Active Member</p>
            </div>
            """, unsafe_allow_html=True)
            
        # Call to action
        st.markdown("""
        <div style="background-color: #E9ECEF; padding: 2rem; border-radius: 10px; margin: 2rem 0; text-align: center;">
            <h2 style="color: #3A0CA3; font-weight: 700; margin-bottom: 1rem;">Ready to get started?</h2>
            <p style="font-size: 1.1rem; margin-bottom: 1.5rem;">Sign up now to experience the benefits of our comprehensive fitness management system.</p>
            <p style="font-weight: 600; color: #4361EE;">Click the "Sign Up" tab in the sidebar to create your account!</p>
        </div>
        """, unsafe_allow_html=True)
        
        # Footer
        st.markdown("""
        <div style="margin-top: 3rem; text-align: center; color: #6C757D; font-size: 0.9rem;">
            <p>© 2025 Fitness Management System. All rights reserved.</p>
        </div>
        """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()
