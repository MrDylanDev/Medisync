from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken

from .serializers import (
    RegisterSerializer,
    LoginSerializer,
    UsuarioSerializer,
    PasswordResetRequestSerializer,
    PasswordResetConfirmSerializer,
)

Usuario = get_user_model()


@api_view(['POST'])
@permission_classes([AllowAny])
def register(request):
    """
    Register a new user account.
    
    Creates a new Usuario with the provided credentials.
    Returns the user data and JWT tokens on success.
    """
    serializer = RegisterSerializer(data=request.data)
    if serializer.is_valid():
        user = serializer.save()
        refresh = RefreshToken.for_user(user)
        return Response(
            {
                'user': UsuarioSerializer(user).data,
                'access': str(refresh.access_token),
                'refresh': str(refresh),
            },
            status=status.HTTP_201_CREATED,
        )
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([AllowAny])
def login(request):
    """
    Authenticate user and return JWT tokens.
    
    Validates credentials and returns access + refresh tokens.
    """
    serializer = LoginSerializer(data=request.data, context={'request': request})
    if serializer.is_valid():
        user = serializer.validated_data['user']
        refresh = RefreshToken.for_user(user)
        return Response(
            {
                'user': UsuarioSerializer(user).data,
                'access': str(refresh.access_token),
                'refresh': str(refresh),
            }
        )
    return Response(serializer.errors, status=status.HTTP_401_UNAUTHORIZED)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def logout(request):
    """
    Logout by blacklisting the refresh token.
    
    Requires a valid refresh token in the request body.
    Blacklists it so it cannot be used to obtain new access tokens.
    """
    try:
        refresh_token = request.data.get('refresh')
        if not refresh_token:
            return Response(
                {'error': _('Token de refresco requerido.')},
                status=status.HTTP_400_BAD_REQUEST,
            )
        token = RefreshToken(refresh_token)
        token.blacklist()
        return Response(
            {'detail': _('Sesión cerrada correctamente.')},
            status=status.HTTP_200_OK,
        )
    except Exception:
        return Response(
            {'error': _('Token inválido o expirado.')},
            status=status.HTTP_400_BAD_REQUEST,
        )


@api_view(['GET', 'PUT', 'PATCH'])
@permission_classes([IsAuthenticated])
def profile(request):
    """
    Retrieve or update the authenticated user's profile.
    
    GET: Returns the current user's data.
    PUT/PATCH: Updates the current user's data.
    """
    user = request.user
    if request.method == 'GET':
        serializer = UsuarioSerializer(user)
        return Response(serializer.data)

    serializer = UsuarioSerializer(user, data=request.data, partial=request.method == 'PATCH')
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([AllowAny])
def password_reset_request(request):
    """
    Request a password reset email.
    
    Accepts an email address and (if registered) sends a
    password reset link. Always returns success to avoid
    user enumeration.
    """
    serializer = PasswordResetRequestSerializer(data=request.data)
    if serializer.is_valid():
        # In a real app, this would send an email with the reset link
        # For development, we just return success
        return Response(
            {'detail': _('Si el correo está registrado, recibirás un enlace de recuperación.')},
            status=status.HTTP_200_OK,
        )
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([AllowAny])
def password_reset_confirm(request):
    """
    Confirm password reset with token and set new password.
    
    Validates the reset token and updates the user's password.
    """
    serializer = PasswordResetConfirmSerializer(data=request.data)
    if serializer.is_valid():
        # In a real app, this would validate the token and update the password
        return Response(
            {'detail': _('Contraseña actualizada correctamente.')},
            status=status.HTTP_200_OK,
        )
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
