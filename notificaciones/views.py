from django.utils.translation import gettext_lazy as _
from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination

from .models import Notificacion
from .serializers import NotificacionSerializer, NotificacionMarcarLeidaSerializer

PAGE_SIZE = 20


@extend_schema(
    tags=['Notificaciones'],
    summary='Listar / crear notificaciones',
    request=NotificacionSerializer,
    responses={200: NotificacionSerializer(many=True)},
)
@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def notificacion_list(request):
    if request.method == 'GET':
        queryset = Notificacion.objects.filter(usuario=request.user)
        paginator = PageNumberPagination()
        paginator.page_size = PAGE_SIZE
        result_page = paginator.paginate_queryset(queryset, request)
        serializer = NotificacionSerializer(result_page, many=True)
        return paginator.get_paginated_response(serializer.data)

    elif request.method == 'POST':
        serializer = NotificacionSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        notificacion = serializer.save()
        result = NotificacionSerializer(notificacion)
        return Response(result.data, status=status.HTTP_201_CREATED)


@extend_schema(
    tags=['Notificaciones'],
    summary='Obtener / eliminar notificación',
    responses={200: NotificacionSerializer, 204: None},
)
@api_view(['GET', 'DELETE'])
@permission_classes([IsAuthenticated])
def notificacion_detail(request, pk):
    try:
        notificacion = Notificacion.objects.get(pk=pk, usuario=request.user)
    except Notificacion.DoesNotExist:
        return Response(
            {'detail': _('Notificación no encontrada.')},
            status=status.HTTP_404_NOT_FOUND,
        )

    if request.method == 'GET':
        serializer = NotificacionSerializer(notificacion)
        return Response(serializer.data)

    elif request.method == 'DELETE':
        notificacion.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


@extend_schema(
    tags=['Notificaciones'],
    summary='Marcar notificaciones como leídas',
    request=NotificacionMarcarLeidaSerializer,
    responses={200: None},
)
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def marcar_leidas(request):
    serializer = NotificacionMarcarLeidaSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    updated = Notificacion.objects.filter(
        usuario=request.user,
        id__in=serializer.validated_data['ids'],
    ).update(leida=True)

    return Response({
        'detail': _(f'{updated} notificaciones marcadas como leídas.'),
        'actualizadas': updated,
    })


@extend_schema(
    tags=['Notificaciones'],
    summary='Contar notificaciones no leídas',
    responses={200: None},
)
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def notificaciones_no_leidas_count(request):
    count = Notificacion.objects.filter(usuario=request.user, leida=False).count()
    return Response({'no_leidas': count})
