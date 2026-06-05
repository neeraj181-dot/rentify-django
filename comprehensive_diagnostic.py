#!/usr/bin/env python
"""
Comprehensive diagnostic for Django subscriptions app.
Tests all potential failure modes.
"""
import os
import sys
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'rentify.settings')
django.setup()

from django.apps import apps
from django.db import connection, DEFAULT_DB_ALIAS
from django.db.models import Model
from collections import Counter
import inspect

print("=" * 80)
print("COMPREHENSIVE DJANGO SUBSCRIPTIONS DIAGNOSTIC")
print("=" * 80)

# 1. CHECK APP REGISTRATION
print("\n[1] APP REGISTRATION")
print("-" * 80)
all_app_labels = [app.label for app in apps.get_app_configs()]
duplicates = [x for x, count in Counter(all_app_labels).items() if count > 1]
print(f"Total installed apps: {len(all_app_labels)}")
print(f"Duplicate app labels: {duplicates if duplicates else 'NONE'}")
print(f"'subscriptions' in apps: {'subscriptions' in all_app_labels}")

# 2. CHECK MODELS
print("\n[2] MODELS")
print("-" * 80)
subscriptions_app = apps.get_app_config('subscriptions')
print(f"App name: {subscriptions_app.name}")
print(f"App path: {subscriptions_app.module.__path__[0]}")
print(f"Models in app: {[model._meta.model_name for model in subscriptions_app.get_models()]}")

# 3. CHECK DATABASE TABLES
print("\n[3] DATABASE TABLES")
print("-" * 80)
with connection.cursor() as cursor:
    # SQLite: get all table names
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = {row[0] for row in cursor.fetchall()}
    
    expected_tables = {
        'subscriptions_usersubscription',
        'subscriptions_subscriptionplan',
        'subscriptions_paymentrecord',
        'subscriptions_addressaccessrequest',
        'subscriptions_dailymessagecount',
    }
    
    missing = expected_tables - tables
    extra = {t for t in tables if t.startswith('subscriptions_')} - expected_tables
    
    print(f"Total tables in database: {len(tables)}")
    print(f"Expected subscription tables: {len(expected_tables)}")
    print(f"Missing tables: {missing if missing else 'NONE'}")
    print(f"Unexpected subscription tables: {extra if extra else 'NONE'}")
    
    for table in expected_tables:
        if table in tables:
            cursor.execute(f"PRAGMA table_info({table})")
            columns = cursor.fetchall()
            print(f"  ✓ {table}: {len(columns)} columns")
        else:
            print(f"  ✗ {table}: MISSING")

# 4. CHECK MIGRATION HISTORY
print("\n[4] MIGRATION HISTORY")
print("-" * 80)
from django.db.migrations.recorder import MigrationRecorder
recorder = MigrationRecorder(connection)
applied = recorder.applied_migrations()
subscriptions_migrations = [app for app, migration in applied if app == 'subscriptions']
print(f"Applied subscriptions migrations: {subscriptions_migrations}")
for app, migration in applied:
    if app == 'subscriptions':
        print(f"  - {app}/{migration}")

# 5. CHECK MODELS VS DATABASE CONSISTENCY
print("\n[5] MODEL/DATABASE CONSISTENCY")
print("-" * 80)
from subscriptions.models import UserSubscription, SubscriptionPlan
try:
    # Try to query each model
    user_sub_count = UserSubscription.objects.count()
    print(f"✓ UserSubscription.objects.count() = {user_sub_count}")
except Exception as e:
    print(f"✗ UserSubscription error: {type(e).__name__}: {e}")

try:
    plan_count = SubscriptionPlan.objects.count()
    print(f"✓ SubscriptionPlan.objects.count() = {plan_count}")
except Exception as e:
    print(f"✗ SubscriptionPlan error: {type(e).__name__}: {e}")

# 6. CHECK MODEL DEFINITIONS
print("\n[6] MODEL DEFINITIONS")
print("-" * 80)
print("UserSubscription fields:")
for field in UserSubscription._meta.get_fields():
    print(f"  - {field.name}: {field.__class__.__name__}")

print("\nUserSubscription indexes:")
if UserSubscription._meta.indexes:
    for idx in UserSubscription._meta.indexes:
        print(f"  - {idx.name}: {idx.fields}")
else:
    print("  (none defined in Meta.indexes)")

# 7. CHECK CONTEXT PROCESSOR
print("\n[7] CONTEXT PROCESSOR")
print("-" * 80)
try:
    from subscriptions.context_processors import premium_processor
    from django.contrib.auth.models import User, AnonymousUser
    from django.test import RequestFactory
    
    # Test with anonymous user
    factory = RequestFactory()
    request = factory.get('/')
    request.user = AnonymousUser()
    result = premium_processor(request)
    print(f"✓ premium_processor(anon) returned: {result.keys()}")
    
    # Test with authenticated user if available
    try:
        user = User.objects.first()
        if user:
            request.user = user
            result = premium_processor(request)
            print(f"✓ premium_processor(user={user.username}) returned: {result.keys()}")
    except Exception as e:
        print(f"! Could not test with authenticated user: {e}")
        
except Exception as e:
    print(f"✗ Context processor error: {type(e).__name__}: {e}")

# 8. CHECK UTILS
print("\n[8] UTILS FUNCTIONS")
print("-" * 80)
try:
    from subscriptions.utils import (
        is_premium, get_active_subscription, can_send_message,
        can_add_to_wishlist, can_view_contact_number, can_view_exact_address
    )
    print("✓ All utils functions imported successfully")
    
    # Try using them
    user = User.objects.first()
    if user:
        is_prem = is_premium(user)
        print(f"  - is_premium(first_user) = {is_prem}")
        
        sub = get_active_subscription(user)
        print(f"  - get_active_subscription(first_user) = {sub}")
        
        can_msg, remaining = can_send_message(user)
        print(f"  - can_send_message(first_user) = ({can_msg}, {remaining})")
    else:
        print("  (no users in database to test with)")
        
except Exception as e:
    print(f"✗ Utils error: {type(e).__name__}: {e}")

print("\n" + "=" * 80)
print("DIAGNOSTIC COMPLETE")
print("=" * 80)
