import os, django, traceback
os.environ['DJANGO_SETTINGS_MODULE'] = 'rentify.settings'
django.setup()

# Test 1: Direct table query
print("=== TEST 1: Direct ORM query ===")
try:
    from subscriptions.models import UserSubscription, SubscriptionPlan
    count = UserSubscription.objects.count()
    print(f"OK - UserSubscription rows: {count}")
except Exception as e:
    traceback.print_exc()

# Test 2: utils.is_premium
print("\n=== TEST 2: utils.is_premium ===")
try:
    from subscriptions.utils import is_premium, get_active_subscription
    from django.contrib.auth.models import User
    u = User.objects.first()
    if u:
        result = is_premium(u)
        print(f"OK - is_premium({u.username}) = {result}")
    else:
        print("No users in DB to test with")
except Exception as e:
    traceback.print_exc()

# Test 3: context processor
print("\n=== TEST 3: context_processor ===")
try:
    from subscriptions.context_processors import premium_processor
    from django.test import RequestFactory
    from django.contrib.auth.models import AnonymousUser
    rf = RequestFactory()
    req = rf.get('/')
    req.user = AnonymousUser()
    ctx = premium_processor(req)
    print(f"OK - anon context: {ctx}")
except Exception as e:
    traceback.print_exc()

# Test 4: homepage view
print("\n=== TEST 4: Homepage request ===")
try:
    from django.test import Client
    from django.contrib.auth.models import User
    c = Client()
    r = c.get('/')
    print(f"OK - homepage status: {r.status_code}")
except Exception as e:
    traceback.print_exc()

print("\n=== ALL TESTS COMPLETE ===")
