import json

from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import render
from django.utils import timezone
from django.views.decorators.http import require_http_methods

from .models import Notificacion


@login_required
def lista(request):
    notificaciones = Notificacion.objects.filter(usuario=request.user).order_by('-creado_en')
    return render(request, 'notificaciones/list.html', {
        'notificaciones': notificaciones,
    })


@login_required
@require_http_methods(["POST"])
def marcar_leidas(request):
    data = json.loads(request.body)
    ids = data.get('ids', [])
    Notificacion.objects.filter(usuario=request.user, id__in=ids).update(leida=True)
    return JsonResponse({'ok': True})


@login_required
def no_leidas_count(request):
    count = Notificacion.objects.filter(usuario=request.user, leida=False).count()
    return JsonResponse({'no_leidas': count})


@login_required
def recientes(request):
    qs = Notificacion.objects.filter(usuario=request.user).order_by('-creado_en')[:5]
    items = []
    for n in qs:
        items.append({
            'id': n.id,
            'titulo': n.titulo,
            'tipo': n.tipo,
            'tipo_display': n.get_tipo_display(),
            'leida': n.leida,
            'creado_en': timezone.localtime(n.creado_en).strftime('%d/%m %H:%M'),
        })
    return JsonResponse(items, safe=False)
