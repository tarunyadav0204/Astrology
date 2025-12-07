"""
Migration script to encrypt existing birth_charts data
Run once to encrypt all existing records
"""
import sqlite3
import os
from dotenv import load_dotenv
from encryption_utils import EncryptionManager

load_dotenv()

def migrate_encrypt_birth_charts():
    """Encrypt all existing birth_charts records"""
    
    # Backup database first
    print("Creating backup...")
    os.system('cp astrology.db astrology.db.backup')
    print("Backup created: astrology.db.backup")
    
    # Initialize encryption
    try:
        encryptor = EncryptionManager()
    except ValueError as e:
        print(f"Error: {e}")
        print("Please set ENCRYPTION_KEY environment variable first")
        print("Run: python encryption_utils.py to generate a key")
        return
    
    conn = sqlite3.connect('astrology.db')
    cursor = conn.cursor()
    
    # Get all birth charts
    cursor.execute("SELECT id, name, date, time, latitude, longitude, place FROM birth_charts")
    charts = cursor.fetchall()
    
    print(f"Found {len(charts)} charts to encrypt")
    
    encrypted_count = 0
    for chart in charts:
        chart_id, name, date, time, lat, lon, place = chart
        
        # Encrypt fields
        enc_name = encryptor.encrypt(name)
        enc_date = encryptor.encrypt(date)
        enc_time = encryptor.encrypt(time)
        enc_lat = encryptor.encrypt(str(lat))
        enc_lon = encryptor.encrypt(str(lon))
        enc_place = encryptor.encrypt(place) if place else place
        
        # Update record
        cursor.execute("""
            UPDATE birth_charts 
            SET name=?, date=?, time=?, latitude=?, longitude=?, place=?
            WHERE id=?
        """, (enc_name, enc_date, enc_time, enc_lat, enc_lon, enc_place, chart_id))
        
        encrypted_count += 1
        if encrypted_count % 10 == 0:
            print(f"Encrypted {encrypted_count}/{len(charts)} charts...")
    
    conn.commit()
    conn.close()
    
    print(f"\nMigration complete! Encrypted {encrypted_count} charts")
    print("Backup saved as: astrology.db.backup")

if __name__ == "__main__":
    print("=== Birth Charts Encryption Migration ===")
    print("This will encrypt all PII data in birth_charts table")
    response = input("Continue? (yes/no): ")
    
    if response.lower() == 'yes':
        migrate_encrypt_birth_charts()
    else:
        print("Migration cancelled")
