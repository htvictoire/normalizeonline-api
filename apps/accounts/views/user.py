from django.conf import settings
from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import authenticate
from drf_commons.views import RetrieveModelMixin
from drf_commons.response import success_response, error_response
from core.authentication import CookieJWTAuthentication

from apps.accounts.serializers import LoginSerializer, UserSerializer
from apps.accounts.models import User

class UserViewSet(RetrieveModelMixin, viewsets.GenericViewSet):
    """
    API view to handle user authentication (login/logout).
    """
    queryset = User.objects.all()
    serializer_class = UserSerializer

    def get_serializer_class(self):
        serializer_map = {
            'login': LoginSerializer,
            'register': UserSerializer,
        }
        return serializer_map.get(self.action, self.serializer_class)
    
    def get_permissions(self):
        if self.action in ['login', 'register', 'refresh', 'verify']:
            return [permissions.AllowAny()]
        return super().get_permissions()
    
    def _set_auth_cookies(self, response, refresh_token: RefreshToken):
        access_token = refresh_token.access_token
        secure = not settings.DEBUG
        common_kwargs = {
            "httponly": True,
            "secure": secure,
            "samesite": "Lax",
            "path": "/",
        }
        response.set_cookie("access_token", str(access_token), **common_kwargs)
        response.set_cookie("refresh_token", str(refresh_token), **common_kwargs)

    def _clear_guest_cookie(self, response):
        cookie_name = getattr(settings, "GUEST_COOKIE_NAME", "guest_id")
        response.delete_cookie(cookie_name, path="/", samesite="Lax")


    @action(detail=False, methods=['post'], url_path='login')
    def login(self, request):
        """
        Handle user login.
        """
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data['email']
        password = serializer.validated_data['password']
        user = authenticate(request, email=email, password=password)
        if user is not None:
            # Authentication successful
            data = UserSerializer(user).data
            refresh = RefreshToken.for_user(user)
            response = success_response(
                data=data,
                message="User logged in successfully",
            )
            self._set_auth_cookies(response, refresh)
            self._clear_guest_cookie(response)
            return response
        else:
            # Authentication failed
            return error_response(
                message="Invalid email or password.",
            )
        
    @action(detail=False, methods=['post'], url_path='register')
    def register(self, request):
        """
        Handle user registration.
        """
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        refresh = RefreshToken.for_user(user)
        response = success_response(
            data=UserSerializer(user).data,
            message="User registered successfully",
        )
        self._set_auth_cookies(response, refresh)
        self._clear_guest_cookie(response)
        return response

    @action(detail=False, methods=['get'], url_path='me')
    def me(self, request):
        return success_response(
            data=UserSerializer(request.user).data,
            message="User retrieved successfully",
        )

    @action(detail=False, methods=['post'], url_path='refresh')
    def refresh(self, request):
        refresh_token = request.COOKIES.get("refresh_token")
        if not refresh_token:
            return error_response(
                message="Refresh token missing.",
                status_code=status.HTTP_401_UNAUTHORIZED,
            )
        try:
            refresh = RefreshToken(refresh_token)
        except Exception:
            return error_response(
                message="Invalid refresh token.",
                status_code=status.HTTP_401_UNAUTHORIZED,
            )

        response = success_response(
            data={},
            message="Token refreshed successfully",
        )
        self._set_auth_cookies(response, refresh)
        return response

    @action(detail=False, methods=['get'], url_path='verify')
    def verify(self, request):
        auth = CookieJWTAuthentication()
        result = auth.authenticate(request)
        if not result:
            return error_response(
                message="Unauthorized.",
                status_code=status.HTTP_401_UNAUTHORIZED,
            )
        return success_response(
            data={},
            message="User verified successfully",
        )

