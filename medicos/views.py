from datetime import datetime

from django.utils.translation import gettext_lazy as _
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination

from .models import Medico, Horario
from .serializers import MedicoSerializer, HorarioSerializer

PAGE_SIZE = 20


# ─── Medico CRUD ──────────────────────────────────────────────────────────────

@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def medico_list(request):
    """
    List all medicos or create a new one.

    GET: Returns paginated list of medicos (requires authentication).
    POST: Creates a new medico (admin only).
    """
    if request.method == 'GET':
        queryset = Medico.objects.select_related('usuario').all()
        paginator = PageNumberPagination()
        paginator.page_size = PAGE_SIZE
        result_page = paginator.paginate_queryset(queryset, request)
        serializer = MedicoSerializer(result_page, many=True)
        return paginator.get_paginated_response(serializer.data)

    elif request.method == 'POST':
        if not request.user.is_staff:
            return Response(
                {'detail': _('No tienes permiso para realizar esta acción.')},
                status=status.HTTP_403_FORBIDDEN,
            )
        serializer = MedicoSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET', 'PUT', 'PATCH', 'DELETE'])
@permission_classes([IsAuthenticated])
def medico_detail(request, pk):
    """
    Retrieve, update or delete a medico.

    GET: Returns the medico.
    PUT/PATCH: Updates the medico (admin only).
    DELETE: Deletes the medico (admin only).
    """
    try:
        medico = Medico.objects.select_related('usuario').get(pk=pk)
    except Medico.DoesNotExist:
        return Response(
            {'detail': _('No encontrado.')},
            status=status.HTTP_404_NOT_FOUND,
        )

    if request.method == 'GET':
        serializer = MedicoSerializer(medico)
        return Response(serializer.data)

    elif request.method in ('PUT', 'PATCH'):
        if not request.user.is_staff:
            return Response(
                {'detail': _('No tienes permiso para realizar esta acción.')},
                status=status.HTTP_403_FORBIDDEN,
            )
        partial = request.method == 'PATCH'
        serializer = MedicoSerializer(medico, data=request.data, partial=partial)
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
        medico.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


# ─── Disponibilidad (Available Slots) ───────────────────────────────────────

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def disponibilidad(request, pk):
    """
    Search available time slots for a medico.

    Query params:
        fecha (required): Date in YYYY-MM-DD format.
        especialidad (optional): Especialidad ID to filter by.

    Returns only disponible=True slots.
    """
    fecha_str = request.query_params.get('fecha')
    if not fecha_str:
        return Response(
            {'detail': _('El parámetro "fecha" es obligatorio (YYYY-MM-DD).')},
            status=status.HTTP_400_BAD_REQUEST,
        )

    try:
        fecha = datetime.strptime(fecha_str, '%Y-%m-%d').date()
    except ValueError:
        return Response(
            {'detail': _('Formato de fecha inválido. Use YYYY-MM-DD.')},
            status=status.HTTP_400_BAD_REQUEST,
        )

    try:
        medico = Medico.objects.get(pk=pk)
    except Medico.DoesNotExist:
        return Response(
            {'detail': _('Médico no encontrado.')},
            status=status.HTTP_404_NOT_FOUND,
        )

    horarios = Horario.objects.filter(
        medico=medico,
        fecha=fecha,
        disponible=True,
    ).order_by('hora_inicio')

    serializer = HorarioSerializer(horarios, many=True)
    return Response(serializer.data, status=status.HTTP_200_OK)
