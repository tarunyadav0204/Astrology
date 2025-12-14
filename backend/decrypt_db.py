#!/usr/bin/env python3
import sqlite3
import os
from dotenv import load_dotenv
from encryption_utils import EncryptionManager

# Load environment variables from .env file
load_dotenv()

# Initialize encryption manager
enc = EncryptionManager()

# Connect to database
conn = sqlite3.connect('astrology.db')
cursor = conn.cursor()

# Get recent birth chart entries
cursor.execute("SELECT id, name, date, time, place FROM birth_charts ORDER BY id DESC LIMIT 10")
rows = cursor.fetchall()

print("Recent Birth Chart Entries (Decrypted):")
print("=" * 80)

for row in rows:
    id_val, name_enc, date_enc, time_enc, place_enc = row
    
    # Decrypt each field
    name = enc.decrypt(name_enc) if name_enc else "N/A"
    date = enc.decrypt(date_enc) if date_enc else "N/A"
    time = enc.decrypt(time_enc) if time_enc else "N/A"
    place = enc.decrypt(place_enc) if place_enc else "N/A"
    
    print(f"ID: {id_val}")
    print(f"Name: {name}")
    print(f"Date: {date}")
    print(f"Time: {time}")
    print(f"Place: {place}")
    print("-" * 40)

conn.close()