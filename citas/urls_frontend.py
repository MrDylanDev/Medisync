from django.urls import path

from . import views_frontend

app_name = 'citas'

urlpatterns = [
    path('agendar/', views_frontend.agendar, name='agendar'),
    path('mis-citas/', views_frontend.mis_citas, name='mis_citas'),
    path('<int:pk>/cancelar/', views_frontend.cancelar, name='cancelar'),
]
