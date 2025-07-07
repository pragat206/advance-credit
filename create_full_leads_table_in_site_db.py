import sqlite3

conn = sqlite3.connect('site.db')
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS leads (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT,
    contact TEXT,
    email TEXT,
    message TEXT,
    source TEXT,
    created_at DATETIME,
    updated_at DATETIME,
    lead_type TEXT,
    assigned_to INTEGER,
    status TEXT,
    is_verified BOOLEAN,
    documentation TEXT,
    notes TEXT,
    partner_id INTEGER
)
""")

conn.commit()
conn.close()
print("Full leads table created in site.db") 