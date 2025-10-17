import sqlite3
import json

# Export nakshatras table
conn = sqlite3.connect('astrology.db')
cursor = conn.cursor()

# Export nakshatras
cursor.execute("SELECT name, lord, deity, nature, guna, description, characteristics, positive_traits, negative_traits, careers, compatibility FROM nakshatras ORDER BY id")
nakshatras = cursor.fetchall()

with open('nakshatras_data.sql', 'w') as f:
    f.write("-- Nakshatras data export\n")
    for row in nakshatras:
        values = ', '.join([f"'{str(val).replace(chr(39), chr(39)+chr(39))}'" if val is not None else 'NULL' for val in row])
        f.write(f"INSERT INTO nakshatras (name, lord, deity, nature, guna, description, characteristics, positive_traits, negative_traits, careers, compatibility) VALUES ({values});\n")

# Export planet_nakshatra_interpretations
cursor.execute("SELECT planet, nakshatra, house, interpretation FROM planet_nakshatra_interpretations ORDER BY planet, nakshatra, house")
interpretations = cursor.fetchall()

with open('planet_nakshatra_interpretations_data.sql', 'w') as f:
    f.write("-- Planet nakshatra interpretations data export\n")
    for row in interpretations:
        values = ', '.join([f"'{str(val).replace(chr(39), chr(39)+chr(39))}'" if val is not None else 'NULL' for val in row])
        f.write(f"INSERT INTO planet_nakshatra_interpretations (planet, nakshatra, house, interpretation) VALUES ({values});\n")

conn.close()
print("Data exported to nakshatras_data.sql and planet_nakshatra_interpretations_data.sql")