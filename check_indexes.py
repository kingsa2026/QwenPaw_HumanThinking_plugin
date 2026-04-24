import sqlite3
conn = sqlite3.connect('/root/.qwenpaw/workspaces/default/memory/human_thinking_memory_default.db')
cursor = conn.cursor()
cursor.execute("SELECT name, sql FROM sqlite_master WHERE type='index'")
for row in cursor.fetchall():
    print(f"Index: {row[0]}")
    if row[1]:
        print(f"SQL: {row[1]}")
    print()