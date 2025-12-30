#!/usr/bin/env python3
"""
Decrypt and compare birth chart entries to find differences
"""
import sqlite3
import os
from dotenv import load_dotenv
from encryption_utils import EncryptionManager

# Load environment variables
load_dotenv()

def decrypt_birth_charts():
    try:
        encryptor = EncryptionManager()
        conn = sqlite3.connect('astrology.db')
        cursor = conn.cursor()
        
        # Get entries for Tarun Yadav and latest entries
        cursor.execute("""
            SELECT id, userid, name, date, time, latitude, longitude, timezone, created_at, place, gender, relation, is_rectified, calibration_year
            FROM birth_charts 
            WHERE id IN (10209, 10225)
            ORDER BY created_at DESC
        """)
        
        entries = cursor.fetchall()
        
        print("=== DECRYPTED BIRTH CHART COMPARISON ===\n")
        
        tarun_entry = None
        latest_entry = None
        
        for entry in entries:
            id_val, userid, name, date, time, lat, lon, timezone, created_at, place, gender, relation, is_rectified, calibration_year = entry
            
            decrypted_name = encryptor.decrypt(name) if name else 'N/A'
            
            entry_data = {
                'id': id_val,
                'userid': userid,
                'name': decrypted_name,
                'date': encryptor.decrypt(date),
                'time': encryptor.decrypt(time),
                'latitude': encryptor.decrypt(lat),
                'longitude': encryptor.decrypt(lon),
                'timezone': timezone,
                'created_at': created_at,
                'place': encryptor.decrypt(place) if place else 'N/A',
                'gender': gender,
                'relation': relation,
                'is_rectified': is_rectified,
                'calibration_year': calibration_year
            }
            
            if 'Tarun' in decrypted_name:
                tarun_entry = entry_data
            else:
                latest_entry = entry_data
        
        if tarun_entry:
            print("TARUN YADAV (OLD - CORRECT DASHAS):")
            for key, value in tarun_entry.items():
                print(f"  {key}: {value}")
            print()
        
        if latest_entry:
            print("LATEST ENTRY (NEW - WRONG DASHAS):")
            for key, value in latest_entry.items():
                print(f"  {key}: {value}")
            print()
        
        if tarun_entry and latest_entry:
            print("=== DIFFERENCES ===\n")
            for key in tarun_entry.keys():
                if tarun_entry[key] != latest_entry[key]:
                    print(f"  {key}:")
                    print(f"    Tarun: {tarun_entry[key]}")
                    print(f"    Latest: {latest_entry[key]}")
                    print()
        
        conn.close()
        
    except Exception as e:
        print(f"Error decrypting charts: {e}")
        import traceback
        print(traceback.format_exc())

if __name__ == "__main__":
    decrypt_birth_charts()