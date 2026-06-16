from datetime import datetime, timedelta

from django.db import transaction
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination

from .models import Cita, EstadoCita
from .serializers import CitaSerializer

PAGE_SIZE = 20


@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def cita_list(request):
    """
    List citas or book a new appointment.

    GET: Returns paginated list of citas.
        - Regular users see only their own citas (as paciente).
        - Admin/staff users see all citas.
    POST: Books a new appointment (atomic: creates Cita + marks Horario as unavailable).
    """
    if request.method == 'GET':
        if request.user.is_staff:
            queryset = Cita.objects.select_related(
                'paciente', 'medico', 'horario', 'estado'
            ).all()
        else:
            # Regular users see only their own citas
            queryset = Cita.objects.select_related(
                'paciente', 'medico', 'horario', 'estado'
            ).filter(paciente__usuario=request.user)

        paginator = PageNumberPagination()
        paginator.page_size = PAGE_SIZE
        result_page = paginator.paginate_queryset(queryset, request)
        serializer = CitaSerializer(result_page, many=True)
        return paginator.get_paginated_response(serializer.data)

    elif request.method == 'POST':
        return _book_appointment(request)


@api_view(['GET', 'DELETE'])
@permission_classes([IsAuthenticated])
def cita_detail(request, pk):
    """
    Retrieve or delete a cita.

    GET: Returns the cita details.
    DELETE: Deletes the cita (admin only).
    """
    try:
        cita = Cita.objects.select_related(
            'paciente', 'medico', 'horario', 'estado'
        ).get(pk=pk)
    except Cita.DoesNotExist:
        return Response(
            {'detail': _('Cita no encontrada.')},
            status=status.HTTP_404_NOT_FOUND,
        )

    if request.method == 'GET':
        serializer = CitaSerializer(cita)
        return Response(serializer.data)

    elif request.method == 'DELETE':
        if not request.user.is_staff:
            return Response(
                {'detail': _('No tienes permiso para realizar esta acción.')},
                status=status.HTTP_403_FORBIDDEN,
            )
        cita.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def cancelar_cita(request, pk):
    """
    Cancel an appointment (atomic operation).

    Validates that the appointment is at least 24 hours in the future.
    Updates Cita estado to 'cancelada' and sets Horario.disponible=True.
    """
    try:
        cita = Cita.objects.select_related('horario', 'estado').get(pk=pk)
    except Cita.DoesNotExist:
        return Response(
            {'detail': _('Cita no encontrada.')},
            status=status.HTTP_404_NOT_FOUND,
        )

    # Check 24-hour cancellation window
    cita_datetime = datetime.combine(cita.horario.fecha, cita.horario.hora_inicio)
    cita_datetime = timezone.make_aware(cita_datetime) if timezone.is_naive(cita_datetime) else cita_datetime
    now = timezone.now()

    if cita_datetime - now < timedelta(hours=24):
        return Response(
            {'detail': _('No se puede cancelar la cita con menos de 24 horas de anticipación.')},
            status=status.HTTP_400_BAD_REQUEST,
        )

    # Perform atomic cancellation
    with transaction.atomic():
        cancelada = EstadoCita.objects.get(nombre='cancelada')
        cita.estado = cancelada
        cita.save(update_fields=['estado'])

        cita.horario.disponible = True
        cita.horario.save(update_fields=['disponible'])

    serializer = CitaSerializer(cita)
    return Response(serializer.data, status=status.HTTP_200_OK)


def _book_appointment(request):
    """
    Book an appointment (atomic operation).

    Creates a Cita and sets Horario.disponible=False in a single
    database transaction to prevent race conditions.
    """
    serializer = CitaSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    with transaction.atomic():
        cita = serializer.save()

        # Mark the horario as unavailable
        horario = cita.horario
        horario.disponible = False
        horario.save(update_fields=['disponible'])

    # Return with estado_nombre populated
    result_serializer = CitaSerializer(cita)
    return Response(result_serializer.data, status=status.HTTP_201_CREATED)
