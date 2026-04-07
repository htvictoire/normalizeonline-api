from uuid import UUID
from django.conf import settings


def get_current_owner(request):
    if getattr(request, "user", None) and request.user.is_authenticated:
        return request.user.id

    guest_id = request.COOKIES.get(settings.GUEST_COOKIE_NAME, None)
    if not guest_id:
        return None

    try:
        return UUID(str(guest_id))
    except ValueError:
        return None
