import sqlite3
DB = "travel.db"

def init_db():
    conn = sqlite3.connect(DB)
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS travel_memory (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            destination TEXT,
            days INTEGER,
            budget INTEGER,
            style TEXT,
            feedback TEXT
        )
    """)
    conn.commit()
    conn.close()

def load_memory():
    conn = sqlite3.connect(DB)
    cur = conn.cursor()
    cur.execute("""
        SELECT destination, days, budget, style, feedback
        FROM travel_memory
        ORDER BY id DESC LIMIT 1
    """)
    row = cur.fetchone()
    conn.close()
    if row:
        return {
            "destination": row[0],
            "days": row[1],
            "budget": row[2],
            "style": row[3],
            "feedback": row[4]
        }
    return {}

def save_memory(memory):
    conn = sqlite3.connect(DB)
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO travel_memory (destination, days, budget, style, feedback)
        VALUES (?, ?, ?, ?, ?)
    """, (
        memory.get("destination"),
        memory.get("days"),
        memory.get("budget"),
        memory.get("style"),
        memory.get("feedback")
    ))
    conn.commit()
    conn.close()
