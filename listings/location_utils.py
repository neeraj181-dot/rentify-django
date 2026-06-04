"""Browse location helpers — session, filtering, counts."""

from django.db.models import Q, Count

POPULAR_CITIES = [
    'Malappuram',
    'Kochi',
    'Kottayam',
    'Calicut',
    'Trivandrum',
    'Bangalore',
    'Chennai',
]

# Extra strings that may appear in listing location fields
CITY_MATCH_TERMS = {
    'Malappuram': ['Malappuram'],
    'Kochi': ['Kochi', 'Cochin', 'Ernakulam'],
    'Kottayam': ['Kottayam'],
    'Calicut': ['Calicut', 'Kozhikode'],
    'Trivandrum': ['Trivandrum', 'Thiruvananthapuram'],
    'Bangalore': ['Bangalore', 'Bengaluru'],
    'Chennai': ['Chennai', 'Madras'],
}


def resolve_browse_location(request):
    """GET param wins; otherwise session; optionally persist GET to session."""
    loc = (request.GET.get('location') or '').strip()
    if loc:
        request.session['browse_location'] = loc
        request.session.modified = True
        return loc
    return (request.session.get('browse_location') or '').strip()


def set_browse_location_session(request, location):
    loc = (location or '').strip()
    if loc:
        request.session['browse_location'] = loc
    else:
        request.session.pop('browse_location', None)
    request.session.modified = True
    return loc


def location_filter_q(city):
    """Build Q filter for a canonical city name."""
    if not city:
        return Q()
    terms = CITY_MATCH_TERMS.get(city, [city])
    q = Q()
    for term in terms:
        q |= (
            Q(location__icontains=term)
            | Q(city__icontains=term)
            | Q(area_locality__icontains=term)
        )
    return q


def filter_queryset_by_location(queryset, city):
    if not city:
        return queryset
    return queryset.filter(location_filter_q(city))


def count_for_city(city):
    from .models import Product

    return Product.objects.filter(
        is_available=True,
        is_flagged=False,
    ).filter(location_filter_q(city)).count()


def popular_location_counts():
    return [{'city': c, 'count': count_for_city(c)} for c in POPULAR_CITIES]


def search_locations(query='', limit=20):
    """Distinct listing locations matching query, with counts."""
    from .models import Product

    qs = (
        Product.objects.filter(is_available=True, is_flagged=False)
        .exclude(location='')
        .values('location')
        .annotate(count=Count('id'))
        .order_by('-count')
    )
    if query:
        qs = qs.filter(location__icontains=query)
    results = []
    seen = set()
    for row in qs[: limit * 3]:
        loc = (row['location'] or '').strip()
        if not loc or loc.lower() in seen:
            continue
        seen.add(loc.lower())
        results.append({'city': loc, 'count': row['count']})
        if len(results) >= limit:
            break
    return results


def normalize_geocode_city(raw_city, raw_state=''):
    """Map geocoder result to a known popular city when possible."""
    if not raw_city:
        return raw_state or ''
    lower = raw_city.lower()
    for city, terms in CITY_MATCH_TERMS.items():
        for term in terms:
            if term.lower() in lower or lower in term.lower():
                return city
    return raw_city.split(',')[0].strip()
