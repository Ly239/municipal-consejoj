"""
Comando maestro que ejecuta todos los seeders en el orden correcto.
"""
from django.core.management.base import BaseCommand
from django.core.management import call_command


class Command(BaseCommand):
    help = 'Ejecuta todos los seeders en orden'

    def handle(self, *args, **options):
        self.stdout.write('🚀 Iniciando carga de datos iniciales...')

        # Orden correcto (respetando dependencias)
        call_command('seed_basic_data')   # 1. Tipos de documento y entes emisores
        call_command('seed_permissions')  # 2. Permisos de soft delete y restore
        call_command('seed_roles')        # 3. Grupos (Superadmin, Admin, Employee, etc.)
        call_command('seed_users')        # 4. Usuarios por defecto

        self.stdout.write(self.style.SUCCESS('🎉 Todos los seeders ejecutados correctamente'))