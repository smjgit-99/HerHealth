"""Supabase-powered authentication for HerHealth."""
import streamlit as st
from supabase import create_client, Client

@st.cache_resource
def get_supabase_client() -> Client:
    url = st.secrets["supabase"]["url"]
    key = st.secrets["supabase"]["key"]
    return create_client(url, key)

def register_user(email: str, password: str, full_name: str):
    """Registers a new user in Supabase Auth."""
    supabase = get_supabase_client()
    try:
        response = supabase.auth.sign_up({
            "email": email.strip().lower(),
            "password": password,
            "options": {
                "data": {"full_name": full_name.strip()}
            }
        })
        return response.user, None
    except Exception as e:
        return None, str(e)

def login_user(email: str, password: str):
    """Logs in an existing user via Supabase Auth and caches tokens."""
    supabase = get_supabase_client()
    try:
        response = supabase.auth.sign_in_with_password({
            "email": email.strip().lower(),
            "password": password
        })
        
        # CRUCIAL: Cache tokens in session state so Streamlit survives page refreshes
        if response.session:
            st.session_state["supabase_session"] = {
                "access_token": response.session.access_token,
                "refresh_token": response.session.refresh_token
            }
            
        return response.user, None
    except Exception as e:
        return None, str(e)

def sign_out():
    """Signs out the current user session."""
    supabase = get_supabase_client()
    try:
        supabase.auth.sign_out()
    except Exception:
        pass