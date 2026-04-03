import sqlite3
import uuid
import datetime
from ai_generator import SYSTEM_PROMPT

def setup_db():
    conn = sqlite3.connect('prompts.db')
    cursor = conn.cursor()
    
    # Create table reflecting the Supabase schema provided
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS prompts (
        id TEXT PRIMARY KEY,
        name TEXT,
        prompt_text TEXT,
        version INTEGER,
        temperature REAL,
        created_at TEXT,
        updated_at TEXT
    )
    ''')
    
    # Check if prompt already exists to avoid duplicates
    cursor.execute('SELECT COUNT(*) FROM prompts WHERE name = ?', ('visa_consultant_v1',))
    if cursor.fetchone()[0] == 0:
        now = datetime.datetime.now(datetime.timezone.utc).isoformat()
        cursor.execute('''
        INSERT INTO prompts (id, name, prompt_text, version, temperature, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (str(uuid.uuid4()), 'visa_consultant_v1', SYSTEM_PROMPT, 1, 0.7, now, now))
        conn.commit()
        print("✅ Database setup complete. Prompt successfully inserted into SQLite 'prompts.db'.")
    else:
        print("ℹ️ Prompt already exists in database.")
    
    conn.close()

if __name__ == '__main__':
    setup_db()
