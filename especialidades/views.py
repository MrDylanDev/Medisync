from django.utils.translation import gettext_lazy as _
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination

from .models import Especialidad
from .serializers import EspecialidadSerializer

PAGE_SIZE = 20


@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def especialidad_list(request):
    """
    List all especialidades or create a new one.

    GET: Returns paginated list (requires authentication).
    POST: Creates a new especialidad (admin only).
    """
    if request.method == 'GET':
        queryset = Especialidad.objects.all()
        activo = request.query_params.get('activo')
        if activo is not None:
            queryset = queryset.filter(activo=activo.lower() in ('true', '1', 'yes'))

        paginator = PageNumberPagination()
        paginator.page_size = PAGE_SIZE
        result_page = paginator.paginate_queryset(queryset, request)
        serializer = EspecialidadSerializer(result_page, many=True)
        return paginator.get_paginated_response(serializer.data)

    elif request.method == 'POST':
        if not request.user.is_staff:
            return Response(
                {'detail': _('No tienes permiso para realizar esta acción.')},
                status=status.HTTP_403_FORBIDDEN,
            )
        serializer = EspecialidadSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET', 'PUT', 'PATCH', 'DELETE'])
@permission_classes([IsAuthenticated])
def especialidad_detail(request, pk):
    """
    Retrieve, update or delete an especialidad.

    GET: Returns the especialidad (requires authentication).
    PUT/PATCH: Updates the especialidad (admin only).
    DELETE: Deletes the especialidad (admin only).
    """
    try:
        especialidad = Especialidad.objects.get(pk=pk)
    except Especialidad.DoesNotExist:
        return Response(
            {'detail': _('No encontrado.')},
            status=status.HTTP_404_NOT_FOUND,
        )

    if request.method == 'GET':
        serializer = EspecialidadSerializer(especialidad)
        return Response(serializer.data)

    elif request.method in ('PUT', 'PATCH'):
        if not request.user.is_staff:
            return Response(
                {'detail': _('No tienes permiso para realizar esta acción.')},
                status=status.HTTP_403_FORBIDDEN,
            )
        partial = request.method == 'PATCH'
        serializer = EspecialidadSerializer(
            especialidad, data=request.data, partial=partial,
        )
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    elif request.method == 'DELETE':
        if not request.user.is_staff:
            return Response(
                {'detail': _('No tienes permiso para realizar esta acción.')},
                status=status.HTTP_403_FORBIDDEN,
            )
        especialidad.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
