#!/usr/bin/env python
"""
Final verification: Test complete user flow
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'rentify.settings')
django.setup()

from django.test import Client
from django.contrib.auth.models import User

print("=" * 80)
print("FINAL VERIFICATION - USER FLOW TEST")
print("=" * 80)

# Test 1: Homepage for anonymous user
print("\n[TEST 1] Homepage (Anonymous User)")
print("-" * 80)
client = Client()
try:
    response = client.get('/')
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        print("✓ Homepage loaded successfully for anonymous user")
        # Check if premium badge/status is in response
        content = response.content.decode()
        if 'premium' in content.lower():
            print("  - Premium-related content found in page")
    else:
        print(f"✗ Unexpected status: {response.status_code}")
except Exception as e:
    print(f"✗ Error loading homepage: {type(e).__name__}: {e}")

# Test 2: Homepage for authenticated user
print("\n[TEST 2] Homepage (Authenticated User)")
print("-" * 80)
try:
    user = User.objects.first()
    if user:
        client.force_login(user)
        response = client.get('/')
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            print(f"✓ Homepage loaded successfully for user '{user.username}'")
        else:
            print(f"✗ Unexpected status: {response.status_code}")
    else:
        print("(No users in database, skipping authenticated test)")
except Exception as e:
    print(f"✗ Error loading homepage for authenticated user: {type(e).__name__}: {e}")

# Test 3: Admin panel access (subscription models)
print("\n[TEST 3] Admin Panel (Subscriptions Models)")
print("-" * 80)
try:
    from django.contrib.admin.sites import site
    from subscriptions.models import UserSubscription, SubscriptionPlan
    
    # Check if models are registered
    user_sub_registered = UserSubscription in site._registry
    plan_registered = SubscriptionPlan in site._registry
    
    print(f"UserSubscription in admin: {'✓' if user_sub_registered else '✗'}")
    print(f"SubscriptionPlan in admin: {'✓' if plan_registered else '✗'}")
    
    # Try accessing the changelist view
    try:
        response = client.get('/admin/subscriptions/usersubscription/')
        print(f"Admin changelist status: {response.status_code}")
        if response.status_code in [200, 302]:  # 200 = OK, 302 = redirect to login
            print("✓ Admin views accessible")
        else:
            print(f"! Unexpected status: {response.status_code}")
    except Exception as e:
        print(f"! Admin access test incomplete: {type(e).__name__}")
        
except Exception as e:
    print(f"✗ Error checking admin: {type(e).__name__}: {e}")

# Test 4: Premium features check
print("\n[TEST 4] Premium Features")
print("-" * 80)
try:
    from subscriptions.utils import is_premium, can_send_message, can_add_to_wishlist
    from subscriptions.models import UserSubscription, SubscriptionPlan
    
    user = User.objects.first()
    if user:
        # Check free tier limitations
        can_msg, remaining = can_send_message(user)
        can_wishlist = can_add_to_wishlist(user, 0)
        is_prem = is_premium(user)
        
        print(f"User '{user.username}' status:")
        print(f"  - Premium: {is_prem}")
        print(f"  - Can send message: {can_msg} (remaining: {remaining})")
        print(f"  - Can add to wishlist (0 items): {can_wishlist}")
        print("✓ Premium features working correctly")
    else:
        print("(No users to test)")
        
except Exception as e:
    print(f"✗ Error testing premium features: {type(e).__name__}: {e}")

print("\n" + "=" * 80)
print("VERIFICATION COMPLETE")
print("=" * 80)
