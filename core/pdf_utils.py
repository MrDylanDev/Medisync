import io
from datetime import date

from django.conf import settings
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
)
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_RIGHT


def generar_comprobante_cita(cita) -> bytes:
    """
    Generate a PDF appointment receipt for a given Cita.
    Returns the PDF as bytes.
    """
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        topMargin=2*cm,
        bottomMargin=2*cm,
        leftMargin=2*cm,
        rightMargin=2*cm,
    )

    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'CustomTitle', parent=styles['Title'],
        fontSize=18, spaceAfter=6,
        textColor=colors.HexColor('#2c3e50'),
    )
    subtitle_style = ParagraphStyle(
        'Subtitle', parent=styles['Normal'],
        fontSize=10, textColor=colors.gray,
        alignment=TA_CENTER, spaceAfter=20,
    )
    label_style = ParagraphStyle(
        'Label', parent=styles['Normal'],
        fontSize=10, textColor=colors.HexColor('#555'),
    )
    value_style = ParagraphStyle(
        'Value', parent=styles['Normal'],
        fontSize=12, spaceAfter=10,
    )

    elements = []

    elements.append(Paragraph('Medisync', title_style))
    elements.append(Paragraph('Comprobante de Cita', subtitle_style))
    elements.append(Spacer(1, 0.5*cm))

    especialidad = ''
    relacion = cita.medico.especialidades.filter(es_principal=True).first()
    if not relacion:
        relacion = cita.medico.especialidades.first()
    if relacion:
        especialidad = relacion.especialidad.nombre

    data = [
        [Paragraph('<b>Paciente</b>', label_style),
         Paragraph(cita.paciente.usuario.nombre_completo, value_style)],
        [Paragraph('<b>Médico</b>', label_style),
         Paragraph(f'Dr. {cita.medico.usuario.nombre_completo}', value_style)],
        [Paragraph('<b>Especialidad</b>', label_style),
         Paragraph(especialidad or '—', value_style)],
        [Paragraph('<b>Fecha</b>', label_style),
         Paragraph(cita.horario.fecha.strftime('%d/%m/%Y'), value_style)],
        [Paragraph('<b>Horario</b>', label_style),
         Paragraph(f'{cita.horario.hora_inicio.strftime("%H:%M")} — {cita.horario.hora_fin.strftime("%H:%M")}', value_style)],
        [Paragraph('<b>Consultorio</b>', label_style),
         Paragraph(getattr(cita.medico, 'informacion_consultorio', None) or 'No especificado', value_style)],
        [Paragraph('<b>Estado</b>', label_style),
         Paragraph(cita.estado.nombre.capitalize(), value_style)],
    ]

    table = Table(data, colWidths=[4*cm, 10*cm])
    table.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ('LINEBELOW', (0, 0), (-1, -2), 0.5, colors.HexColor('#eee')),
    ]))
    elements.append(table)

    elements.append(Spacer(1, 1*cm))
    elements.append(Paragraph(
        f'Generado el {date.today().strftime("%d/%m/%Y")}',
        ParagraphStyle('Footer', parent=styles['Normal'],
                       fontSize=8, textColor=colors.gray, alignment=TA_RIGHT),
    ))

    doc.build(elements)
    pdf_bytes = buffer.getvalue()
    buffer.close()
    return pdf_bytes
