#!/usr/bin/env python3
"""
Idempotent encryption setup
Safe to run multiple times - only encrypts unencrypted data (Postgres birth_charts).
"""
import os

from dotenv import load_dotenv

from db import execute, get_conn


def check_encryption_needed():
    """Check if encryption setup is needed"""
    load_dotenv()
    key = os.getenv("ENCRYPTION_KEY")
    if not key:
        return True, "No encryption key found"

    try:
        with get_conn() as conn:
            cur = execute(conn, "SELECT name FROM birth_charts LIMIT 1")
            result = cur.fetchone()

        if not result:
            return False, "No data to encrypt"

        name = result[0]
        if name and ("gAAAAA" in name or len(name) > 50):
            return False, "Data appears already encrypted"

        return True, "Unencrypted data found"

    except Exception as e:
        return False, f"Database check failed: {e}"


def generate_key_if_needed():
    """Generate encryption key if not exists"""
    load_dotenv()
    if os.getenv("ENCRYPTION_KEY"):
        print("✅ Encryption key already exists")
        return True

    try:
        from encryption_utils import generate_key

        key = generate_key()

        with open(".env", "a") as f:
            f.write(f"\nENCRYPTION_KEY={key}\n")

        print("✅ Generated new encryption key")
        return True
    except Exception as e:
        print(f"❌ Failed to generate key: {e}")
        return False


def encrypt_existing_data():
    """Encrypt existing birth_charts rows if needed (Postgres)."""
    needed, reason = check_encryption_needed()

    if not needed:
        print(f"⏭️ Encryption not needed: {reason}")
        return True

    print(f"🔐 Encryption needed: {reason}")
    print("📦 Ensure you have a Postgres backup/snapshot before bulk encrypting.")

    try:
        from encryption_utils import EncryptionManager

        encryptor = EncryptionManager()

        with get_conn() as conn:
            cur = execute(
                conn,
                "SELECT id, name, date, time, latitude, longitude, place FROM birth_charts",
            )
            charts = cur.fetchall()

            encrypted_count = 0
            for chart in charts:
                chart_id, name, date, time, lat, lon, place = chart

                if name and ("gAAAAA" in name or len(name) > 50):
                    continue

                enc_name = encryptor.encrypt(name) if name else name
                enc_date = encryptor.encrypt(date) if date else date
                enc_time = encryptor.encrypt(time) if time else time
                enc_lat = encryptor.encrypt(str(lat)) if lat else lat
                enc_lon = encryptor.encrypt(str(lon)) if lon else lon
                enc_place = encryptor.encrypt(place) if place else place

                execute(
                    conn,
                    """
                    UPDATE birth_charts
                    SET name = ?, date = ?, time = ?, latitude = ?, longitude = ?, place = ?
                    WHERE id = ?
                    """,
                    (enc_name, enc_date, enc_time, enc_lat, enc_lon, enc_place, chart_id),
                )
                encrypted_count += 1

            conn.commit()

        print(f"✅ Encrypted {encrypted_count} records")
        return True

    except Exception as e:
        print(f"❌ Encryption failed: {e}")
        print("🔄 Restore from a Postgres backup if data was partially updated.")
        return False


def main():
    """Main setup function"""
    print("🔐 Setting up encryption...")

    if not generate_key_if_needed():
        return False

    if not encrypt_existing_data():
        return False

    print("✅ Encryption setup complete")
    return True


if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
