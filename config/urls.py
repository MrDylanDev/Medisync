from django.contrib import admin
from django.contrib.auth import views as auth_views
from django.urls import path, include, reverse_lazy

from accounts import views_frontend
from accounts.forms import EmailAuthenticationForm
from core import views as core_views
from especialidades import views_public as especialidades_public
from medicos import views_public as medicos_public

urlpatterns = [
    # Admin
    path('admin/', admin.site.urls),

    # Home
    path('', core_views.home, name='home'),

    # Frontend — session-based auth
    path('accounts/login/', auth_views.LoginView.as_view(
        template_name='accounts/login.html',
        authentication_form=EmailAuthenticationForm,
        redirect_authenticated_user=True,
    ), name='login'),
    path('accounts/logout/', auth_views.LogoutView.as_view(
        next_page='login',
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

    # Public landing pages
    path('especialidades/', especialidades_public.especialidad_list, name='especialidades_list'),
    path('medicos/', medicos_public.medico_list, name='medicos_list'),
    path('medicos/<int:pk>/', medicos_public.medico_detail, name='medicos_detail'),

    # API — JWT-based auth
    path('api/auth/', include('accounts.urls')),
    path('api/especialidades/', include('especialidades.urls')),
    path('api/medicos/', include('medicos.urls')),
    path('api/citas/', include('citas.urls')),
]
