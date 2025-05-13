import streamlit as st
import pandas as pd
import altair as alt
from database import (
    get_statistics_for_gym, get_statistics_for_trainer, get_statistics_for_athlete,
    get_gym_id_from_user_id, get_trainer_id_from_user_id, get_athlete_id_from_user_id
)
from utils import UserType

def show_dashboard():
    """Show appropriate dashboard based on user type"""
    user_id = st.session_state.user_id
    user_type = st.session_state.user_type
    
    if user_type == UserType.GYM_MANAGER.value:
        gym_id = get_gym_id_from_user_id(user_id)
        if gym_id:
            show_gym_dashboard(gym_id)
        else:
            st.warning("Please complete your gym profile first.")
    
    elif user_type == UserType.TRAINER.value:
        trainer_id = get_trainer_id_from_user_id(user_id)
        if trainer_id:
            show_trainer_dashboard(trainer_id)
        else:
            st.warning("Please complete your trainer profile first.")
    
    elif user_type == UserType.ATHLETE.value:
        athlete_id = get_athlete_id_from_user_id(user_id)
        if athlete_id:
            show_athlete_dashboard(athlete_id)
        else:
            st.warning("Please complete your athlete profile first.")

def show_gym_dashboard(gym_id):
    """Show dashboard for gym managers"""
    st.title("Gym Dashboard")
    
    # Get statistics
    stats = get_statistics_for_gym(gym_id)
    
    # Display KPI metrics
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Total Members", stats['members_count'])
    
    with col2:
        st.metric("Total Trainers", stats['trainers_count'])
    
    with col3:
        st.metric("Average Rating", f"{stats['avg_rating']:.1f}/5.0")
    
    # Visits chart
    st.subheader("Daily Visits")
    
    if stats['visits_data']:
        visits_df = pd.DataFrame(stats['visits_data'])
        
        chart = alt.Chart(visits_df).mark_bar().encode(
            x=alt.X('visit_date:T', title='Date'),
            y=alt.Y('visit_count:Q', title='Number of Visits'),
            tooltip=['visit_date', 'visit_count']
        ).properties(
            width='container',
            height=300
        )
        
        st.altair_chart(chart, use_container_width=True)
    else:
        st.info("No visit data available.")
    
    # Athletes per trainer
    st.subheader("Athletes per Trainer")
    
    if stats['athletes_per_trainer']:
        trainers_df = pd.DataFrame(stats['athletes_per_trainer'])
        
        chart = alt.Chart(trainers_df).mark_bar().encode(
            x=alt.X('full_name:N', title='Trainer'),
            y=alt.Y('athlete_count:Q', title='Number of Athletes'),
            tooltip=['full_name', 'athlete_count']
        ).properties(
            width='container',
            height=300
        )
        
        st.altair_chart(chart, use_container_width=True)
    else:
        st.info("No trainer data available.")

def show_trainer_dashboard(trainer_id):
    """Show dashboard for trainers"""
    st.title("Trainer Dashboard")
    
    # Get statistics
    stats = get_statistics_for_trainer(trainer_id)
    
    # Display KPI metrics
    col1, col2 = st.columns(2)
    
    with col1:
        st.metric("Total Athletes", stats['athletes_count'])
    
    with col2:
        st.metric("Average Rating", f"{stats['avg_rating']:.1f}/5.0")
    
    # Athletes list
    st.subheader("Your Athletes")
    
    if stats['athletes']:
        athletes_df = pd.DataFrame(stats['athletes'])
        
        st.dataframe(
            athletes_df[['full_name', 'age', 'gender', 'goals']],
            column_config={
                "full_name": "Name",
                "age": "Age",
                "gender": "Gender",
                "goals": "Goals"
            },
            use_container_width=True
        )
    else:
        st.info("You don't have any athletes yet.")

def show_athlete_dashboard(athlete_id):
    """Show dashboard for athletes"""
    st.title("Athlete Dashboard")
    
    # Get statistics
    stats = get_statistics_for_athlete(athlete_id)
    
    # Display KPI metrics
    col1, col2 = st.columns(2)
    
    with col1:
        st.metric("Total Visits", stats['visits_count'])
    
    with col2:
        avg_time_minutes = stats['avg_time']
        if avg_time_minutes > 0:
            hours = int(avg_time_minutes // 60)
            minutes = int(avg_time_minutes % 60)
            time_str = f"{hours}h {minutes}m" if hours > 0 else f"{minutes}m"
            st.metric("Average Session Length", time_str)
        else:
            st.metric("Average Session Length", "N/A")
    
    # Visits chart
    st.subheader("Your Gym Visits")
    
    if stats['visits_data']:
        visits_df = pd.DataFrame(stats['visits_data'])
        
        chart = alt.Chart(visits_df).mark_bar().encode(
            x=alt.X('visit_date:T', title='Date'),
            y=alt.Y('visit_count:Q', title='Number of Visits'),
            tooltip=['visit_date', 'visit_count']
        ).properties(
            width='container',
            height=300
        )
        
        st.altair_chart(chart, use_container_width=True)
    else:
        st.info("No visit data available.")
