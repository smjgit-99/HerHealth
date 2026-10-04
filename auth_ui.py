import streamlit as st
import random
import string
import secrets
import time
import hashlib
import re

try:
    from modules import auth
except ImportError:
    auth = None

def hash_string(text):
    return hashlib.sha256(text.encode()).hexdigest()

def is_valid_password(password):
    """At least 8 chars, 1 uppercase, 1 number, and 1 special symbol."""
    return bool(re.match(r'^(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&])[A-Za-z\d@$!\%*?&]{8,}$', password))

def generate_captcha():
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=5))

def generate_verification_code():
    return ''.join([str(secrets.randbelow(10)) for _ in range(6)])

def render_auth_ui():
    if 'captcha_text' not in st.session_state:
        st.session_state.captcha_text = generate_captcha()
    if 'login_attempts' not in st.session_state:
        st.session_state.login_attempts = 0
        st.session_state.lockout_until = 0

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
        .captcha-box {
            background-color: #EEF4FD;
            padding: 10px;
            border-radius: 8px;
            text-align: center;
            font-size: 24px;
            font-weight: bold;
            letter-spacing: 5px;
            color: #1D1B2A;
            transform: skewX(-4deg);
            border: 1px solid #D1E3F8;
            user-select: none;
        }
        div[data-testid="stTextInput"]:has(input[aria-label="hp_hidden"]) {
            display: none !important;
        }
        </style>
    """, unsafe_allow_html=True,)

    _, col_main, _ = st.columns([1, 1.3, 1])

    with col_main:
        st.markdown('<div class="auth-container-card">', unsafe_allow_html=True)
        
        st.markdown("<h3 style='text-align: center; color: #1D1B2A; margin-bottom: 0;'>Member Authentication</h3>", unsafe_allow_html=True)
        st.markdown("<p style='text-align: center; color: #6B6880; font-size: 0.9rem;'>Sign in or create an account to participate in discussions.</p><br>", unsafe_allow_html=True)

        # --- FLOW A: EMAIL OTP VERIFICATION ---
        if st.session_state.get('show_verification', False):
            st.markdown("#### ✉️ Email Verification")
            st.info(f"Verification code sent to **{st.session_state.get('pending_email', 'your email')}**.")
            
            if 'pending_plain_otp' in st.session_state:
                st.warning(f"🔑 **[Local Demo Code]**: `{st.session_state.pending_plain_otp}` (Copy this code below)")

            otp_input = st.text_input("Enter 6-digit Code", max_chars=6, key="signup_otp_field")
            
            c_v1, c_v2 = st.columns(2)
            with c_v1:
                if st.button("Verify & Enter", type="primary", use_container_width=True):
                    if time.time() > st.session_state.get('otp_expiry', 0):
                        st.error("Code expired. Request a new one.")
                    elif hash_string(otp_input) == st.session_state.get('pending_otp_hash', ''):
                        st.session_state.logged_in = True
                        st.session_state.user_data = st.session_state.pop('pending_user_data', {})
                        st.session_state.show_verification = False
                        st.success("Verified successfully! Entering community...")
                        time.sleep(0.8)
                        st.session_state.nav_page = "Community"
                        st.rerun()
                    else:
                        st.error("Invalid verification code.")
            with c_v2:
                if st.button("Resend Code", use_container_width=True):
                    new_code = generate_verification_code()
                    st.session_state.pending_plain_otp = new_code
                    st.session_state.pending_otp_hash = hash_string(new_code)
                    st.session_state.otp_expiry = time.time() + 600
                    st.success("New code dispatched.")
                    st.rerun()

            st.markdown('</div>', unsafe_allow_html=True)
            return

        # --- FLOW B: FORGOT PASSWORD ---
        if st.session_state.get('show_forgot_flow', False):
            st.markdown("#### 🔒 Reset Password")
            forgot_email = st.text_input("Account Email", key="forgot_email_field")
            
            if st.button("Send Reset Code", type="primary", use_container_width=True):
                if not forgot_email or "@" not in forgot_email:
                    st.error("Enter a valid email.")
                else:
                    reset_code = generate_verification_code()
                    st.session_state.reset_plain_code = reset_code
                    st.session_state.reset_code_hash = hash_string(reset_code)
                    st.session_state.reset_expiry = time.time() + 600
                    st.session_state.show_reset_step = True
                    st.success("Reset code generated.")

            if st.session_state.get('show_reset_step', False):
                st.info(f"🔑 **[Local Demo Code]**: `{st.session_state.get('reset_plain_code', '')}`")
                reset_input = st.text_input("6-digit Code", max_chars=6, key="reset_code_input")
                new_pass = st.text_input("New Password (Min 8 chars, 1 uppercase, 1 number, 1 symbol)", type="password", key="reset_new_pass")
                
                if st.button("Update Password", type="primary", use_container_width=True):
                    if hash_string(reset_input) != st.session_state.get('reset_code_hash', ''):
                        st.error("Invalid code.")
                    elif not is_valid_password(new_pass):
                        st.error("Password must contain 8+ chars, 1 uppercase letter, 1 number, and 1 symbol.")
                    else:
                        st.success("Password updated! Please sign in.")
                        st.session_state.show_forgot_flow = False
                        st.session_state.show_reset_step = False
                        st.rerun()

            if st.button("← Back to Sign In", use_container_width=True):
                st.session_state.show_forgot_flow = False
                st.session_state.show_reset_step = False
                st.rerun()

            st.markdown('</div>', unsafe_allow_html=True)
            return

        # --- TABS ---
        tab_signin, tab_signup = st.tabs(["Sign In", "Create Account"])

        with tab_signin:
            st.write("")
            email_in = st.text_input("Email", key="signin_email", placeholder="you@example.com")
            pass_in = st.text_input("Password", type="password", key="signin_password", placeholder="••••••••")
            
            c_f_space, c_f_btn = st.columns([1.5, 1])
            with c_f_btn:
                if st.button("Forgot Password?", key="trigger_forgot", type="tertiary"):
                    st.session_state.show_forgot_flow = True
                    st.rerun()

            st.write("")
            if st.button("Sign In", type="primary", use_container_width=True, key="btn_signin_action"):
                success = False
                user_row = None
                if auth and hasattr(auth, 'login'):
                    user_row, err = auth.login(email_in, pass_in)
                    if user_row: success = True
                elif email_in == "demo@herhealth.com" and pass_in == "Password@123":
                    success = True
                    user_row = {"name": "Demo User", "email": email_in}

                if success:
                    st.session_state.logged_in = True
                    st.session_state.user_data = user_row
                    st.session_state.nav_page = "Community"
                    st.rerun()
                else:
                    st.error("Invalid email or password.")

            st.markdown("<div style='text-align: center; margin: 10px 0; color: #6B6880; font-size: 0.85rem;'>OR</div>", unsafe_allow_html=True)
            if st.button("Continue with Google", use_container_width=True, icon=":material/login:"):
                st.session_state.logged_in = True
                st.session_state.user_data = {"name": "Google User", "email": "google_user@gmail.com"}
                st.session_state.nav_page = "Community"
                st.rerun()

        with tab_signup:
            st.write("")
            name_up = st.text_input("Full Name", key="signup_fullname", placeholder="Jane Doe")
            email_up = st.text_input("Email Address", key="signup_email", placeholder="you@example.com")
            pass_up = st.text_input("Password", type="password", key="signup_pass", placeholder="••••••••")
            st.caption("Must have 8+ chars, 1 uppercase letter, 1 number, and 1 symbol (@$!%*?&).")
            pass_conf = st.text_input("Confirm Password", type="password", key="signup_pass_confirm", placeholder="••••••••")
            
            hp_val = st.text_input("hp_hidden", key="honeypot_field", label_visibility="collapsed")

            st.write("")
            st.markdown("**Security Check**")
            c_cap1, c_cap2 = st.columns([1, 2], vertical_alignment="bottom")
            with c_cap1:
                st.markdown(f'<div class="captcha-box">{st.session_state.captcha_text}</div>', unsafe_allow_html=True)
                if st.button("🔄 Refresh", key="refresh_captcha_su", use_container_width=True):
                    st.session_state.captcha_text = generate_captcha()
                    st.rerun()
            with c_cap2:
                captcha_in = st.text_input("Enter code above", key="captcha_input_su", placeholder="Code")

            st.write("")
            if st.button("Create Account", type="primary", use_container_width=True, key="btn_signup_action"):
                if hp_val != "":
                    st.error("Bot blocked.")
                elif captcha_in.upper() != st.session_state.captcha_text:
                    st.error("Incorrect security code.")
                    st.session_state.captcha_text = generate_captcha()
                    st.rerun()
                elif not name_up.strip():
                    st.error("Please enter your full name.")
                elif not email_up.strip() or "@" not in email_up:
                    st.error("Please enter a valid email.")
                elif not is_valid_password(pass_up):
                    st.error("Password must contain at least 8 characters, one uppercase letter, one number, and one symbol.")
                elif pass_up != pass_conf:
                    st.error("Passwords do not match.")
                else:
                    plain_otp = generate_verification_code()
                    st.session_state.pending_plain_otp = plain_otp
                    st.session_state.pending_otp_hash = hash_string(plain_otp)
                    st.session_state.otp_expiry = time.time() + 600
                    st.session_state.pending_email = email_up
                    st.session_state.pending_user_data = {
                        "name": name_up,
                        "email": email_up,
                        "pass_hash": hash_string(pass_up)
                    }
                    st.session_state.show_verification = True
                    st.success("Account registered! Please enter your verification code below.")
                    st.rerun()

        st.markdown('</div>', unsafe_allow_html=True)