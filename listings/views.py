from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.contrib.auth.decorators import login_required
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_POST
from django.contrib import messages
from django.db.models import Q, Avg, Case, When, IntegerField, Value
from django.http import JsonResponse, HttpResponseRedirect
from django.core.paginator import Paginator
from .models import Product, ProductImage, Wishlist, CATEGORY_CHOICES, CATEGORY_ICONS
from .forms import ProductForm, ProductImageForm, SearchForm
from reviews.models import Review
from .location_utils import (
    resolve_browse_location,
    set_browse_location_session,
    filter_queryset_by_location,
    popular_location_counts,
    search_locations,
    normalize_geocode_city,
    POPULAR_CITIES,
)


def home_view(request):
    base = Product.objects.filter(is_available=True, is_flagged=False)
    loc = resolve_browse_location(request)
    if loc:
        base = filter_queryset_by_location(base, loc)
    featured = base.order_by('-rating', '-created_at')[:8]
    trending = base.order_by('-views_count')[:6]
    categories = CATEGORY_CHOICES
    total_listings = Product.objects.filter(is_available=True).count()
    context = {
        'featured': featured,
        'trending': trending,
        'categories': categories,
        'category_icons': CATEGORY_ICONS,
        'total_listings': total_listings,
    }
    return render(request, 'listings/home.html', context)


def how_it_works_view(request):
    return render(request, 'listings/how_it_works.html')


def categories_page_view(request):
    from django.db.models import Count
    # Count live listings per category
    cat_counts = dict(
        Product.objects.filter(is_available=True, is_flagged=False)
               .values_list('category')
               .annotate(c=Count('id'))
               .values_list('category', 'c')
    )
    categories_with_counts = [
        (slug, name, CATEGORY_ICONS.get(slug, 'bi-grid'), cat_counts.get(slug, 0))
        for slug, name in CATEGORY_CHOICES
    ]
    return render(request, 'listings/categories_page.html', {
        'categories_with_counts': categories_with_counts,
        'total_listings': sum(cat_counts.values()),
    })


def earn_view(request):
    total_listings = Product.objects.filter(is_available=True).count()
    return render(request, 'listings/earn.html', {'total_listings': total_listings})


def search_view(request):
    # Build category list for template — no filter tricks needed
    CATEGORY_DATA = [
        ('laptops',            'Laptops',            'bi-laptop-fill'),
        ('cameras',            'Cameras',            'bi-camera-fill'),
        ('gaming',             'Gaming',             'bi-joystick'),
        ('drones',             'Drones',             'bi-send-fill'),
        ('bikes',              'Bikes',              'bi-bicycle'),
        ('cars',               'Cars',               'bi-car-front-fill'),
        ('furniture',          'Furniture',          'bi-house-fill'),
        ('tools',              'Tools',              'bi-tools'),
        ('books',              'Books',              'bi-book-fill'),
        ('musical_instruments','Music',              'bi-music-note-beamed'),
        ('projectors',         'Projectors',         'bi-projector'),
        ('other',              'Other',              'bi-grid'),
    ]
    products = Product.objects.filter(is_available=True, is_flagged=False)

    q = request.GET.get('q', '').strip()
    category = request.GET.get('category', '')
    location = resolve_browse_location(request)
    min_price = request.GET.get('min_price', '')
    max_price = request.GET.get('max_price', '')
    min_rating = request.GET.get('min_rating', '')
    available_only = request.GET.get('available_only', '')
    sort = request.GET.get('sort', 'newest')

    if q:
        products = products.filter(
            Q(title__icontains=q) | Q(description__icontains=q) | Q(location__icontains=q)
            | Q(city__icontains=q) | Q(area_locality__icontains=q)
        )
    if category:
        products = products.filter(category=category)
    if location:
        products = filter_queryset_by_location(products, location)
        products = products.annotate(
            loc_priority=Case(
                When(location__istartswith=location, then=Value(0)),
                When(location__icontains=location, then=Value(1)),
                default=Value(2),
                output_field=IntegerField(),
            )
        )
    if min_price:
        products = products.filter(price_per_day__gte=min_price)
    if max_price:
        products = products.filter(price_per_day__lte=max_price)
    if min_rating:
        products = products.filter(rating__gte=min_rating)

    sort_map = {
        'newest': '-created_at',
        'oldest': 'created_at',
        'price_low': 'price_per_day',
        'price_high': '-price_per_day',
        'rating': '-rating',
        'popular': '-views_count',
    }
    order = sort_map.get(sort, '-created_at')
    if location:
        products = products.order_by('loc_priority', order)
    else:
        products = products.order_by(order)

    paginator = Paginator(products, 12)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    # Wishlist ids for current user
    wishlist_ids = []
    if request.user.is_authenticated:
        wishlist_ids = list(Wishlist.objects.filter(user=request.user).values_list('product_id', flat=True))

    has_filters = any([q, category, location, min_price, max_price, min_rating])
    featured = []
    if not has_filters:
        featured = list(
            Product.objects.filter(is_available=True, is_flagged=False)
            .order_by('-rating', '-created_at')[:8]
        )

    context = {
        'page_obj': page_obj,
        'products': page_obj,
        'featured': featured,
        'total_count': products.count(),
        'q': q,
        'category': category,
        'location': location,
        'categories': CATEGORY_CHOICES,
        'category_icons': CATEGORY_ICONS,
        'sort': sort,
        'wishlist_ids': wishlist_ids,
        'CATEGORY_DATA': CATEGORY_DATA,
        'active_category_name': dict((s, n) for s, n, i in CATEGORY_DATA).get(category, ''),
        'has_filters': has_filters,
    }
    return render(request, 'listings/search.html', context)


def category_view(request, category_slug):
    products = Product.objects.filter(
        category=category_slug, is_available=True, is_flagged=False
    )
    location = resolve_browse_location(request)
    if location:
        products = filter_queryset_by_location(products, location).annotate(
            loc_priority=Case(
                When(location__istartswith=location, then=Value(0)),
                When(location__icontains=location, then=Value(1)),
                default=Value(2),
                output_field=IntegerField(),
            )
        ).order_by('loc_priority', '-rating', '-created_at')
    else:
        products = products.order_by('-rating', '-created_at')
    category_name = dict(CATEGORY_CHOICES).get(category_slug, 'Products')
    category_icon = CATEGORY_ICONS.get(category_slug, 'bi-grid')

    paginator = Paginator(products, 12)
    page_obj = paginator.get_page(request.GET.get('page'))

    wishlist_ids = []
    if request.user.is_authenticated:
        wishlist_ids = list(Wishlist.objects.filter(user=request.user).values_list('product_id', flat=True))

    context = {
        'products': page_obj,
        'category_name': category_name,
        'category_slug': category_slug,
        'category_icon': category_icon,
        'wishlist_ids': wishlist_ids,
        'total_count': products.count(),
        'browse_location': location,
    }
    return render(request, 'listings/category.html', context)


def product_detail_view(request, pk):
    product = get_object_or_404(Product, pk=pk, is_flagged=False)
    # Increment views
    Product.objects.filter(pk=pk).update(views_count=product.views_count + 1)

    images = product.images.all()
    reviews = Review.objects.filter(product=product).select_related('reviewer').order_by('-created_at')
    similar = Product.objects.filter(
        category=product.category, is_available=True, is_flagged=False
    ).exclude(pk=pk)[:4]

    in_wishlist = False
    user_booked = False
    is_owner = False
    if request.user.is_authenticated:
        is_owner = product.owner_id == request.user.id
        in_wishlist = Wishlist.objects.filter(user=request.user, product=product).exists()
        from bookings.models import Booking
        user_booked = Booking.objects.filter(
            renter=request.user, product=product, status__in=['approved', 'completed']
        ).exists()

    context = {
        'product': product,
        'images': images,
        'reviews': reviews,
        'similar': similar,
        'in_wishlist': in_wishlist,
        'user_booked': user_booked,
        'is_owner': is_owner,
        'show_private_address': is_owner or user_booked,
        'rating_range': range(1, 6),
    }
    return render(request, 'listings/product_detail.html', context)


def _listing_form_context():
    """Shared metadata for create/edit listing forms."""
    from .location_data import CITIES_BY_STATE
    categories = [
        {
            'value': value,
            'label': label,
            'icon': CATEGORY_ICONS.get(value, 'bi-grid'),
        }
        for value, label in CATEGORY_CHOICES
    ]
    return {'listing_categories': categories, 'cities_by_state': CITIES_BY_STATE}


def _redirect_after_listing_save(product):
    """POST/Redirect/GET — redirect to My Listings, not the form. Prevents Back-button resubmit."""
    from django.urls import reverse
    return HttpResponseRedirect(reverse('my_listings'), status=303)


@login_required
def listing_form_meta(request):
    """JSON: categories for listing comboboxes."""
    ctx = _listing_form_context()
    return JsonResponse({
        'categories': ctx['listing_categories'],
        'cities_by_state': ctx['cities_by_state'],
    })


@never_cache
@login_required
def create_listing_view(request):
    if request.method == 'POST':
        form = ProductForm(request.POST)
        if form.is_valid():
            product = form.save(commit=False)
            product.owner = request.user
            product.auto_calculate_prices()
            if product.price_per_day < 10:
                product.is_flagged = True
                product.flag_reason = 'Suspiciously low price - under review'
            product.save()
            saved = 0
            for i in range(5):
                img = request.FILES.get(f'image_{i}')
                if img:
                    ProductImage.objects.create(
                        product=product,
                        image=img,
                        is_primary=(saved == 0),
                        order=saved,
                    )
                    saved += 1
            messages.success(
                request,
                '✓ Listing created successfully! You can manage it from My Listings.',
            )
            # PRG: 303 redirect → my_listings so Back never replays the POST
            return HttpResponseRedirect(reverse('my_listings'), status=303)
    else:
        form = ProductForm()
    context = {'form': form}
    context.update(_listing_form_context())
    resp = render(request, 'listings/create_listing.html', context)
    # Prevent browser from caching the blank form page
    resp['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
    resp['Pragma']  = 'no-cache'
    resp['Expires'] = '0'
    return resp


@never_cache
@login_required
def edit_listing_view(request, pk):
    product = get_object_or_404(Product, pk=pk, owner=request.user)
    if request.method == 'POST':
        form = ProductForm(request.POST, instance=product)
        if form.is_valid():
            product = form.save(commit=False)
            product.auto_calculate_prices()
            product.save()
            existing_count = product.images.count()
            slots_left = max(0, 5 - existing_count)
            added = 0
            for i in range(5):
                if added >= slots_left:
                    break
                img = request.FILES.get(f'image_{i}')
                if img:
                    ProductImage.objects.create(
                        product=product,
                        image=img,
                        is_primary=False,
                        order=existing_count + added,
                    )
                    added += 1
            if not product.images.filter(is_primary=True).exists():
                first_img = product.images.order_by('order', 'uploaded_at').first()
                if first_img:
                    first_img.is_primary = True
                    first_img.save(update_fields=['is_primary'])
            messages.success(request, '✓ Listing updated successfully!')
            # PRG: 303 redirect → my_listings
            return HttpResponseRedirect(reverse('my_listings'), status=303)
    else:
        form = ProductForm(instance=product)
    context = {'form': form, 'product': product}
    context.update(_listing_form_context())
    resp = render(request, 'listings/edit_listing.html', context)
    resp['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
    resp['Pragma']  = 'no-cache'
    resp['Expires'] = '0'
    return resp


@login_required
def delete_listing_view(request, pk):
    product = get_object_or_404(Product, pk=pk, owner=request.user)
    if request.method == 'POST':
        product.delete()
        messages.success(request, 'Listing deleted.')
        return redirect('my_listings')
    return render(request, 'listings/delete_listing.html', {'product': product})


@login_required
def my_listings_view(request):
    from django.db.models import Sum
    from bookings.models import Booking

    listings = list(Product.objects.filter(owner=request.user).order_by('-created_at'))
    product_ids = [p.id for p in listings]
    rented_ids = set(
        Booking.objects.filter(
            product_id__in=product_ids,
            status__in=['approved', 'active'],
        ).values_list('product_id', flat=True)
    )
    pending_ids = set(
        Booking.objects.filter(
            product_id__in=product_ids,
            status='pending',
        ).values_list('product_id', flat=True)
    )
    for product in listings:
        if product.id in rented_ids:
            product.display_status = 'rented'
        elif product.id in pending_ids:
            product.display_status = 'pending'
        elif product.is_available:
            product.display_status = 'active'
        else:
            product.display_status = 'paused'

    total_views = sum(p.views_count for p in listings)
    active_count = sum(1 for p in listings if p.display_status == 'active')
    return render(request, 'listings/my_listings.html', {
        'listings': listings,
        'total_views': total_views,
        'active_count': active_count,
    })


@login_required
def toggle_wishlist_view(request, pk):
    product = get_object_or_404(Product, pk=pk)
    wishlist_item, created = Wishlist.objects.get_or_create(user=request.user, product=product)
    if not created:
        wishlist_item.delete()
        in_wishlist = False
    else:
        in_wishlist = True
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({'in_wishlist': in_wishlist})
    return redirect(request.META.get('HTTP_REFERER', 'product_detail'))


@login_required
def wishlist_view(request):
    wishlist = Wishlist.objects.filter(user=request.user).select_related('product').order_by('-added_at')
    return render(request, 'listings/wishlist.html', {'wishlist': wishlist})


@login_required
@require_POST
def set_primary_image(request, image_id):
    image = get_object_or_404(ProductImage, id=image_id, product__owner=request.user)
    ProductImage.objects.filter(product=image.product).update(is_primary=False)
    image.is_primary = True
    image.order = 0
    image.save(update_fields=['is_primary', 'order'])
    return JsonResponse({'ok': True, 'image_id': image.id, 'url': image.image.url})


@login_required
def delete_product_image(request, image_id):
    image = get_object_or_404(ProductImage, id=image_id, product__owner=request.user)
    product = image.product
    was_primary = image.is_primary
    image.delete()
    if was_primary:
        nxt = product.images.order_by('order', 'uploaded_at').first()
        if nxt:
            nxt.is_primary = True
            nxt.save(update_fields=['is_primary'])
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        primary = product.images.filter(is_primary=True).first()
        return JsonResponse({
            'ok': True,
            'remaining': product.images.count(),
            'primary_id': primary.id if primary else None,
            'primary_url': primary.image.url if primary else None,
        })
    messages.success(request, 'Image removed.')
    return redirect('edit_listing', pk=product.pk)


def location_counts_api(request):
    """Popular cities + searchable locations with listing counts."""
    q = request.GET.get('q', '').strip()
    selected = resolve_browse_location(request)
    return JsonResponse({
        'popular': popular_location_counts(),
        'results': search_locations(q),
        'selected': selected,
        'popular_cities': POPULAR_CITIES,
    })


@require_POST
def set_browse_location_view(request):
    """Persist browse city to Django session."""
    import json
    if request.content_type == 'application/json':
        try:
            payload = json.loads(request.body.decode() or '{}')
        except json.JSONDecodeError:
            payload = {}
        loc = (payload.get('location') or '').strip()
    else:
        loc = (request.POST.get('location') or '').strip()
    set_browse_location_session(request, loc)
    return JsonResponse({'ok': True, 'location': loc})


def reverse_geocode_view(request):
    """Reverse geocode lat/lon → city (server-side, avoids CORS)."""
    import json
    import urllib.error
    import urllib.request

    lat = request.GET.get('lat')
    lon = request.GET.get('lon')
    if not lat or not lon:
        return JsonResponse({'error': 'Missing coordinates'}, status=400)
    url = (
        f'https://nominatim.openstreetmap.org/reverse?lat={lat}&lon={lon}'
        f'&format=json&addressdetails=1'
    )
    req = urllib.request.Request(
        url,
        headers={'User-Agent': 'Rentify/1.0 (https://rentify.local; marketplace)'},
    )
    try:
        with urllib.request.urlopen(req, timeout=8) as resp:
            data = json.loads(resp.read().decode())
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError):
        return JsonResponse({'error': 'Could not detect location. Please pick a city manually.'}, status=502)

    addr = data.get('address') or {}
    raw_city = (
        addr.get('city')
        or addr.get('town')
        or addr.get('village')
        or addr.get('municipality')
        or addr.get('state_district')
        or addr.get('county')
        or ''
    )
    state = addr.get('state') or ''
    city = normalize_geocode_city(raw_city, state)
    if not city:
        return JsonResponse({'error': 'Could not determine city. Please select manually.'}, status=404)
    set_browse_location_session(request, city)
    return JsonResponse({'ok': True, 'city': city, 'state': state, 'display': city})


def ai_price_suggestion(request):
    """Simple AI price suggestion based on product title keywords."""
    title = request.GET.get('title', '').lower()
    suggestions = {
        'macbook': {'daily': 350, 'weekly': 2000, 'monthly': 7000, 'deposit': 10000},
        'laptop': {'daily': 250, 'weekly': 1500, 'monthly': 5000, 'deposit': 8000},
        'iphone': {'daily': 200, 'weekly': 1200, 'monthly': 4000, 'deposit': 5000},
        'camera': {'daily': 300, 'weekly': 1800, 'monthly': 6000, 'deposit': 8000},
        'drone': {'daily': 400, 'weekly': 2500, 'monthly': 8000, 'deposit': 15000},
        'bike': {'daily': 150, 'weekly': 900, 'monthly': 3000, 'deposit': 3000},
        'car': {'daily': 1500, 'weekly': 9000, 'monthly': 30000, 'deposit': 20000},
        'ps5': {'daily': 200, 'weekly': 1200, 'monthly': 4000, 'deposit': 5000},
        'projector': {'daily': 300, 'weekly': 1800, 'monthly': 6000, 'deposit': 5000},
        'guitar': {'daily': 100, 'weekly': 600, 'monthly': 2000, 'deposit': 3000},
    }
    result = {'daily': 100, 'weekly': 600, 'monthly': 2000, 'deposit': 2000}
    for keyword, prices in suggestions.items():
        if keyword in title:
            result = prices
            break
    return JsonResponse({'suggestion': result, 'title': title})


def ai_description_generator(request):
    """Generate a simple professional description."""
    title = request.GET.get('title', '')
    category = request.GET.get('category', '')
    if not title:
        return JsonResponse({'description': ''})

    cat_name = dict(CATEGORY_CHOICES).get(category, category)
    description = (
        f"Rent this premium {title} — perfect for your needs without the commitment of buying. "
        f"This {cat_name.lower()} is well-maintained, fully functional, and ready to use. "
        f"Ideal for professionals, students, or anyone who needs it temporarily. "
        f"Comes with all original accessories. Available for daily, weekly, or monthly rental. "
        f"Pickup and drop-off can be arranged. Contact the owner for more details."
    )
    return JsonResponse({'description': description})
