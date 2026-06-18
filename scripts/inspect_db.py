import sqlite3

conn = sqlite3.connect('db.sqlite3')
cur = conn.cursor()
cur.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
tables = [r[0] for r in cur.fetchall()]
print('Tables:', [t for t in tables if 'client' in t.lower() or t == 'VENTAS'])
for t in ['CLIENTES', 'clientes_cliente']:
    if t in tables:
        cur.execute(f'SELECT COUNT(*) FROM "{t}"')
        print(t, 'count:', cur.fetchone()[0])
        cur.execute(f'SELECT * FROM "{t}" LIMIT 3')
        print(t, 'rows:', cur.fetchall())
