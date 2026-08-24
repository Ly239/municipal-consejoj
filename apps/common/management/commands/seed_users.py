"""
Comando para crear los usuarios por defecto del sistema.
Crea un usuario para cada rol: Administrator, Employee, ContentManager, Viewer.
"""
from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group
from django.contrib.auth import get_user_model
from common.constants import (
    GROUP_ADMINISTRATOR,
    GROUP_EMPLOYEE,
    GROUP_CONTENT_MANAGER,
    GROUP_VIEWER,
)

User = get_user_model()


class Command(BaseCommand):
    help = 'Crea usuarios por defecto para cada rol del sistema'

    def handle(self, *args, **options):
        self.stdout.write('🚀 Creando usuarios del sistema...')

        # Crear usuarios para cada rol (sin root)
        self.create_user('admin', 'admin456', GROUP_ADMINISTRATOR, 'Admin', 'Secretaría', 'admin@consejo.local', '11111111')
        self.create_user('employee', 'empleado789', GROUP_EMPLOYEE, 'Empleado', 'Secretaría', 'employee@consejo.local', '22222222')
        self.create_user('contentmanager', 'contenido321', GROUP_CONTENT_MANAGER, 'Gestor', 'Contenido', 'content@consejo.local', '33333333')
        self.create_user('viewer', 'visual654', GROUP_VIEWER, 'Visualizador', 'Usuario', 'viewer@consejo.local', '44444444')

        self.stdout.write(self.style.SUCCESS('✅ Todos los usuarios creados exitosamente'))

    def create_user(self, username, password, group_name, first_name, last_name, email, id_number):
        """
        Crea un usuario con el nombre de usuario, contraseña, grupo y datos personales dados.
        Si el usuario ya existe, muestra un mensaje de advertencia.
        """
        # Verificar si el usuario ya existe
        if User.objects.filter(username=username).exists():
            self.stdout.write(self.style.WARNING(f'⚠ Usuario "{username}" ya existe.'))
            return

        # Crear el usuario
        user = User.objects.create_user(
            username=username,
            password=password,
            email=email,
            first_name=first_name,
            last_name=last_name,
            id_number=id_number,
        )

        # Asignar el grupo correspondiente
        group = Group.objects.get(name=group_name)
        user.groups.add(group)

        self.stdout.write(self.style.SUCCESS(
            f'✅ Usuario "{username}" creado (contraseña: {password}, rol: {group_name})'
        ))