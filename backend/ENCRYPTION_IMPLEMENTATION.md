# Encryption Implementation Guide

## Files Created
1. `encryption_utils.py` - Encryption manager with Fernet
2. `migrate_encrypt_data.py` - Migration script for existing data

## Changes Required in main.py

### 1. Add import at top (after other imports):
```python
from encryption_utils import EncryptionManager

# Initialize encryption manager
try:
    encryptor = EncryptionManager()
except ValueError as e:
    print(f"WARNING: Encryption not configured: {e}")
    encryptor = None
```

### 2. Modify these functions to encrypt BEFORE database INSERT/UPDATE:

**Line ~800 - register_with_birth function:**
```python
# BEFORE:
cursor.execute('''
    INSERT INTO birth_charts (userid, name, date, time, latitude, longitude, timezone, place, gender, relation)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 'self')
''', (user[0], birth_data.name, birth_data.date, birth_data.time, 
      birth_data.latitude, birth_data.longitude, birth_data.timezone, 
      birth_data.place or '', birth_data.gender or ''))

# AFTER:
if encryptor:
    enc_name = encryptor.encrypt(birth_data.name)
    enc_date = encryptor.encrypt(birth_data.date)
    enc_time = encryptor.encrypt(birth_data.time)
    enc_lat = encryptor.encrypt(str(birth_data.latitude))
    enc_lon = encryptor.encrypt(str(birth_data.longitude))
    enc_place = encryptor.encrypt(birth_data.place or '')
else:
    enc_name, enc_date, enc_time = birth_data.name, birth_data.date, birth_data.time
    enc_lat, enc_lon, enc_place = str(birth_data.latitude), str(birth_data.longitude), birth_data.place or ''

cursor.execute('''
    INSERT INTO birth_charts (userid, name, date, time, latitude, longitude, timezone, place, gender, relation)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 'self')
''', (user[0], enc_name, enc_date, enc_time, enc_lat, enc_lon, 
      birth_data.timezone, enc_place, birth_data.gender or '', 'self'))
```

**Line ~1100 - calculate_chart function:**
```python
# BEFORE:
cursor.execute('''
    INSERT OR REPLACE INTO birth_charts (userid, name, date, time, latitude, longitude, timezone, place, gender, relation)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
''', (current_user.userid, birth_data.name, birth_data.date, birth_data.time, 
      birth_data.latitude, birth_data.longitude, birth_data.timezone, birth_data.place, birth_data.gender, birth_data.relation or 'other'))

# AFTER:
if encryptor:
    enc_name = encryptor.encrypt(birth_data.name)
    enc_date = encryptor.encrypt(birth_data.date)
    enc_time = encryptor.encrypt(birth_data.time)
    enc_lat = encryptor.encrypt(str(birth_data.latitude))
    enc_lon = encryptor.encrypt(str(birth_data.longitude))
    enc_place = encryptor.encrypt(birth_data.place)
else:
    enc_name, enc_date, enc_time = birth_data.name, birth_data.date, birth_data.time
    enc_lat, enc_lon, enc_place = str(birth_data.latitude), str(birth_data.longitude), birth_data.place

cursor.execute('''
    INSERT OR REPLACE INTO birth_charts (userid, name, date, time, latitude, longitude, timezone, place, gender, relation)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
''', (current_user.userid, enc_name, enc_date, enc_time, enc_lat, enc_lon, 
      birth_data.timezone, enc_place, birth_data.gender, birth_data.relation or 'other'))
```

**Line ~950 - update_self_birth_chart function:**
```python
# BEFORE:
cursor.execute('''
    INSERT INTO birth_charts (userid, name, date, time, latitude, longitude, timezone, place, gender, relation)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 'self')
''', (current_user.userid, birth_data.name, birth_data.date, birth_data.time, 
      birth_data.latitude, birth_data.longitude, birth_data.timezone, 
      birth_data.place or '', birth_data.gender or ''))

# AFTER:
if encryptor:
    enc_name = encryptor.encrypt(birth_data.name)
    enc_date = encryptor.encrypt(birth_data.date)
    enc_time = encryptor.encrypt(birth_data.time)
    enc_lat = encryptor.encrypt(str(birth_data.latitude))
    enc_lon = encryptor.encrypt(str(birth_data.longitude))
    enc_place = encryptor.encrypt(birth_data.place or '')
else:
    enc_name, enc_date, enc_time = birth_data.name, birth_data.date, birth_data.time
    enc_lat, enc_lon, enc_place = str(birth_data.latitude), str(birth_data.longitude), birth_data.place or ''

cursor.execute('''
    INSERT INTO birth_charts (userid, name, date, time, latitude, longitude, timezone, place, gender, relation)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 'self')
''', (current_user.userid, enc_name, enc_date, enc_time, enc_lat, enc_lon, 
      birth_data.timezone, enc_place, birth_data.gender or '', 'self'))
```

**Line ~1350 - update_birth_chart function:**
```python
# BEFORE:
cursor.execute('''
    UPDATE birth_charts 
    SET name=?, date=?, time=?, latitude=?, longitude=?, timezone=?, place=?, gender=?, relation=?
    WHERE id=?
''', (birth_data.name, birth_data.date, birth_data.time, 
      birth_data.latitude, birth_data.longitude, birth_data.timezone, birth_data.place, birth_data.gender, birth_data.relation or 'other', chart_id))

# AFTER:
if encryptor:
    enc_name = encryptor.encrypt(birth_data.name)
    enc_date = encryptor.encrypt(birth_data.date)
    enc_time = encryptor.encrypt(birth_data.time)
    enc_lat = encryptor.encrypt(str(birth_data.latitude))
    enc_lon = encryptor.encrypt(str(birth_data.longitude))
    enc_place = encryptor.encrypt(birth_data.place)
else:
    enc_name, enc_date, enc_time = birth_data.name, birth_data.date, birth_data.time
    enc_lat, enc_lon, enc_place = str(birth_data.latitude), str(birth_data.longitude), birth_data.place

cursor.execute('''
    UPDATE birth_charts 
    SET name=?, date=?, time=?, latitude=?, longitude=?, timezone=?, place=?, gender=?, relation=?
    WHERE id=?
''', (enc_name, enc_date, enc_time, enc_lat, enc_lon, 
      birth_data.timezone, enc_place, birth_data.gender, birth_data.relation or 'other', chart_id))
```

### 3. Modify these functions to decrypt AFTER database SELECT:

**Line ~900 - get_self_birth_chart function:**
```python
# AFTER cursor.fetchone():
result = cursor.fetchone()
conn.close()

if not result:
    return {"has_self_chart": False}

# Decrypt data
if encryptor:
    name = encryptor.decrypt(result[0])
    date = encryptor.decrypt(result[1])
    time = encryptor.decrypt(result[2])
    lat = float(encryptor.decrypt(str(result[3])))
    lon = float(encryptor.decrypt(str(result[4])))
    place = encryptor.decrypt(result[6])
else:
    name, date, time = result[0], result[1], result[2]
    lat, lon, place = result[3], result[4], result[6]

return {
    "has_self_chart": True,
    "name": name,
    "date": date,
    "time": time,
    "latitude": lat,
    "longitude": lon,
    "timezone": result[5],
    "place": place,
    "gender": result[7]
}
```

**Line ~750 - login function (self_birth_chart section):**
```python
# AFTER cursor.fetchone():
self_birth_chart = cursor.fetchone()
birth_chart_data = None

if self_birth_chart and encryptor:
    birth_chart_data = {
        'id': self_birth_chart[0],
        'name': encryptor.decrypt(self_birth_chart[1]),
        'date': encryptor.decrypt(self_birth_chart[2]),
        'time': encryptor.decrypt(self_birth_chart[3]),
        'latitude': float(encryptor.decrypt(str(self_birth_chart[4]))),
        'longitude': float(encryptor.decrypt(str(self_birth_chart[5]))),
        'timezone': self_birth_chart[6],
        'place': encryptor.decrypt(self_birth_chart[7] or ''),
        'gender': self_birth_chart[8] or '',
        'relation': self_birth_chart[9] or 'self',
        'created_at': self_birth_chart[10]
    }
elif self_birth_chart:
    # No encryption
    birth_chart_data = {
        'id': self_birth_chart[0],
        'name': self_birth_chart[1],
        'date': self_birth_chart[2],
        'time': self_birth_chart[3],
        'latitude': self_birth_chart[4],
        'longitude': self_birth_chart[5],
        'timezone': self_birth_chart[6],
        'place': self_birth_chart[7] or '',
        'gender': self_birth_chart[8] or '',
        'relation': self_birth_chart[9] or 'self',
        'created_at': self_birth_chart[10]
    }
```

**Line ~1300 - get_birth_charts function:**
```python
# AFTER cursor.fetchall():
rows = cursor.fetchall()
conn.close()

charts = []
for row in rows:
    if encryptor:
        chart = {
            'id': row[0],
            'userid': row[1],
            'name': encryptor.decrypt(row[2]),
            'date': encryptor.decrypt(row[3]),
            'time': encryptor.decrypt(row[4]),
            'latitude': float(encryptor.decrypt(str(row[5]))),
            'longitude': float(encryptor.decrypt(str(row[6]))),
            'timezone': row[7],
            'created_at': row[8],
            'place': encryptor.decrypt(row[9] if row[9] else ''),
            'gender': row[10] if row[10] else '',
            'relation': row[11] if len(row) > 11 and row[11] else 'other'
        }
    else:
        chart = {
            'id': row[0],
            'userid': row[1],
            'name': row[2],
            'date': row[3],
            'time': row[4],
            'latitude': row[5],
            'longitude': row[6],
            'timezone': row[7],
            'created_at': row[8],
            'place': row[9] if row[9] else '',
            'gender': row[10] if row[10] else '',
            'relation': row[11] if len(row) > 11 and row[11] else 'other'
        }
    charts.append(chart)

return {"charts": charts}
```

## Setup Steps

1. Generate encryption key:
```bash
cd /Users/tarunydv/Desktop/Code/AstrologyApp/backend
python encryption_utils.py
```

2. Add key to .env file:
```bash
echo "ENCRYPTION_KEY=<generated_key>" >> .env
```

3. Run migration (creates backup first):
```bash
python migrate_encrypt_data.py
```

4. Apply code changes to main.py as documented above

5. Restart server

## Rollback Plan
If issues occur:
```bash
cp astrology.db.backup astrology.db
```

## Notes
- Encryption is backward compatible (detects unencrypted data)
- Timezone field is NOT encrypted (needed for calculations)
- Gender and relation fields are NOT encrypted (not PII)
- All PII fields (name, date, time, lat, lon, place) are encrypted
