import streamlit as st
from supabase import create_client

# Test reading from secrets
url = "https://pfkzudqzbcxfzzjgqgo.supabase.co"
key = "sb_publishable_4XmNj7iwPHPdgx4lBGADuQ_W2oww..."

print("Initializing Supabase client...")
supabase = create_client(url, key)
print("Success! Connected to Supabase.")
