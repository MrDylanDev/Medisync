from django.urls import path

from . import views_frontend

app_name = 'notificaciones'

urlpatterns = [
    path('', views_frontend.lista, name='lista'),
    path('marcar-leidas/', views_frontend.marcar_leidas, name='marcar_leidas'),
    path('api/no-leidas/', views_frontend.no_leidas_count, name='no_leidas_api'),
    path('api/recientes/', views_frontend.recientes, name='recientes_api'),
]
