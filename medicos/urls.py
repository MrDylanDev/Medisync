from django.urls import path

from . import views

urlpatterns = [
    path('', views.medico_list, name='medico-list'),
    path('<int:pk>/', views.medico_detail, name='medico-detail'),
    path('<int:pk>/disponibilidad/', views.disponibilidad, name='medico-disponibilidad'),
    path('<int:pk>/disponibilidad/<int:id_disp>/', views.disponibilidad_detalle, name='medico-disponibilidad-detalle'),
]
