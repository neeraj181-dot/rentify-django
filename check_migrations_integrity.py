#!/usr/bin/env python
import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'rentify.settings')
django.setup()

from django.db import connection
from django.core.management import call_command
import io
import sys

# Check migration table integrity
print("=== DJANGO MIGRATIONS TABLE ===")
cursor = connection.cursor()
cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='django_migrations'")
if cursor.fetchone():
    print("✓ django_migrations table exists")
    cursor.execute("SELECT app, name FROM django_migrations WHERE app='subscriptions'")
    for app, name in cursor.fetchall():
        print(f"  - {app}: {name}")
else:
    print("✗ django_migrations table MISSING!")

# Double check by running makemigrations in dry-run mode
print("\n=== CHECKING FOR UNAPPLIED CHANGES ===")
# Capture output from makemigrations --dry-run
old_stdout = sys.stdout
sys.stdout = io.StringIO()
try:
    call_command('makemigrations', '--dry-run', verbosity=1)
    output = sys.stdout.getvalue()
finally:
    sys.stdout = old_stdout

if "No changes detected" in output:
    print("✓ No unapplied changes in any app")
else:
    print("! Potential changes detected:")
    print(output)

# Check for any inconsistencies
print("\n=== MIGRATION FILE INTEGRITY ===")
import sys
from pathlib import Path
migration_file = Path('d:\\rentify\\subscriptions\\migrations\\0001_initial.py')
if migration_file.exists():
    print(f"✓ Migration file exists: {migration_file}")
    # Try to import it
    try:
        import importlib.util
        spec = importlib.util.spec_from_file_location("migration", migration_file)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        print(f"✓ Migration file imports successfully")
        if hasattr(module, 'Migration'):
            print(f"✓ Migration class defined")
    except Exception as e:
        print(f"✗ Error importing migration: {e}")
else:
    print(f"✗ Migration file not found: {migration_file}")
