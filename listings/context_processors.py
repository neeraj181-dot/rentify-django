def browse_location_processor(request):
    return {'browse_location': (request.session.get('browse_location') or '').strip()}
