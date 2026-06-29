from datetime import datetime, timedelta

from django.db import transaction
from django.http import HttpResponse
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from drf_spectacular.utils import extend_schema, OpenApiParameter, inline_serializer
from rest_framework import serializers, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination

from core.utils import send_template_email
from core.pdf_utils import generar_comprobante_cita
from .models import Cita, EstadoCita
from .serializers import CitaSerializer

PAGE_SIZE = 20


@extend_schema(
    tags=['Citas'],
    summary='Listar / agendar citas',
    request=CitaSerializer,
    responses={200: CitaSerializer(many=True), 201: CitaSerializer},
)
@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def cita_list(request):
    """List citas or book a new appointment."""
    if request.method == 'GET':
        if request.user.is_staff:
            queryset = Cita.objects.select_related(
                'paciente', 'medico', 'horario', 'estado'
            ).all()
        else:
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


@extend_schema(
    tags=['Citas'],
    summary='Obtener / reprogramar / eliminar cita',
    responses={200: CitaSerializer, 204: None},
)
@api_view(['GET', 'PUT', 'DELETE'])
@permission_classes([IsAuthenticated])
def cita_detail(request, pk):
    """Retrieve, reschedule or delete a cita."""
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

    elif request.method == 'PUT':
        can_edit = (
            request.user.is_staff
            or cita.paciente.usuario == request.user
        )
        if not can_edit:
            return Response(
                {'detail': _('No tienes permiso para modificar esta cita.')},
                status=status.HTTP_403_FORBIDDEN,
            )

        if cita.estado.nombre not in ('pendiente', 'confirmada'):
            return Response(
                {'detail': _('Solo se pueden reprogramar citas pendientes o confirmadas.')},
                status=status.HTTP_400_BAD_REQUEST,
            )

        serializer = CitaSerializer(cita, data=request.data, partial=True)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        from datetime import datetime
        with transaction.atomic():
            old_horario = cita.horario
            nueva_cita = serializer.save()

            if nueva_cita.horario != old_horario:
                old_horario.disponible = True
                old_horario.save(update_fields=['disponible'])
                nueva_cita.horario.disponible = False
                nueva_cita.horario.save(update_fields=['disponible'])

        result = CitaSerializer(nueva_cita)
        return Response(result.data)

    elif request.method == 'DELETE':
        if not request.user.is_staff:
            return Response(
                {'detail': _('No tienes permiso para realizar esta acción.')},
                status=status.HTTP_403_FORBIDDEN,
            )
        cita.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


@extend_schema(
    tags=['Citas'],
    summary='Cancelar cita',
    responses={200: CitaSerializer, 400: None},
)
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def cancelar_cita(request, pk):
    """Cancel an appointment (atomic operation)."""
    try:
        cita = Cita.objects.select_related(
            'horario', 'estado', 'paciente__usuario', 'medico__usuario'
        ).get(pk=pk)
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

    # Determine quien cancela
    if request.user.is_staff:
        cancelador = 'admin'
    elif request.user.rol == 'medico':
        cancelador = 'medico'
    else:
        cancelador = 'paciente'

    # Perform atomic cancellation
    with transaction.atomic():
        cancelada = EstadoCita.objects.get(nombre='cancelada')
        cita.estado = cancelada
        cita.cancelada_por = cancelador
        cita.fecha_cancelacion = timezone.now()
        cita.save(update_fields=['estado', 'cancelada_por', 'fecha_cancelacion'])

        cita.horario.disponible = True
        cita.horario.save(update_fields=['disponible'])

    serializer = CitaSerializer(cita)

    _send_appointment_cancelled(cita, request.user)

    return Response(serializer.data, status=status.HTTP_200_OK)


def _book_appointment(request):
    """
    Book an appointment (atomic operation).

    Creates a Cita and sets Horario.disponible=False in a single
    database transaction to prevent race conditions.
    Sends a confirmation email to the patient.
    """
    serializer = CitaSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    with transaction.atomic():
        cita = serializer.save()

        horario = cita.horario
        horario.disponible = False
        horario.save(update_fields=['disponible'])

    result_serializer = CitaSerializer(cita)

    _send_appointment_confirmed(cita)

    return Response(result_serializer.data, status=status.HTTP_201_CREATED)


# ─── Email helpers ────────────────────────────────────────────────────────────

def _get_especialidad(medico):
    """Get the primary especialidad name for a medico, or empty string."""
    relacion = medico.especialidades.filter(es_principal=True).first()
    if not relacion:
        relacion = medico.especialidades.first()
    return relacion.especialidad.nombre if relacion else ''


def _send_appointment_confirmed(cita):
    """Send confirmation email to the patient."""
    especialidad = _get_especialidad(cita.medico)

    context = {
        'paciente_nombre': cita.paciente.usuario.nombre_completo,
        'medico_nombre': f'Dr. {cita.medico.usuario.nombre_completo}',
        'especialidad': especialidad,
        'fecha': cita.horario.fecha.strftime('%d/%m/%Y'),
        'hora_inicio': cita.horario.hora_inicio.strftime('%H:%M'),
        'hora_fin': cita.horario.hora_fin.strftime('%H:%M'),
        'consultorio': cita.medico.informacion_consultorio or 'No especificado',
        'atencion_online': cita.medico.atencion_online,
        'motivo': cita.motivo,
    }

    send_template_email(
        subject='Cita confirmada — Medisync',
        template_name='emails/appointment_confirmed.html',
        context=context,
        recipient_list=[cita.paciente.usuario.correo],
    )


def _send_appointment_cancelled(cita, cancelled_by):
    """Send cancellation emails to patient and doctor."""
    especialidad = _get_especialidad(cita.medico)

    context = {
        'paciente_nombre': cita.paciente.usuario.nombre_completo,
        'medico_nombre': f'Dr. {cita.medico.usuario.nombre_completo}',
        'especialidad': especialidad,
        'fecha': cita.horario.fecha.strftime('%d/%m/%Y'),
        'hora_inicio': cita.horario.hora_inicio.strftime('%H:%M'),
        'hora_fin': cita.horario.hora_fin.strftime('%H:%M'),
        'cancelada_por': cancelled_by.nombre_completo,
    }

    send_template_email(
        subject='Cita cancelada — Medisync',
        template_name='emails/appointment_cancelled.html',
        context=context,
        recipient_list=[cita.paciente.usuario.correo],
    )
    send_template_email(
        subject='Cita cancelada — Medisync',
        template_name='emails/appointment_cancelled.html',
        context=context,
        recipient_list=[cita.medico.usuario.correo],
    )


@extend_schema(
    tags=['Citas'],
    summary='Descargar comprobante PDF',
    responses={200: None, 404: None},
)
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def comprobante_pdf(request, pk):
    """Download a PDF receipt for an appointment."""
    try:
        cita = Cita.objects.select_related(
            'paciente__usuario', 'medico__usuario',
            'horario', 'estado',
        ).get(pk=pk)
    except Cita.DoesNotExist:
        return Response(
            {'detail': _('Cita no encontrada.')},
            status=status.HTTP_404_NOT_FOUND,
        )

    can_access = (
        request.user.is_staff
        or cita.paciente.usuario == request.user
        or cita.medico.usuario == request.user
    )
    if not can_access:
        return Response(
            {'detail': _('No tienes permiso para acceder a este comprobante.')},
            status=status.HTTP_403_FORBIDDEN,
        )

    pdf_bytes = generar_comprobante_cita(cita)
    filename = f'comprobante_cita_{pk}.pdf'

    return HttpResponse(pdf_bytes, content_type='application/pdf', headers={
        'Content-Disposition': f'attachment; filename="{filename}"',
    })
