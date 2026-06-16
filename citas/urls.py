from django.urls import path

from . import views

urlpatterns = [
    path('', views.cita_list, name='cita-list'),
    path('<int:pk>/', views.cita_detail, name='cita-detail'),
    path('<int:pk>/cancelar/', views.cancelar_cita, name='cita-cancelar'),
]
