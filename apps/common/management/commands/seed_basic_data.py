"""
Comando para cargar datos iniciales en tablas seeder.
Crea tipos de documentos y entes emisores del sistema.
"""
from django.core.management.base import BaseCommand
from documents.models import DocumentType, IssuingEntity


class Command(BaseCommand):
    help = 'Carga datos iniciales en tablas seeder'

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
            {'name': 'Informe Trimestral', 'description': 'Informe de gestión presentado cada tres meses'},  # ✅
            {'name': 'Informe de Comisión', 'description': 'Informe de comisión'},
            {'name': 'Oficio', 'description': 'Oficio de la Secretaría'},
            {'name': 'Providencia', 'description': 'Providencia administrativa'},
        ]
        self.seed_data(DocumentType, data, 'Tipo de Documento')

    def seed_issuing_entities(self):
        """Carga los entes emisores del sistema."""
        
        data = [
            {'name': 'Concejo Municipal de Junín', 'description': 'Poder Legislativo del municipio'},  # ✅
            {'name': 'Alcaldía de Junín', 'description': 'Poder Ejecutivo del municipio'},  # ✅
            {'name': 'Concejo Local de Planificación Pública (CLPP)', 'description': 'Órgano de planificación municipal'},
            {'name': 'Contraloría Municipal', 'description': 'Órgano de control fiscal'},
            {'name': 'Instituto Municipal del Deporte (IMDEJUNÍN)', 'description': 'Ente adscrito a la Alcaldía'},  # ✅
            {'name': 'Cuerpo de Bomberos', 'description': 'Servicio de emergencia municipal'},
            {'name': 'CEDNA', 'description': 'Concejo de Derechos de Niños, Niñas y Adolescentes'},
            {'name': 'Otros', 'description': 'Ente no listado (especificar en el documento)'}, # Permite escribir nombre personalizado
        ]
        self.seed_data(IssuingEntity, data, 'Ente Emisor')
