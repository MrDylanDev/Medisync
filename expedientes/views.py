from django.db import transaction
from django.utils.translation import gettext_lazy as _
from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination

from .models import Expediente
from .serializers import ExpedienteSerializer

PAGE_SIZE = 20


@extend_schema(
    tags=['Expedientes'],
    summary='Listar / crear expedientes',
    request=ExpedienteSerializer,
    responses={200: ExpedienteSerializer(many=True), 201: ExpedienteSerializer},
)
@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def expediente_list(request):
    if request.method == 'GET':
        if request.user.is_staff:
            queryset = Expediente.objects.select_related(
                'paciente__usuario', 'medico__usuario', 'cita'
            ).all()
        elif request.user.rol == 'medico':
            queryset = Expediente.objects.select_related(
                'paciente__usuario', 'medico__usuario', 'cita'
            ).filter(medico__usuario=request.user)
        else:
            queryset = Expediente.objects.select_related(
                'paciente__usuario', 'medico__usuario', 'cita'
            ).filter(paciente__usuario=request.user)

        paginator = PageNumberPagination()
        paginator.page_size = PAGE_SIZE
        result_page = paginator.paginate_queryset(queryset, request)
        serializer = ExpedienteSerializer(result_page, many=True)
        return paginator.get_paginated_response(serializer.data)

    elif request.method == 'POST':
        serializer = ExpedienteSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        with transaction.atomic():
            expediente = serializer.save(created_by=request.user)
        result = ExpedienteSerializer(expediente)
        return Response(result.data, status=status.HTTP_201_CREATED)


@extend_schema(
    tags=['Expedientes'],
    summary='Obtener / actualizar / eliminar expediente',
    request=ExpedienteSerializer,
    responses={200: ExpedienteSerializer, 204: None},
)
@api_view(['GET', 'PUT', 'PATCH', 'DELETE'])
@permission_classes([IsAuthenticated])
def expediente_detail(request, pk):
    try:
        expediente = Expediente.objects.select_related(
            'paciente__usuario', 'medico__usuario', 'cita'
        ).get(pk=pk)
    except Expediente.DoesNotExist:
        return Response(
            {'detail': _('Expediente no encontrado.')},
            status=status.HTTP_404_NOT_FOUND,
        )

    can_access = (
        request.user.is_staff
        or expediente.medico.usuario == request.user
        or expediente.paciente.usuario == request.user
    )
    if not can_access:
        return Response(
            {'detail': _('No tienes permiso para acceder a este expediente.')},
            status=status.HTTP_403_FORBIDDEN,
        )

    if request.method == 'GET':
        serializer = ExpedienteSerializer(expediente)
        return Response(serializer.data)

    elif request.method in ('PUT', 'PATCH'):
        if not (request.user.is_staff or expediente.medico.usuario == request.user):
            return Response(
                {'detail': _('Solo el médico o un administrador pueden modificar expedientes.')},
                status=status.HTTP_403_FORBIDDEN,
            )
        serializer = ExpedienteSerializer(
            expediente,
            data=request.data,
            partial=request.method == 'PATCH',
        )
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    elif request.method == 'DELETE':
        if not request.user.is_staff:
            return Response(
                {'detail': _('No tienes permiso para eliminar expedientes.')},
                status=status.HTTP_403_FORBIDDEN,
            )
        expediente.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
