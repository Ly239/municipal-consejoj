"""
Comando para cargar datos iniciales en tablas seeder.
Crea tipos de documentos y entes emisores del sistema.
"""
from django.core.management.base import BaseCommand
from documents.models import DocumentType, IssuingEntity


class Command(BaseCommand):
    help = 'Carga datos iniciales en tablas seeder (tipos de documento, entes emisores)'

    def handle(self, *args, **kwargs):
        self.stdout.write('🚀 Iniciando carga de datos básicos...')
        self.seed_document_types()
        self.seed_issuing_entities()
        self.stdout.write(self.style.SUCCESS('✅ Datos básicos cargados correctamente'))

    def seed_data(self, model, data, label):
        """
        Método genérico para sembrar datos.
        Recibe el modelo, una lista de diccionarios y una etiqueta.
        """
        for entry in data:
            # Obtener los campos para el get_or_create
            defaults = {k: v for k, v in entry.items() if k != 'name'}
            obj, created = model.objects.get_or_create(
                name=entry['name'],
                defaults=defaults
            )
            if created:
                self.stdout.write(self.style.SUCCESS(f'✓ {label}: "{entry["name"]}" creado'))
            else:
                self.stdout.write(self.style.WARNING(f'⚠ {label}: "{entry["name"]}" ya existe'))

    def seed_document_types(self):
        """Carga los tipos de documentos del sistema."""
        data = [
            {'name': 'Acuerdo', 'description': 'Acuerdo del Concejo Municipal'},
            {'name': 'Ordenanza', 'description': 'Ordenanza Municipal'},
            {'name': 'Resolución', 'description': 'Resolución de la Alcaldía'},
            {'name': 'Decreto', 'description': 'Decreto de la Alcaldía'},
            {'name': 'Acta', 'description': 'Acta de sesión del Concejo'},
            {'name': 'Informe de Comisión', 'description': 'Informe de comisión'},
            {'name': 'Oficio', 'description': 'Oficio de la Secretaría'},
            {'name': 'Providencia', 'description': 'Providencia administrativa'},
        ]
        self.seed_data(DocumentType, data, 'Tipo de Documento')

    def seed_issuing_entities(self):
        """Carga los entes emisores del sistema."""
        data = [
            {'name': 'Cuerpo de Bomberos'},
            {'name': 'Consejo Local de Planificación'},
            {'name': 'Alcaldía Junín'},
            {'name': 'CEDNA'},
            {'name': 'Contraloría'},
            {'name': 'Indejunin (Instituto Municipal del Deporte)'},
            {'name': 'Otros'},  # Permite escribir nombre personalizado
        ]
        self.seed_data(IssuingEntity, data, 'Ente Emisor')