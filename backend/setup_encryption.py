#!/usr/bin/env python3
"""
Idempotent encryption setup script
Safe to run multiple times - only encrypts unencrypted data
"""
import os
import sqlite3
from dotenv import load_dotenv

def check_encryption_needed():
    """Check if encryption setup is needed"""
    # Check if encryption key exists
    load_dotenv()
    key = os.getenv('ENCRYPTION_KEY')
    if not key:
        return True, "No encryption key found"
    
    # Check if data is already encrypted
    try:
        conn = sqlite3.connect('astrology.db')
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM birth_charts LIMIT 1")
        result = cursor.fetchone()
        conn.close()
        
        if not result:
            return False, "No data to encrypt"
        
        # Try to detect if data is encrypted (encrypted data contains special chars)
        name = result[0]
        if name and ('gAAAAA' in name or len(name) > 50):
            return False, "Data appears already encrypted"
        
        return True, "Unencrypted data found"
        
    except Exception as e:
        return False, f"Database check failed: {e}"

def generate_key_if_needed():
    """Generate encryption key if not exists"""
    load_dotenv()
    if os.getenv('ENCRYPTION_KEY'):
        print("✅ Encryption key already exists")
        return True
    
    try:
        from encryption_utils import generate_key
        key = generate_key()
        
        # Add to .env file
        with open('.env', 'a') as f:
            f.write(f"\nENCRYPTION_KEY={key}\n")
        
        print("✅ Generated new encryption key")
        return True
    except Exception as e:
        print(f"❌ Failed to generate key: {e}")
        return False

def encrypt_existing_data():
    """Encrypt existing data if needed"""
    needed, reason = check_encryption_needed()
    
    if not needed:
        print(f"⏭️ Encryption not needed: {reason}")
        return True
    
    print(f"🔐 Encryption needed: {reason}")
    
    try:
        from encryption_utils import EncryptionManager
        
        # Create backup
        print("📦 Creating backup...")
        os.system('cp astrology.db astrology.db.backup')
        
        encryptor = EncryptionManager()
        conn = sqlite3.connect('astrology.db')
        cursor = conn.cursor()
        
        # Get unencrypted records
        cursor.execute("SELECT id, name, date, time, latitude, longitude, place FROM birth_charts")
        charts = cursor.fetchall()
        
        encrypted_count = 0
        for chart in charts:
            chart_id, name, date, time, lat, lon, place = chart
            
            # Skip if already encrypted
            if name and ('gAAAAA' in name or len(name) > 50):
                continue
            
            # Encrypt fields
            enc_name = encryptor.encrypt(name) if name else name
            enc_date = encryptor.encrypt(date) if date else date
            enc_time = encryptor.encrypt(time) if time else time
            enc_lat = encryptor.encrypt(str(lat)) if lat else lat
            enc_lon = encryptor.encrypt(str(lon)) if lon else lon
            enc_place = encryptor.encrypt(place) if place else place
            
            # Update record
            cursor.execute("""
                UPDATE birth_charts 
                SET name=?, date=?, time=?, latitude=?, longitude=?, place=?
                WHERE id=?
            """, (enc_name, enc_date, enc_time, enc_lat, enc_lon, enc_place, chart_id))
            
            encrypted_count += 1
        
        conn.commit()
        conn.close()
        
        print(f"✅ Encrypted {encrypted_count} records")
        return True
        
    except Exception as e:
        print(f"❌ Encryption failed: {e}")
        # Restore backup on failure
        if os.path.exists('astrology.db.backup'):
            os.system('cp astrology.db.backup astrology.db')
            print("🔄 Restored from backup")
        return False

def main():
    """Main setup function"""
    print("🔐 Setting up encryption...")
    
    # Step 1: Generate key if needed
    if not generate_key_if_needed():
        return False
    
    # Step 2: Encrypt existing data if needed
    if not encrypt_existing_data():
        return False
    
    print("✅ Encryption setup complete")
    return True

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)