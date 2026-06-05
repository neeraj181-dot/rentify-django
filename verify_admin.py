#!/usr/bin/env python
import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'rentify.settings')
django.setup()

from django.contrib.admin.sites import site
from subscriptions.models import SubscriptionPlan, UserSubscription, PaymentRecord, AddressAccessRequest, DailyMessageCount

models = [SubscriptionPlan, UserSubscription, PaymentRecord, AddressAccessRequest, DailyMessageCount]
for model in models:
    status = "✓" if model in site._registry else "✗"
    print(f"{status} {model.__name__} registered in admin")
