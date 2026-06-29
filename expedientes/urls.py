from django.urls import path

from . import views

urlpatterns = [
    path('', views.expediente_list, name='expediente-list'),
    path('<int:pk>/', views.expediente_detail, name='expediente-detail'),
]
