import sqlite3
from datetime import datetime

def init_db():
    """Initialize the database"""
    conn = sqlite3.connect('travel.db')
    cursor = conn.cursor()
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS trips (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            destination TEXT NOT NULL,
            days INTEGER NOT NULL,
            budget REAL NOT NULL,
            style TEXT,
            purpose TEXT,
            feedback TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    conn.commit()
    conn.close()

def save_memory(memory_data):
    """Save trip data to database"""
    conn = sqlite3.connect('travel.db')
    cursor = conn.cursor()
    
    cursor.execute('''
        INSERT INTO trips (destination, days, budget, style, purpose, feedback, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (
        memory_data.get('destination', ''),
        memory_data.get('days', 0),
        memory_data.get('budget', 0),
        memory_data.get('style', ''),
        memory_data.get('purpose', ''),
        memory_data.get('feedback', ''),
        datetime.now()
    ))
    
    conn.commit()
    conn.close()

def load_memory():
    """Load the most recent trip data"""
    conn = sqlite3.connect('travel.db')
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT destination, days, budget, style, purpose, feedback
        FROM trips
        ORDER BY created_at DESC
        LIMIT 1
    ''')
    
    row = cursor.fetchone()
    conn.close()
    
    if row:
        return {
            'destination': row[0],
            'days': row[1],
            'budget': row[2],
            'style': row[3],
            'purpose': row[4],
            'feedback': row[5]
        }
    else:
        return {
            'destination': 'Paris',
            'days': 5,
            'budget': 1500,
            'style': 'balanced',
            'purpose': 'leisure'
        }

def get_all_trips():
    """Get all trip history"""
    conn = sqlite3.connect('travel.db')
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT destination, days, budget, purpose, created_at
        FROM trips
        ORDER BY created_at DESC
        LIMIT 10
    ''')
    
    rows = cursor.fetchall()
    conn.close()
    
    trips = []
    for row in rows:
        trips.append({
            'destination': row[0],
            'days': row[1],
            'budget': row[2],
            'purpose': row[3],
            'created_at': row[4]
        })
    return trips