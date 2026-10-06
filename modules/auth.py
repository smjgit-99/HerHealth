import streamlit as st
from supabase import create_client, Client

def get_supabase_client() -> Client:
    """Returns a fresh or restored Supabase client instance."""
    url = st.secrets["supabase"]["url"]
    key = st.secrets["supabase"]["key"]
    
    client = create_client(url, key)
    
    if "supabase_session" in st.session_state:
        try:
            sess = st.session_state["supabase_session"]
            client.auth.set_session(
                access_token=sess["access_token"],
                refresh_token=sess["refresh_token"]
            )
        except Exception:
            pass
            
    return client

def get_current_user():
    """Validates and retrieves the current authenticated user safely on F5 refresh."""
    if "supabase_session" not in st.session_state:
        return None
    
    sess = st.session_state["supabase_session"]
    access_token = sess.get("access_token")
    refresh_token = sess.get("refresh_token")
    
    try:
        supabase = get_supabase_client()
        # Directly pass the access token to ensure robust validation on refresh
        response = supabase.auth.get_user(access_token)
        if response and response.user:
            st.session_state["logged_in"] = True
            st.session_state["user_data"] = response.user
            return response.user
    except Exception:
        pass

    # Fallback: Try refreshing the session if the access token expired
    try:
        supabase = get_supabase_client()
        refreshed = supabase.auth.refresh_session(refresh_token)
        if refreshed and refreshed.session and refreshed.user:
            st.session_state["supabase_session"] = {
                "access_token": refreshed.session.access_token,
                "refresh_token": refreshed.session.refresh_token
            }
            st.session_state["logged_in"] = True
            st.session_state["user_data"] = refreshed.user
            return refreshed.user
    except Exception:
        pass
            
    # Clear invalid session state
    st.session_state.pop("supabase_session", None)
    st.session_state.pop("user_data", None)
    st.session_state.pop("logged_in", None)
    return None

def login_user(email: str, password: str):
    """Logs in a user and stores their session tokens."""
    try:
        supabase = get_supabase_client()
        response = supabase.auth.sign_in_with_password({
            "email": email,
            "password": password
        })
        if response.session and response.user:
            st.session_state["supabase_session"] = {
                "access_token": response.session.access_token,
                "refresh_token": response.session.refresh_token
            }
            st.session_state["logged_in"] = True
            st.session_state["user_data"] = response.user
        return response.user, None
    except Exception as e:
        return None, str(e)

def register_user(email: str, password: str, full_name: str):
    """Registers a new user with Supabase Auth."""
    try:
        supabase = get_supabase_client()
        response = supabase.auth.sign_up({
            "email": email,
            "password": password,
            "options": {
                "data": {
                    "full_name": full_name
                }
            }
        })
        return response.user, None
    except Exception as e:
        return None, str(e)

def sign_out():
    """Signs out the current user and clears session state."""
    try:
        supabase = get_supabase_client()
        supabase.auth.sign_out()
    except Exception:
        pass
    st.session_state.pop("supabase_session", None)
    st.session_state.pop("user_data", None)
    st.session_state.pop("logged_in", None)

# Alias for compatibility if any other module calls logout_user
logout_user = sign_out