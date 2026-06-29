from django.urls import path

from . import views_frontend

app_name = 'expedientes'

urlpatterns = [
    path('', views_frontend.lista, name='lista'),
    path('crear/', views_frontend.crear, name='crear'),
]
