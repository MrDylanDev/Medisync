from django.urls import path

from . import views

urlpatterns = [
    path('', views.notificacion_list, name='notificacion-list'),
    path('no-leidas/', views.notificaciones_no_leidas_count, name='notificaciones-no-leidas'),
    path('marcar-leidas/', views.marcar_leidas, name='notificaciones-marcar-leidas'),
    path('<int:pk>/', views.notificacion_detail, name='notificacion-detail'),
]
