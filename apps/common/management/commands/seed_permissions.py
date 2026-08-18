"""
Comando para crear permisos de soft delete y restore 
para todos los modelos que heredan de SoftDeleteMixin.
"""
from django.core.management.base import BaseCommand
from django.apps import apps
from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType


class Command(BaseCommand):
    help = 'Crea permisos de soft delete y restore para modelos con SoftDeleteMixin'

    def handle(self, *args, **options):
        self.stdout.write(self.style.MIGRATE_HEADING('Iniciando creación de permisos de Soft Delete...'))
        self.create_softdelete_permissions()

    def create_softdelete_permissions(self):
        """Crea permisos de soft delete y restore para modelos que heredan de SoftDeleteMixin."""
        softdelete_models = self.get_softdelete_models()

        if not softdelete_models:
            self.stdout.write(self.style.WARNING('No se encontraron modelos con SoftDeleteMixin'))
            return

        self.stdout.write(self.style.SUCCESS(f'Encontrados {len(softdelete_models)} modelos con SoftDeleteMixin:'))
        for model in softdelete_models:
            self.stdout.write(f'   • {model._meta.label}')

        total_created = 0
        for model in softdelete_models:
            created = self.create_model_permissions(model)
            total_created += created
            if created > 0:
                self.stdout.write(self.style.SUCCESS(f'Permisos creados para: {model._meta.model_name}'))
            else:
                self.stdout.write(self.style.WARNING(f'Permisos ya existían para: {model._meta.model_name}'))

        self.stdout.write(self.style.SUCCESS(f'Proceso completado. Total de permisos creados: {total_created}'))

    def get_softdelete_models(self):
        """Obtiene todos los modelos que heredan de SoftDeleteMixin."""
        softdelete_models = []
        for model in apps.get_models():
            if self.is_softdelete_model(model):
                softdelete_models.append(model)
        return softdelete_models

    def is_softdelete_model(self, model):
        """Verifica si un modelo hereda de SoftDeleteMixin."""
        for base in model.__mro__:
            if base.__name__ == 'SoftDeleteMixin' and hasattr(model, '_meta'):
                return True
        return False

    def create_model_permissions(self, model):
        """
        Crea los permisos soft_delete_<model> y restore_<model> para un modelo.
        Retorna cuántos permisos creó (0 o 2).
        """
        content_type = ContentType.objects.get_for_model(model)
        model_name = model._meta.model_name
        created_count = 0

        # Permiso: soft_delete
        perm, created = Permission.objects.get_or_create(
            codename=f'soft_delete_{model_name}',
            content_type=content_type,
            defaults={'name': f'Can soft delete {model_name}'}
        )
        if created:
            created_count += 1

        # Permiso: restore
        perm, created = Permission.objects.get_or_create(
            codename=f'restore_{model_name}',
            content_type=content_type,
            defaults={'name': f'Can restore {model_name}'}
        )
        if created:
            created_count += 1

        return created_count