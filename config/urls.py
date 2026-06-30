from django.contrib import admin
from django.contrib.auth import views as auth_views
from django.urls import path, include, reverse_lazy

from accounts import views as accounts_views
from citas import views as citas_views
from accounts import views_frontend
from accounts.forms import EmailAuthenticationForm
from core import views as core_views
from core import views_reports
from especialidades import views_public as especialidades_public
from medicos import views_public as medicos_public

urlpatterns = [
    # Admin
    path('admin/', admin.site.urls),

    # Home
    path('', core_views.home, name='home'),

    # Frontend — session-based auth (GET redirects to home, POST handled by modal)
    path('accounts/login/', views_frontend.login_modal, name='login'),
    path('accounts/logout/', auth_views.LogoutView.as_view(
        next_page='home',
    ), name='logout'),
    path('accounts/register/', views_frontend.register, name='register'),
    path('accounts/profile/', views_frontend.profile, name='profile'),
    path('accounts/password-reset/', auth_views.PasswordResetView.as_view(
        template_name='accounts/password_reset.html',
        email_template_name='emails/password_reset.html',
        subject_template_name='emails/password_reset_subject.txt',
        success_url=reverse_lazy('password_reset_done'),
    ), name='password_reset'),
    path('accounts/password-reset/done/', auth_views.PasswordResetDoneView.as_view(
        template_name='accounts/password_reset_done.html',
    ), name='password_reset_done'),
    path('accounts/reset/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(
        template_name='accounts/password_reset_confirm.html',
        success_url=reverse_lazy('password_reset_complete'),
    ), name='password_reset_confirm'),
    path('accounts/reset/done/', auth_views.PasswordResetCompleteView.as_view(
        template_name='accounts/password_reset_complete.html',
    ), name='password_reset_complete'),

    # Dashboard
    path('dashboard/', views_frontend.dashboard, name='dashboard'),

    # Frontend — citas
    path('citas/', include('citas.urls_frontend')),

    # Frontend — médicos
    path('medicos/', include('medicos.urls_frontend')),

    # Frontend — expedientes
    path('expedientes/', include('expedientes.urls_frontend')),

    # Frontend — notificaciones
    path('notificaciones/', include('notificaciones.urls_frontend')),

    # Frontend — admin usuarios (nota: evitar /admin/ porque lo captura el admin de Django)
    path('dashboard/usuarios/', views_frontend.admin_usuarios, name='admin-usuarios'),
    path('dashboard/usuarios/<int:pk>/bloquear/', views_frontend.admin_bloquear_usuario_frontend, name='admin-usuario-bloquear-frontend'),
    path('dashboard/usuarios/<int:pk>/activar/', views_frontend.admin_activar_usuario_frontend, name='admin-usuario-activar-frontend'),
    path('dashboard/usuarios/<int:pk>/eliminar/', views_frontend.admin_eliminar_usuario_frontend, name='admin-usuario-eliminar-frontend'),

    # Frontend — reportes
    path('reportes/', views_reports.reportes, name='reportes'),

    # API — reportes
    path('api/reportes/', views_reports.reportes_api, name='reportes-api'),

    # Public landing pages
    path('especialidades/', especialidades_public.especialidad_list, name='especialidades_list'),
    path('medicos/', medicos_public.medico_list, name='medicos_list'),
    path('medicos/<int:pk>/', medicos_public.medico_detail, name='medicos_detail'),

    # API — JWT-based auth
    path('api/auth/', include('accounts.urls')),
    path('api/especialidades/', include('especialidades.urls')),
    path('api/medicos/', include('medicos.urls')),
    path('api/citas/', include('citas.urls')),

    # API — expedientes
    path('api/expedientes/', include('expedientes.urls')),

    # API — notificaciones
    path('api/notificaciones/', include('notificaciones.urls')),

    # API — admin
    path('api/admin/usuarios/', accounts_views.admin_usuarios_list, name='admin-usuarios-list'),
    path('api/admin/usuarios/<int:pk>/bloquear/', accounts_views.admin_bloquear_usuario, name='admin-usuario-bloquear'),
    path('api/admin/usuarios/<int:pk>/activar/', accounts_views.admin_activar_usuario, name='admin-usuario-activar'),
    path('api/admin/usuarios/<int:pk>/eliminar/', accounts_views.admin_eliminar_usuario, name='admin-usuario-eliminar'),

    # PDF comprobante
    path('api/citas/<int:pk>/comprobante/', citas_views.comprobante_pdf),


    # API — Swagger
    path('api/schema/', include('core.urls_swagger')),
]
