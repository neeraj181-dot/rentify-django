import os, django, sqlite3
os.environ['DJANGO_SETTINGS_MODULE'] = 'rentify.settings'
django.setup()
from django.conf import settings

db_path = settings.DATABASES['default']['NAME']
print("DB PATH:", db_path)

conn = sqlite3.connect(db_path)
cur = conn.cursor()
tables = [r[0] for r in cur.execute(
    "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
).fetchall()]
print("TOTAL TABLES:", len(tables))
sub_tables = [t for t in tables if 'subscri' in t.lower()]
print("SUBSCRIPTION TABLES:", sub_tables if sub_tables else "NONE FOUND")

# Check django_migrations for subscriptions
rows = cur.execute(
    "SELECT app, name, applied FROM django_migrations WHERE app='subscriptions'"
).fetchall()
print("MIGRATION RECORDS:", rows if rows else "NONE IN django_migrations")

conn.close()
