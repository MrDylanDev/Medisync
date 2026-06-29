from datetime import datetime, time as time_type, timedelta

from django.db import IntegrityError
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

@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def disponibilidad(request, pk):
    """
    Search or create time slots for a medico.

    GET: Returns disponible=True slots for a given fecha.
        Query params: fecha (required, YYYY-MM-DD).

    POST: Creates one or more slots.
        Single slot: { "fecha", "hora_inicio", "hora_fin" }
        Batch:       { "fecha", "hora_inicio", "hora_fin", "duracion_slot": 15|20|30 }
    """
    try:
        medico = Medico.objects.select_related('usuario').get(pk=pk)
    except Medico.DoesNotExist:
        return Response(
            {'detail': _('Médico no encontrado.')},
            status=status.HTTP_404_NOT_FOUND,
        )

    if request.method == 'GET':
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

        horarios = Horario.objects.filter(
            medico=medico, fecha=fecha, disponible=True,
        ).order_by('hora_inicio')
        serializer = HorarioSerializer(horarios, many=True)
        return Response(serializer.data)

    elif request.method == 'POST':
        if not _es_medico_propietario_o_admin(request.user, medico):
            return Response(
                {'detail': _('No tienes permiso para gestionar este horario.')},
                status=status.HTTP_403_FORBIDDEN,
            )

        fecha_str = request.data.get('fecha')
        hora_inicio_str = request.data.get('hora_inicio')
        hora_fin_str = request.data.get('hora_fin')
        duracion = request.data.get('duracion_slot')

        errors = {}
        if not fecha_str:
            errors['fecha'] = 'Requerido.'
        if not hora_inicio_str:
            errors['hora_inicio'] = 'Requerido.'
        if not hora_fin_str:
            errors['hora_fin'] = 'Requerido.'

        if errors:
            return Response(errors, status=status.HTTP_400_BAD_REQUEST)

        try:
            fecha = datetime.strptime(fecha_str, '%Y-%m-%d').date()
        except ValueError:
            return Response({'fecha': 'Formato inválido. Use YYYY-MM-DD.'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            hora_inicio = datetime.strptime(hora_inicio_str, '%H:%M').time()
            hora_fin = datetime.strptime(hora_fin_str, '%H:%M').time()
        except ValueError:
            return Response(
                {'hora_inicio': 'Formato inválido. Use HH:MM.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if hora_fin <= hora_inicio:
            return Response(
                {'hora_fin': 'Debe ser posterior a hora_inicio.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if duracion:
            try:
                duracion = int(duracion)
            except (TypeError, ValueError):
                return Response(
                    {'duracion_slot': 'Debe ser un número (15, 20 o 30).'},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            if duracion not in (15, 20, 30):
                return Response(
                    {'duracion_slot': 'Debe ser 15, 20 o 30 minutos.'},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            slots_creados = _crear_slots(medico, fecha, hora_inicio, hora_fin, duracion)
            serializer = HorarioSerializer(slots_creados, many=True)
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        serializer = HorarioSerializer(data={
            'medico': medico.id, 'fecha': fecha_str,
            'hora_inicio': hora_inicio_str, 'hora_fin': hora_fin_str,
        })
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        try:
            serializer.save()
        except IntegrityError:
            return Response(
                {'detail': _('Ya existe un horario idéntico.')},
                status=status.HTTP_409_CONFLICT,
            )
        return Response(serializer.data, status=status.HTTP_201_CREATED)


@api_view(['PUT', 'PATCH', 'DELETE'])
@permission_classes([IsAuthenticated])
def disponibilidad_detalle(request, pk, id_disp):
    """Update or delete a specific time slot."""
    try:
        medico = Medico.objects.select_related('usuario').get(pk=pk)
    except Medico.DoesNotExist:
        return Response({'detail': _('Médico no encontrado.')}, status=status.HTTP_404_NOT_FOUND)

    if not _es_medico_propietario_o_admin(request.user, medico):
        return Response(
            {'detail': _('No tienes permiso para gestionar este horario.')},
            status=status.HTTP_403_FORBIDDEN,
        )

    try:
        horario = Horario.objects.get(pk=id_disp, medico=medico)
    except Horario.DoesNotExist:
        return Response({'detail': _('Horario no encontrado.')}, status=status.HTTP_404_NOT_FOUND)

    if request.method == 'DELETE':
        horario.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    partial = request.method == 'PATCH'
    serializer = HorarioSerializer(horario, data=request.data, partial=partial)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    try:
        serializer.save()
    except IntegrityError:
        return Response(
            {'detail': _('El cambio genera un conflicto con otro horario existente.')},
            status=status.HTTP_409_CONFLICT,
        )
    return Response(serializer.data)


# ─── Helpers ─────────────────────────────────────────────────────────────────

def _es_medico_propietario_o_admin(user, medico):
    """Check if user is the medico itself or an admin."""
    if user.is_staff:
        return True
    try:
        return user.medico_datos == medico
    except Medico.DoesNotExist:
        return False


def _crear_slots(medico, fecha, hora_inicio, hora_fin, duracion_minutos):
    """Divide a time range into slots and create them."""
    start = datetime.combine(fecha, hora_inicio)
    end = datetime.combine(fecha, hora_fin)
    delta = timedelta(minutes=duracion_minutos)
    creados = []

    current = start
    while current + delta <= end:
        slot_inicio = current.time()
        slot_fin = (current + delta).time()

        _, created = Horario.objects.get_or_create(
            medico=medico,
            fecha=fecha,
            hora_inicio=slot_inicio,
            hora_fin=slot_fin,
            defaults={'disponible': True},
        )
        if created:
            creados.append(_.id)
        current += delta

    return Horario.objects.filter(id__in=creados).order_by('hora_inicio')
