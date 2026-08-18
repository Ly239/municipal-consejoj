"""
Comando para crear los grupos del sistema y asignar permisos según cada rol.
Roles: Superadmin, Administrator, Employee, ContentManager, Viewer.
"""
from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group, Permission
from common.constants import (
    GROUP_SUPERADMIN,
    GROUP_ADMINISTRATOR,
    GROUP_EMPLOYEE,
    GROUP_CONTENT_MANAGER,
    GROUP_VIEWER,
)


class Command(BaseCommand):
    help = 'Crea los grupos del sistema y asigna permisos'

    def handle(self, *args, **options):
        self.stdout.write('🚀 Creando grupos del sistema...')
        self.create_groups()
        self.assign_permissions()
        self.stdout.write(self.style.SUCCESS('✅ Grupos creados y permisos asignados'))

    def create_groups(self):
        """Crea los 5 grupos principales del sistema."""
        groups = [
            {'name': GROUP_SUPERADMIN, 'desc': 'Superadministrador - Desarrollo'},
            {'name': GROUP_ADMINISTRATOR, 'desc': 'Administrador - Jefe de Secretaría'},
            {'name': GROUP_EMPLOYEE, 'desc': 'Empleado - Personal de Secretaría'},
            {'name': GROUP_CONTENT_MANAGER, 'desc': 'Gestor de Contenido - Home'},
            {'name': GROUP_VIEWER, 'desc': 'Visualizador - Usuario registrado'},
        ]

        for group_data in groups:
            group, created = Group.objects.get_or_create(name=group_data['name'])
            if created:
                self.stdout.write(self.style.SUCCESS(f'✅ Grupo "{group_data["name"]}" creado.'))
            else:
                self.stdout.write(self.style.WARNING(f'⚠ Grupo "{group_data["name"]}" ya existe.'))

    def assign_permissions(self):
        """Asigna permisos a cada grupo según su rol."""
        # ------------------------------------------------------------
        # 1. GRUPO EMPLOYEE (Personal de secretaría)
        # ------------------------------------------------------------
        employee_group = Group.objects.get(name=GROUP_EMPLOYEE)
        employee_perms = Permission.objects.filter(
            codename__in=[
                'add_document',          # Puede subir documentos
                'change_document',       # Puede editar los suyos
                'view_document',         # Puede ver documentos
                'view_gazette',          # Puede ver gacetas
                'soft_delete_document',  # ✅ Puede mover a papelera (soft delete)
                # ❌ No tiene 'delete_document' (hard delete)
                # ❌ No tiene 'restore_document'
            ]
        )
        employee_group.permissions.add(*employee_perms)
        self.stdout.write(self.style.SUCCESS(
            f'✅ {GROUP_EMPLOYEE} tiene {employee_group.permissions.count()} permisos.'
        ))

        # ------------------------------------------------------------
        # 2. GRUPO ADMINISTRATOR (Jefe de secretaría)
        # ------------------------------------------------------------
        admin_group = Group.objects.get(name=GROUP_ADMINISTRATOR)
        admin_perms = Permission.objects.filter(
            codename__in=[
                'add_document', 'change_document', 'view_document',
                'delete_document',          # Hard delete
                'soft_delete_document',     # Soft delete (papelera)
                'restore_document',         # Restaurar desde papelera
                'add_gazette', 'change_gazette', 'view_gazette',
                'delete_gazette',           # Hard delete
                'soft_delete_gazette',      # Soft delete (papelera)
                'restore_gazette',          # Restaurar desde papelera
                'view_documenttype',
                'view_issuingentity',
            ]
        )
        admin_group.permissions.add(*admin_perms)
        self.stdout.write(self.style.SUCCESS(
            f'✅ {GROUP_ADMINISTRATOR} tiene {admin_group.permissions.count()} permisos.'
        ))

        # ------------------------------------------------------------
        # 3. GRUPO VIEWER (Solo lectura)
        # ------------------------------------------------------------
        viewer_group = Group.objects.get(name=GROUP_VIEWER)
        viewer_perms = Permission.objects.filter(
            codename__in=[
                'view_document',
                'view_gazette',
            ]
        )
        viewer_group.permissions.add(*viewer_perms)
        self.stdout.write(self.style.SUCCESS(
            f'✅ {GROUP_VIEWER} tiene {viewer_group.permissions.count()} permisos.'
        ))

        # ------------------------------------------------------------
        # 4. GRUPO CONTENT_MANAGER (Gestor de contenido del Home)
        # ------------------------------------------------------------
        content_group = Group.objects.get(name=GROUP_CONTENT_MANAGER)
        # Por ahora sin permisos (se añadirán cuando existan los modelos de core)
        self.stdout.write(self.style.SUCCESS(
            f'✅ {GROUP_CONTENT_MANAGER} pendiente de permisos (modelos de core no creados aún).'
        ))

        # ------------------------------------------------------------
        # 5. GRUPO SUPERADMIN (No necesita permisos específicos)
        # ------------------------------------------------------------
        self.stdout.write(self.style.SUCCESS(
            f'✅ {GROUP_SUPERADMIN} no requiere permisos explícitos (superusuario).'
        ))