import streamlit as st
import re
from modules import auth

def is_valid_password(password):
    """At least 8 chars, 1 uppercase, 1 number, and 1 special symbol."""
    return bool(re.match(r'^(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&])[A-Za-z\d@$!%*?&]{8,}$', password))

def render_auth_ui():
    st.markdown("""
        <style>
        .auth-container-card {
            background-color: #ffffff;
            padding: 2rem;
            border-radius: 16px;
            box-shadow: 0 10px 30px rgba(155, 114, 203, 0.1);
            border: 1px solid #EFEAF8;
            margin-bottom: 2rem;
        }
        </style>
    """, unsafe_allow_html=True)

    _, col_main, _ = st.columns([1, 1.3, 1])

    with col_main:
        st.markdown('<div class="auth-container-card">', unsafe_allow_html=True)
        st.markdown("<h3 style='text-align: center; color: #1D1B2A; margin-bottom: 0;'>Member Authentication</h3>", unsafe_allow_html=True)
        st.markdown("<p style='text-align: center; color: #6B6880; font-size: 0.9rem;'>Sign in or create an account to participate in discussions.</p><br>", unsafe_allow_html=True)

        tab_signin, tab_signup = st.tabs(["Sign In", "Create Account"])

        with tab_signin:
            st.write("")
            email_in = st.text_input("Email", key="signin_email", placeholder="you@example.com")
            pass_in = st.text_input("Password", type="password", key="signin_password", placeholder="••••••••")
            
            st.write("")
            if st.button("Sign In", type="primary", use_container_width=True, key="btn_signin_action"):
                if not email_in or not pass_in:
                    st.error("Please fill in all fields.")
                else:
                    user, err = auth.login_user(email_in, pass_in)
                    if user:
                        st.session_state.logged_in = True
                        st.session_state.user_data = user
                        st.session_state.nav_page = "Community"
                        st.success("Signed in successfully!")
                        st.rerun()
                    else:
                        st.error(f"Sign in failed: {err}")

        with tab_signup:
            st.write("")
            name_up = st.text_input("Full Name", key="signup_fullname", placeholder="Jane Doe")
            email_up = st.text_input("Email Address", key="signup_email", placeholder="you@example.com")
            pass_up = st.text_input("Password", type="password", key="signup_pass", placeholder="••••••••")
            st.caption("Must have 8+ chars, 1 uppercase letter, 1 number, and 1 symbol (@$!%*?&).")
            pass_conf = st.text_input("Confirm Password", type="password", key="signup_pass_confirm", placeholder="••••••••")

            st.write("")
            if st.button("Create Account", type="primary", use_container_width=True, key="btn_signup_action"):
                if not name_up.strip():
                    st.error("Please enter your full name.")
                elif not email_up or "@" not in email_up:
                    st.error("Please enter a valid email address.")
                elif not is_valid_password(pass_up):
                    st.error("Password must contain at least 8 characters, one uppercase letter, one number, and one symbol.")
                elif pass_up != pass_conf:
                    st.error("Passwords do not match.")
                else:
                    user, err = auth.register_user(email_up, pass_up, name_up)
                    if user:
                        st.success("Account created successfully! You can now switch to the 'Sign In' tab.")
                    else:
                        st.error(f"Registration error: {err}")

        st.markdown('</div>', unsafe_allow_html=True)