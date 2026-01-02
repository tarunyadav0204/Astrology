#!/usr/bin/env python3
"""
Script to view production birth_charts table data in unencrypted format
"""

import sqlite3
import os
from cryptography.fernet import Fernet

def load_encryption_key():
    """Load encryption key from environment or file"""
    # Try environment variable first
    key = os.getenv('ENCRYPTION_KEY')
    if key:
        # Key should be a string, return as bytes for Fernet
        return key.encode() if isinstance(key, str) else key
    
    # Try key file
    key_file = 'encryption.key'
    if os.path.exists(key_file):
        with open(key_file, 'rb') as f:
            return f.read()
    
    # Try .env file in backend directory (local and production paths)
    env_paths = ['backend/.env', '/home/tarun_yadav/AstrologyApp/backend/.env']
    for env_file in env_paths:
        if os.path.exists(env_file):
            with open(env_file, 'r') as f:
                for line in f:
                    if line.startswith('ENCRYPTION_KEY='):
                        key = line.split('=', 1)[1].strip().strip('"\'')
                        return key.encode()
    
    return None

def decrypt_data(encrypted_data, encryptor):
    """Decrypt data if encryptor is available"""
    if not encryptor or not encrypted_data:
        return encrypted_data
    
    try:
        # Fernet expects bytes input
        if isinstance(encrypted_data, str):
            data_bytes = encrypted_data.encode()
        else:
            data_bytes = encrypted_data
        
        decrypted = encryptor.decrypt(data_bytes)
        return decrypted.decode()
    except Exception as e:
        return f"[DECRYPT_FAILED: {str(e)}]"

def main():
    # Initialize encryptor
    encryptor = None
    key = load_encryption_key()
    if key:
        try:
            encryptor = Fernet(key)
            print(f"✅ Encryption key loaded (length: {len(key)} bytes)")
        except Exception as e:
            print(f"❌ Invalid encryption key: {e}")
    else:
        print("⚠️  No encryption key found - showing raw data")
        print("💡 Looking for: ENCRYPTION_KEY env var or encryption.key file")
    
    # Connect to database (check multiple paths)
    db_paths = ['backend/astrology.db', 'astrology.db', '/Users/tarunydv/Desktop/Code/AstrologyApp/backend/astrology.db']
    db_path = None
    for path in db_paths:
        if os.path.exists(path):
            db_path = path
            break
    
    if not db_path:
        print(f"❌ Database not found in any expected location")
        return
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Get all birth chart records
        cursor.execute("SELECT * FROM birth_charts")
        records = cursor.fetchall()
        
        # Get column names
        cursor.execute("PRAGMA table_info(birth_charts)")
        columns = [col[1] for col in cursor.fetchall()]
        
        print(f"\n📊 Found {len(records)} birth chart records\n")
        print("=" * 100)
        
        for i, record in enumerate(records, 1):
            print(f"\n🔍 Record {i}:")
            print("-" * 50)
            
            for j, value in enumerate(record):
                col_name = columns[j]
                
                # Decrypt sensitive fields if encryptor is available
                if encryptor and col_name in ['name', 'date', 'time', 'latitude', 'longitude', 'place'] and value:
                    # Check if value looks like Fernet encrypted data (starts with gAAAAA)
                    if isinstance(value, str) and (value.startswith('gAAAAA') or (len(value) > 20 and any(c in value for c in ['=', '+', '/']))):
                        decrypted_value = decrypt_data(value, encryptor)
                        print(f"{col_name:12}: {decrypted_value}")
                    else:
                        # Data is not encrypted, show as-is
                        print(f"{col_name:12}: {value}")
                else:
                    print(f"{col_name:12}: {value}")
        
        print("\n" + "=" * 100)
        print(f"Total records: {len(records)}")
        
    except sqlite3.Error as e:
        print(f"❌ Database error: {e}")
    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    main()