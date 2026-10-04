import sqlite3
import hashlib
import secrets
from datetime import datetime, timedelta

DB_NAME = "herhealth.db"

def init_db():
    """Initializes the SQLite database and creates necessary tables."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    # Users table with security and lockout fields
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            is_verified INTEGER DEFAULT 0,
            verification_code_hash TEXT,
            code_expiry TEXT,
            failed_attempts INTEGER DEFAULT 0,
            lockout_until TEXT
        )
    """)
    
    # Reports table (stores only lab summaries and values—never raw document text)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS reports (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT NOT NULL,
            summary_text TEXT NOT NULL,
            timestamp TEXT NOT NULL,
            FOREIGN KEY (email) REFERENCES users (email)
        )
    """)
    
    conn.commit()
    conn.close()

def hash_data(data: str) -> str:
    """Securely hashes strings (passwords or verification codes) using SHA-256."""
    return hashlib.sha256(data.encode('utf-8')).hexdigest()

def register_user(email, password):
    """Registers a new user and generates a 6-digit verification code."""
    init_db()
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    # Check if user already exists
    cursor.execute("SELECT email FROM users WHERE email = ?", (email,))
    if cursor.fetchone():
        conn.close()
        return False, "Email is already registered."
    
    password_hash = hash_data(password)
    verification_code = ''.join([str(secrets.randbelow(10)) for _ in range(6)])
    code_hash = hash_data(verification_code)
    code_expiry = (datetime.now() + timedelta(minutes=10)).isoformat()
    
    try:
        cursor.execute("""
            INSERT INTO users (email, password_hash, verification_code_hash, code_expiry, is_verified)
            VALUES (?, ?, ?, ?, 0)
        """, (email, password_hash, code_hash, code_expiry))
        conn.commit()
        conn.close()
        # In production, you'd send 'verification_code' via email. 
        # For testing, we can return it or print it.
        return True, verification_code
    except Exception as e:
        conn.close()
        return False, str(e)

def verify_code(email, code):
    """Verifies the 6-digit code entered by the user."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    cursor.execute("SELECT verification_code_hash, code_expiry, is_verified FROM users WHERE email = ?", (email,))
    row = cursor.fetchone()
    if not row:
        conn.close()
        return False, "User not found."
        
    stored_hash, expiry_str, is_verified = row
    if is_verified:
        conn.close()
        return True, "Account already verified."
        
    if datetime.now() > datetime.fromisoformat(expiry_str):
        conn.close()
        return False, "Verification code has expired."
        
    if hash_data(code) == stored_hash:
        cursor.execute("UPDATE users SET is_verified = 1, verification_code_hash = NULL WHERE email = ?", (email,))
        conn.commit()
        conn.close()
        return True, "Account verified successfully!"
    else:
        conn.close()
        return False, "Invalid verification code."

def authenticate_user(email, password):
    """Authenticates a user with rate-limiting and lockout protection (5 attempts)."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT password_hash, is_verified, failed_attempts, lockout_until 
        FROM users WHERE email = ?
    """, (email,))
    row = cursor.fetchone()
    
    if not row:
        conn.close()
        return False, "Invalid email or password."
        
    password_hash, is_verified, failed_attempts, lockout_until = row
    
    # Check lockout
    if lockout_until and datetime.now() < datetime.fromisoformat(lockout_until):
        conn.close()
        remaining = int((datetime.fromisoformat(lockout_until) - datetime.now()).total_seconds() / 60)
        return False, f"Account locked due to multiple failed attempts. Try again in {remaining} minutes."
        
    if not is_verified:
        conn.close()
        return False, "Please verify your email before logging in."
        
    if hash_data(password) == password_hash:
        # Reset failed attempts on successful login
        cursor.execute("UPDATE users SET failed_attempts = 0, lockout_until = NULL WHERE email = ?", (email,))
        conn.commit()
        conn.close()
        return True, "Login successful."
    else:
        failed_attempts += 1
        new_lockout = None
        if failed_attempts >= 5:
            new_lockout = (datetime.now() + timedelta(minutes=15)).isoformat()
            
        cursor.execute("""
            UPDATE users SET failed_attempts = ?, lockout_until = ? WHERE email = ?
        """, (failed_attempts, new_lockout, email))
        conn.commit()
        conn.close()
        
        if failed_attempts >= 5:
            return False, "Too many failed attempts. Account locked for 15 minutes."
        return False, f"Invalid email or password. Attempt {failed_attempts} of 5."

def save_user_report(email, summary_text):
    """Saves a translated lab report summary to the database."""
    init_db()
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    cursor.execute("""
        INSERT INTO reports (email, summary_text, timestamp)
        VALUES (?, ?, ?)
    """, (email, summary_text, timestamp))
    conn.commit()
    conn.close()

def get_user_reports(email):
    """Retrieves saved reports for a user."""
    init_db()
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT summary_text, timestamp FROM reports WHERE email = ? ORDER BY id DESC", (email,))
    reports = cursor.fetchall()
    conn.close()
    return reports