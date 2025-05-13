import streamlit as st
from database import (
    get_support_tickets, create_support_ticket, respond_to_ticket,
    update_ticket_status, get_ticket_responses
)
from utils import check_session, format_time_ago

def show_support(athlete_id, athlete_details):
    """Show the support interface for athletes"""
    check_session()
    
    st.title("Support")
    
    if not athlete_details['gym_id']:
        st.warning("You need to select a gym in your profile first.")
        return
    
    # Get tickets
    tickets = get_support_tickets(athlete_id=athlete_id)
    
    # Create tabs for new ticket and existing tickets
    new_tab, existing_tab = st.tabs(["New Support Ticket", "Your Tickets"])
    
    with new_tab:
        show_new_ticket_form(athlete_id, athlete_details)
    
    with existing_tab:
        show_existing_tickets(athlete_id, tickets)

def show_new_ticket_form(athlete_id, athlete_details):
    """Show form to create a new support ticket"""
    st.subheader("Create Support Ticket")
    
    with st.form("new_ticket_form"):
        subject = st.text_input("Subject*")
        message = st.text_area("Message*", height=150)
        
        submit_button = st.form_submit_button("Submit Ticket")
        
        if submit_button:
            if not subject or not message:
                st.error("Please fill all required fields.")
            else:
                success = create_support_ticket(athlete_id, athlete_details['gym_id'], subject, message)
                
                if success:
                    st.success("Ticket submitted successfully!")
                    st.rerun()
                else:
                    st.error("An error occurred. Please try again.")

def show_existing_tickets(athlete_id, tickets):
    """Show existing support tickets"""
    st.subheader("Your Support Tickets")
    
    if not tickets:
        st.info("You haven't submitted any support tickets yet.")
        return
    
    # Filter tickets by status
    status_filter = st.selectbox(
        "Filter by status",
        ["All", "open", "in progress", "closed"]
    )
    
    filtered_tickets = tickets
    if status_filter != "All":
        filtered_tickets = [t for t in tickets if t['status'] == status_filter]
    
    if not filtered_tickets:
        st.info(f"No tickets with status '{status_filter}'.")
        return
    
    # Display tickets
    for ticket in filtered_tickets:
        with st.expander(f"{ticket['subject']} - {ticket['status'].upper()} - {format_time_ago(ticket['created_at'])}"):
            st.write(f"**Status:** {ticket['status'].upper()}")
            st.write(f"**Created:** {format_time_ago(ticket['created_at'])}")
            st.write(f"**Gym:** {ticket['gym_name']}")
            st.write(f"**Subject:** {ticket['subject']}")
            st.write("**Your message:**")
            st.write(ticket['message'])
            
            # Get responses
            responses = get_ticket_responses(ticket['id'])
            
            if responses:
                st.write("---")
                st.write("**Responses:**")
                
                for response in responses:
                    st.write(f"{response['username']} ({response['user_type']}): {response['message']}")
                    st.write(f"*{format_time_ago(response['created_at'])}*")
            
            # Allow responding if ticket is not closed
            if ticket['status'] != 'closed':
                st.write("---")
                with st.form(f"respond_ticket_{ticket['id']}"):
                    response = st.text_area("Add additional information", key=f"response_{ticket['id']}")
                    
                    submit_button = st.form_submit_button("Send Response")
                    
                    if submit_button:
                        if response:
                            success = respond_to_ticket(ticket['id'], st.session_state.user_id, response)
                            
                            if success:
                                st.success("Response sent successfully!")
                                st.rerun()
                            else:
                                st.error("An error occurred. Please try again.")
