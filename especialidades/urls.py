from django.urls import path

from . import views

urlpatterns = [
    path('', views.especialidad_list, name='especialidad-list'),
    path('<int:pk>/', views.especialidad_detail, name='especialidad-detail'),
]
