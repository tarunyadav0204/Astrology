"""
Encryption utilities for PII data in birth_charts table
"""
import os
from cryptography.fernet import Fernet
import base64

class EncryptionManager:
    def __init__(self):
        key = os.getenv('ENCRYPTION_KEY')
        if not key:
            raise ValueError("ENCRYPTION_KEY environment variable is required")
        self.cipher = Fernet(key.encode() if isinstance(key, str) else key)
    
    def encrypt(self, value):
        """Encrypt a string value"""
        if value is None or value == "":
            return value
        if not isinstance(value, str):
            value = str(value)
        return self.cipher.encrypt(value.encode()).decode()
    
    def decrypt(self, value):
        """Decrypt a string value"""
        if value is None or value == "":
            return value
        try:
            return self.cipher.decrypt(value.encode()).decode()
        except:
            # If decryption fails, assume it's unencrypted data (backward compatibility)
            return value
    
    def encrypt_chart_data(self, chart_dict):
        """Encrypt PII fields in chart dictionary"""
        encrypted = chart_dict.copy()
        if 'name' in encrypted:
            encrypted['name'] = self.encrypt(encrypted['name'])
        if 'place' in encrypted:
            encrypted['place'] = self.encrypt(encrypted['place'])
        if 'date' in encrypted:
            encrypted['date'] = self.encrypt(encrypted['date'])
        if 'time' in encrypted:
            encrypted['time'] = self.encrypt(encrypted['time'])
        if 'latitude' in encrypted:
            encrypted['latitude'] = self.encrypt(str(encrypted['latitude']))
        if 'longitude' in encrypted:
            encrypted['longitude'] = self.encrypt(str(encrypted['longitude']))
        return encrypted
    
    def decrypt_chart_data(self, chart_dict):
        """Decrypt PII fields in chart dictionary"""
        decrypted = chart_dict.copy()
        if 'name' in decrypted:
            decrypted['name'] = self.decrypt(decrypted['name'])
        if 'place' in decrypted:
            decrypted['place'] = self.decrypt(decrypted['place'])
        if 'date' in decrypted:
            decrypted['date'] = self.decrypt(decrypted['date'])
        if 'time' in decrypted:
            decrypted['time'] = self.decrypt(decrypted['time'])
        if 'latitude' in decrypted:
            lat = self.decrypt(str(decrypted['latitude']))
            decrypted['latitude'] = float(lat) if lat else decrypted['latitude']
        if 'longitude' in decrypted:
            lon = self.decrypt(str(decrypted['longitude']))
            decrypted['longitude'] = float(lon) if lon else decrypted['longitude']
        return decrypted

def generate_key():
    """Generate a new encryption key (run once)"""
    return Fernet.generate_key().decode()

if __name__ == "__main__":
    print("Generated encryption key:")
    print(generate_key())
    print("\nAdd this to your .env file as:")
    print("ENCRYPTION_KEY=<key>")
