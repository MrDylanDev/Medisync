from django.urls import path

from . import views_frontend

app_name = 'medicos'

urlpatterns = [
    path('mis-horarios/', views_frontend.mis_horarios, name='mis_horarios'),
    path('agregar-horario/', views_frontend.agregar_horario, name='agregar_horario'),
    path('eliminar-horario/<int:pk>/', views_frontend.eliminar_horario, name='eliminar_horario'),
    path('citas-agendadas/', views_frontend.citas_agendadas, name='citas_agendadas'),
    path('citas/<int:pk>/realizada/', views_frontend.marcar_realizada, name='marcar_realizada'),
    path('citas/<int:pk>/no-asistio/', views_frontend.marcar_no_asistio, name='marcar_no_asistio'),
]
