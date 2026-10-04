"""Email + password accounts: salted PBKDF2 hashes, lockout, email verification OTP, password reset."""
import hashlib
import hmac
import os
import re
import secrets
import time 
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

from modules import db

ITERATIONS = 200_000
MAX_FAILS = 5
LOCK_SECONDS = 15 * 60
MAX_DOC_BYTES = 5 * 1024 * 1024
EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
PASSWORD_RE = re.compile(r'^(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&])[A-Za-z\d@$!%*?&]{8,}$')

BAD_LOGIN = "Wrong email or password."


def _hash(password: str, salt: bytes) -> bytes:
    return hashlib.pbkdf2_hmac("sha256", password.encode(), salt, ITERATIONS)


def _admin_email() -> str:
    return os.getenv("ADMIN_EMAIL", "").strip().lower()


def send_real_email_otp(recipient_email: str, otp_code: str) -> bool:
    """Sends a real 6-digit OTP email using Gmail SMTP with diagnostic logging."""
    sender_email = os.getenv("SMTP_EMAIL", "").strip()
    sender_password = os.getenv("SMTP_PASSWORD", "").strip()
    
    print(f"DEBUG: Attempting SMTP dispatch. Sender: '{sender_email}', Recipient: '{recipient_email}'")
    
    if not sender_email or not sender_password:
        print("SMTP Error: Missing SMTP_EMAIL or SMTP_PASSWORD environment variables.")
        return False
        
    message = MIMEMultipart()
    message["From"] = f"HerHealth Community <{sender_email}>"
    message["To"] = recipient_email
    message["Subject"] = "Your HerHealth Verification Code"
    
    body = f"""
    Hello,
    
    Your verification code for HerHealth is: {otp_code}
    
    This code will expire in 10 minutes. If you did not request this, please ignore this email.
    
    Best regards,
    HerHealth Team
    """
    message.attach(MIMEText(body, "plain"))
    
    try:
        print("DEBUG: Connecting to smtp.gmail.com:587...")
        server = smtplib.SMTP("smtp.gmail.com", 587, timeout=10)
        server.set_debuglevel(1)  # Prints all SMTP server conversation to your terminal
        server.starttls()
        print("DEBUG: Authenticating with Gmail...")
        server.login(sender_email, sender_password)
        print("DEBUG: Sending mail...")
        server.sendmail(sender_email, recipient_email, message.as_string())
        server.quit()
        print("DEBUG: Email sent successfully!")
        return True
    except Exception as e:
        print(f"❌ SMTP Detailed Exception Error: {type(e).__name__}: {e}")
        return False


def register(email: str, name: str, password: str):
    """Returns (user_row, None) or (None, error message). Requires email OTP verification."""
    email, name = email.strip().lower(), name.strip()
    if not EMAIL_RE.match(email):
        return None, "Enter a valid email address."
    if not name:
        return None, "Please enter your full name."
    if not PASSWORD_RE.match(password):
        return None, "Password must be at least 8 characters and include at least one uppercase letter, one number, and one special symbol (@$!%*?&)."
    
    existing = db.one("SELECT * FROM users WHERE email=?", (email,))
    if existing and existing.get("status") == "verified":
        return None, "That email already has an active account. Try signing in."
    
    salt = secrets.token_bytes(16)
    pw_hash = _hash(password, salt)
    role = "admin" if email == _admin_email() else "member"
    
    otp = ''.join([str(secrets.randbelow(10)) for _ in range(6)])
    otp_hash = hashlib.sha256(otp.encode()).hexdigest()
    otp_expiry = time.time() + 600  # 10 minutes
    
    if existing:
        db.run("UPDATE users SET alias=?, salt=?, pw_hash=?, role=?, otp_hash=?, otp_expiry=? WHERE email=?",
               (name, salt, pw_hash, role, otp_hash, otp_expiry, email))
        uid = existing["id"]
    else:
        uid = db.run("INSERT INTO users(email, alias, salt, pw_hash, role, created, otp_hash, otp_expiry, status) VALUES(?,?,?,?,?,?,?,?,?)",
                     (email, name, salt, pw_hash, role, time.time(), otp_hash, otp_expiry, "unverified"))
    
    email_sent = send_real_email_otp(email, otp)
    user_row = db.one("SELECT * FROM users WHERE id=?", (uid,))
    return {"user": user_row, "plain_otp": otp, "email_sent": email_sent}, None


def verify_otp(email: str, otp: str):
    email = email.strip().lower()
    u = db.one("SELECT * FROM users WHERE email=?", (email,))
    if not u:
        return None, "Account not found."
    if u.get("status") == "verified":
        return u, None
    if time.time() > u.get("otp_expiry", 0):
        return None, "Verification code has expired. Please request a new one."
    
    input_hash = hashlib.sha256(otp.strip().encode()).hexdigest()
    if hmac.compare_digest(input_hash, u.get("otp_hash", "")):
        db.run("UPDATE users SET status='verified', otp_hash=NULL, otp_expiry=NULL WHERE id=?", (u["id"],))
        return db.one("SELECT * FROM users WHERE id=?", (u["id"],)), None
    return None, "Invalid verification code."


def resend_otp(email: str):
    email = email.strip().lower()
    u = db.one("SELECT * FROM users WHERE email=?", (email,))
    if not u:
        return None, "Account not found."
    
    otp = ''.join([str(secrets.randbelow(10)) for _ in range(6)])
    otp_hash = hashlib.sha256(otp.encode()).hexdigest()
    otp_expiry = time.time() + 600
    
    db.run("UPDATE users SET otp_hash=?, otp_expiry=? WHERE id=?", (otp_hash, otp_expiry, u["id"]))
    email_sent = send_real_email_otp(email, otp)
    return {"plain_otp": otp, "email_sent": email_sent}, None


def request_password_reset(email: str):
    email = email.strip().lower()
    u = db.one("SELECT * FROM users WHERE email=?", (email,))
    if not u:
        return {"plain_otp": "000000", "email_sent": False}, None
    
    otp = ''.join([str(secrets.randbelow(10)) for _ in range(6)])
    otp_hash = hashlib.sha256(otp.encode()).hexdigest()
    otp_expiry = time.time() + 600
    
    db.run("UPDATE users SET otp_hash=?, otp_expiry=? WHERE id=?", (otp_hash, otp_expiry, u["id"]))
    email_sent = send_real_email_otp(email, otp)
    return {"plain_otp": otp, "email_sent": email_sent}, None


def reset_password_with_otp(email: str, otp: str, new_password: str):
    email = email.strip().lower()
    if not PASSWORD_RE.match(new_password):
        return None, "Password must be at least 8 characters and include at least one uppercase letter, one number, and one special symbol (@$!%*?&)."
    
    u = db.one("SELECT * FROM users WHERE email=?", (email,))
    if not u:
        return None, "Invalid request."
    if time.time() > u.get("otp_expiry", 0):
        return None, "Reset code has expired."
    
    input_hash = hashlib.sha256(otp.strip().encode()).hexdigest()
    if not hmac.compare_digest(input_hash, u.get("otp_hash", "")):
        return None, "Invalid reset code."
    
    salt = secrets.token_bytes(16)
    pw_hash = _hash(new_password, salt)
    db.run("UPDATE users SET salt=?, pw_hash=?, otp_hash=NULL, otp_expiry=NULL WHERE id=?", (salt, pw_hash, u["id"]))
    return db.one("SELECT * FROM users WHERE id=?", (u["id"],)), None


def login(email: str, password: str):
    """Returns (user_row, None) or (None, error message). Requires verified status."""
    u = db.one("SELECT * FROM users WHERE email=?", (email.strip().lower(),))
    
    # Use 'if not u:' to safely catch None, empty tuples, or empty results
    if not u:
        _hash(password, b"0" * 16)
        return None, BAD_LOGIN
        
    # Safely get status whether 'u' is a dictionary, row, or object
    status = "verified"
    if hasattr(u, "get"):
        status = u.get("status", "verified")
    elif isinstance(u, (tuple, list)) and len(u) > 4: # Adjust index if using raw tuples
        pass  # or handle tuple index if needed, but dict/Row is preferred

    if status == "unverified":
        return None, "Please verify your email address before signing in."
        
    if u["locked_until"] > time.time():
        mins = int((u["locked_until"] - time.time()) // 60) + 1
        return None, f"Too many wrong attempts. Try again in about {mins} minutes."
        
    if hmac.compare_digest(_hash(password, u["salt"]), u["pw_hash"]):
        db.run("UPDATE users SET failed=0, locked_until=0 WHERE id=?", (u["id"],))
        if u["email"] == _admin_email() and u["role"] != "admin":
            db.run("UPDATE users SET role='admin' WHERE id=?", (u["id"],))
        return db.one("SELECT * FROM users WHERE id=?", (u["id"],)), None
        
    fails = u["failed"] + 1
    if fails >= MAX_FAILS:
        db.run("UPDATE users SET failed=0, locked_until=? WHERE id=?", (time.time() + LOCK_SECONDS, u["id"]))
        return None, "Too many wrong attempts. This account is locked for 15 minutes."
        
    db.run("UPDATE users SET failed=? WHERE id=?", (fails, u["id"]))
    return None, BAD_LOGIN


def get_user(user_id):
    return db.one("SELECT * FROM users WHERE id=?", (user_id,)) if user_id else None


def submit_verification(user_id: int, tag: str, filename: str, data: bytes):
    if len(data) > MAX_DOC_BYTES:
        return "File is too large (max 5 MB)."
    if not filename.lower().endswith((".pdf", ".png", ".jpg", ".jpeg")):
        return "Upload a PDF, PNG or JPG."
    db.run("UPDATE users SET status='pending', tag=?, doc_name=?, doc_blob=? WHERE id=?", (tag, filename, data, user_id))
    return None


def pending_verifications() -> list:
    return db.q("SELECT id, alias, tag, doc_name, doc_blob FROM users WHERE status='pending' ORDER BY created")


def decide_verification(user_id: int, approve: bool):
    db.run("UPDATE users SET status=?, doc_blob=NULL WHERE id=?", ("verified" if approve else "rejected", user_id))