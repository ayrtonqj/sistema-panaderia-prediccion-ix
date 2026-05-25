import sqlite3
import sys

db='db.sqlite3'
conn=sqlite3.connect(db)
c=conn.cursor()
try:
    # List tables
    c.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = [r[0] for r in c.fetchall()]
    print('TABLES:', tables)
    if 'usuarios' not in tables:
        print('NO_TABLE_USUARIOS')
    else:
        c.execute('SELECT username, email, rol, is_superuser, password FROM usuarios')
        rows=c.fetchall()
        if not rows:
            print('NO_USERS')
        else:
            for r in rows:
                username, email, rol, is_superuser, password = r
                print(f"USERNAME: {username}")
                print(f"EMAIL: {email}")
                print(f"ROL: {rol}")
                print(f"IS_SUPERUSER: {is_superuser}")
                print(f"PASSWORD_HASH: {password}")
                print('---')
except Exception as e:
    print('ERROR:', e)
finally:
    conn.close()
