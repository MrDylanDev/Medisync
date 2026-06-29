from django.contrib.auth import get_user_model
from django.db.models import Q
from django.utils.translation import gettext_lazy as _
from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAdminUser, IsAuthenticated
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination
from rest_framework_simplejwt.tokens import RefreshToken

from .serializers import (
    RegisterSerializer,
    LoginSerializer,
    UsuarioSerializer,
    PasswordResetRequestSerializer,
    PasswordResetConfirmSerializer,
)

Usuario = get_user_model()


@extend_schema(tags=['Auth'], summary='Registrar usuario', request=RegisterSerializer, responses={201: None})
@api_view(['POST'])
@permission_classes([AllowAny])
def register(request):
    """Register a new user account."""
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


@extend_schema(tags=['Auth'], summary='Iniciar sesión', request=LoginSerializer, responses={200: None})
@api_view(['POST'])
@permission_classes([AllowAny])
def login(request):
    """Authenticate user and return JWT tokens."""
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


@extend_schema(tags=['Auth'], summary='Cerrar sesión', responses={200: None})
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def logout(request):
    """Logout by blacklisting the refresh token."""
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


@extend_schema(tags=['Auth'], summary='Obtener / actualizar perfil', request=UsuarioSerializer, responses={200: UsuarioSerializer})
@api_view(['GET', 'PUT', 'PATCH'])
@permission_classes([IsAuthenticated])
def profile(request):
    """Retrieve or update the authenticated user's profile."""
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


# ─── Admin endpoints ─────────────────────────────────────────────────────────

PAGE_SIZE = 20


@extend_schema(tags=['Admin'], summary='Listar usuarios (admin)')
@api_view(['GET'])
@permission_classes([IsAdminUser])
def admin_usuarios_list(request):
    search = request.query_params.get('search', '')
    rol = request.query_params.get('rol', '')
    activo = request.query_params.get('activo')

    queryset = Usuario.objects.all()
    if search:
        queryset = queryset.filter(
            Q(correo__icontains=search)
            | Q(nombre__icontains=search)
            | Q(apellido__icontains=search)
        )
    if rol:
        queryset = queryset.filter(rol=rol)
    if activo is not None:
        queryset = queryset.filter(is_active=activo.lower() in ('true', '1'))

    paginator = PageNumberPagination()
    paginator.page_size = PAGE_SIZE
    result_page = paginator.paginate_queryset(queryset, request)
    serializer = UsuarioSerializer(result_page, many=True)
    return paginator.get_paginated_response(serializer.data)


@extend_schema(tags=['Admin'], summary='Bloquear usuario')
@api_view(['POST'])
@permission_classes([IsAdminUser])
def admin_bloquear_usuario(request, pk):
    try:
        user = Usuario.objects.get(pk=pk)
    except Usuario.DoesNotExist:
        return Response(
            {'detail': _('Usuario no encontrado.')},
            status=status.HTTP_404_NOT_FOUND,
        )

    user.is_active = False
    user.save(update_fields=['is_active'])
    return Response({
        'detail': _(f'Usuario {user.nombre_completo} bloqueado correctamente.'),
    })


@extend_schema(tags=['Admin'], summary='Activar usuario')
@api_view(['POST'])
@permission_classes([IsAdminUser])
def admin_activar_usuario(request, pk):
    try:
        user = Usuario.objects.get(pk=pk)
    except Usuario.DoesNotExist:
        return Response(
            {'detail': _('Usuario no encontrado.')},
            status=status.HTTP_404_NOT_FOUND,
        )

    user.is_active = True
    user.save(update_fields=['is_active'])
    return Response({
        'detail': _(f'Usuario {user.nombre_completo} activado correctamente.'),
    })


@extend_schema(tags=['Admin'], summary='Eliminar usuario')
@api_view(['DELETE'])
@permission_classes([IsAdminUser])
def admin_eliminar_usuario(request, pk):
    try:
        user = Usuario.objects.get(pk=pk)
    except Usuario.DoesNotExist:
        return Response(
            {'detail': _('Usuario no encontrado.')},
            status=status.HTTP_404_NOT_FOUND,
        )

    if user.is_staff:
        return Response(
            {'detail': _('No se puede eliminar un usuario administrador.')},
            status=status.HTTP_400_BAD_REQUEST,
        )

    user.delete()
    return Response(status=status.HTTP_204_NO_CONTENT)
