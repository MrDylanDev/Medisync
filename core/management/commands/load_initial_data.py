from django.core.management.base import BaseCommand
from django.core.management import call_command
from django.contrib.auth import get_user_model

Usuario = get_user_model()


class Command(BaseCommand):
    help = 'Load initial data: fixtures (roles, especialidades) and create default admin'

    def add_arguments(self, parser):
        parser.add_argument(
            '--admin-email',
            default='admin@medisync.com',
            help='Email for the default admin user',
        )
        parser.add_argument(
            '--admin-password',
            default='Admin123!',
            help='Password for the default admin user',
        )

    def handle(self, *args, **options):
        admin_email = options['admin_email']
        admin_password = options['admin_password']

        self.stdout.write('Cargando datos iniciales...')

        # Load fixtures
        self.stdout.write('  → Cargando fixtures/initial_data.json')
        call_command('loaddata', 'initial_data', verbosity=0)

        # Create default admin
        if not Usuario.objects.filter(correo=admin_email).exists():
            Usuario.objects.create_superuser(
                correo=admin_email,
                password=admin_password,
                nombre='Admin',
                apellido='Sistema',
            )
            self.stdout.write(
                self.style.SUCCESS(
                    f'  → Admin creado: {admin_email} / {admin_password}'
                )
            )
        else:
            self.stdout.write(f'  → Admin ya existe: {admin_email}')

        self.stdout.write(self.style.SUCCESS('Datos iniciales cargados correctamente.'))
