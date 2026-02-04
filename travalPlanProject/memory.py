import sqlite3
DB = "travel.db"

def init_db():
    """Initialize the database with updated schema"""
    conn = sqlite3.connect(DB)
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS travel_memory (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            destination TEXT,
            days INTEGER,
            budget INTEGER,
            style TEXT,
            purpose TEXT,
            feedback TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    conn.close()

def load_memory():
    """Load the most recent travel memory"""
    conn = sqlite3.connect(DB)
    cur = conn.cursor()
    cur.execute("""
        SELECT destination, days, budget, style, purpose, feedback
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
            "purpose": row[4],
            "feedback": row[5]
        }
    return {}

def save_memory(memory):
    """Save current travel memory to database"""
    conn = sqlite3.connect(DB)
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO travel_memory (destination, days, budget, style, purpose, feedback)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (
        memory.get("destination"),
        memory.get("days"),
        memory.get("budget"),
        memory.get("style"),
        memory.get("purpose"),
        memory.get("feedback")
    ))
    conn.commit()
    conn.close()

def get_all_trips():
    """Get all saved trips (for history feature)"""
    conn = sqlite3.connect(DB)
    cur = conn.cursor()
    cur.execute("""
        SELECT id, destination, days, budget, style, purpose, created_at
        FROM travel_memory
        ORDER BY id DESC
        LIMIT 10
    """)
    rows = cur.fetchall()
    conn.close()
    
    trips = []
    for row in rows:
        trips.append({
            "id": row[0],
            "destination": row[1],
            "days": row[2],
            "budget": row[3],
            "style": row[4],
            "purpose": row[5],
            "created_at": row[6]
        })
    return trips
