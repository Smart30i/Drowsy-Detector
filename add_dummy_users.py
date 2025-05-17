import sqlite3

# Connect to the existing database
conn = sqlite3.connect("users.db")
cur = conn.cursor()

# Dummy users to insert
dummy_users = [
    ("alice", "alice123"),
    ("bob", "bob456"),
    ("charlie", "charlie789"),
]

# Insert users
for username, password in dummy_users:
    try:
        cur.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, password))
        print(f"Inserted: {username}")
    except sqlite3.IntegrityError:
        print(f"Username {username} already exists.")

conn.commit()
conn.close()
