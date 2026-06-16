from django.urls import path
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
    TokenBlacklistView,
)

from . import views

urlpatterns = [
    # Registration
    path('register/', views.register, name='auth-register'),
    # Login / Logout
    path('login/', views.login, name='auth-login'),
    path('logout/', views.logout, name='auth-logout'),
    # JWT tokens
    path('token/', TokenObtainPairView.as_view(), name='token-obtain'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token-refresh'),
    path('token/blacklist/', TokenBlacklistView.as_view(), name='token-blacklist'),
    # Profile
    path('profile/', views.profile, name='auth-profile'),
    # Password reset
    path('password-reset/', views.password_reset_request, name='auth-password-reset'),
    path(
        'password-reset/confirm/',
        views.password_reset_confirm,
        name='auth-password-reset-confirm',
    ),
]
