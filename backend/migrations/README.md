# Database Migrations

## How to Run Migrations in Production

### Method 1: Using sqlite3 command line
```bash
cd /path/to/backend
sqlite3 astrology.db < migrations/add_conversational_chat.sql
```

### Method 2: Using Python script
```bash
cd /path/to/backend
python -c "import sqlite3; conn = sqlite3.connect('astrology.db'); conn.executescript(open('migrations/add_conversational_chat.sql').read()); conn.close(); print('✅ Migration completed')"
```

### Verify Migration
```bash
sqlite3 astrology.db "SELECT name FROM sqlite_master WHERE type='table' AND name IN ('conversation_state', 'user_facts');"
```

## Rollback (if needed)
```sql
DROP TABLE IF EXISTS user_facts;
DROP TABLE IF EXISTS conversation_state;
ALTER TABLE chat_messages DROP COLUMN message_type;
```
