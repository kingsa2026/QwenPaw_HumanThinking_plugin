import sqlite3
conn = sqlite3.connect('/root/.qwenpaw/workspaces/default/memory/human_thinking_memory_default.db')
cursor = conn.cursor()
cursor.execute("SELECT name, type, sql FROM sqlite_master")
for row in cursor.fetchall():
    print(f"{row[1]}: {row[0]}")
    if row[2]:
        print(f"  SQL: {row[2][:200]}")
    print()