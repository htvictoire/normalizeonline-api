from functools import wraps
from uuid import UUID
from django.conf import settings
from rest_framework import status
from drf_commons.response import error_response
from apps.accounts.models import GuestUser
from apps.accounts.utils import get_current_owner


def ensure_owner(view_func):
    @wraps(view_func)
    def _wrapped(self, request, *args, **kwargs):
        if getattr(request, "user", None) and request.user.is_authenticated:
            return view_func(self, request, *args, **kwargs)

        cookie_name = settings.GUEST_COOKIE_NAME
        guest_id = request.COOKIES.get(cookie_name)
        guest = None

        if guest_id:
            try:
                guest_uuid = UUID(str(guest_id))
                guest = GuestUser.objects.filter(id=guest_uuid).first()
            except ValueError:
                guest = None

        if not guest:
            guest = GuestUser.objects.create()
            request.COOKIES[cookie_name] = str(guest.id)
            response = view_func(self, request, *args, **kwargs)
            response.set_cookie(
                cookie_name,
                str(guest.id),
                httponly=True,
                secure=not settings.DEBUG,
                samesite="Lax",
                path="/",
                max_age=settings.GUEST_COOKIE_MAX_AGE,
            )
            return response

        return view_func(self, request, *args, **kwargs)

    return _wrapped


def ensure_is_owner(view_func):
    @wraps(view_func)
    def _wrapped(self, request, *args, **kwargs):
        if not get_current_owner(request):
            return error_response(
                message="You do not have permission to perform this action.",
                status_code=status.HTTP_403_FORBIDDEN,
            )
        return view_func(self, request, *args, **kwargs)

    return _wrapped
