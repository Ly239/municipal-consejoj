"""
Comando para cargar datos de demostración en la app documents.

Crea 10 gacetas (5 ordinarias + 5 extraordinarias) y 12 documentos
con datos realistas para probar:
- Filtros por año, mes, tipo de documento, estado y rango de fechas.
- Formato con ceros a la izquierda (001, 002, ..., 121).
- Estados: aprobado, pendiente, anulado.
- Entes emisores: mayoría Concejo, algunos externos, algunos "Otros".

Uso:
    python manage.py seed_demo_documents

Idempotente: correr el comando múltiples veces NO duplica datos.
"""
from datetime import date
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model

from documents.models import Gazette, Document, DocumentType, IssuingEntity

User = get_user_model()


class Command(BaseCommand):
    help = 'Carga datos de demostración (gacetas + documentos) para pruebas y presentaciones'

    def handle(self, *args, **kwargs):
        self.stdout.write('🚀 Iniciando carga de datos de demostración...')

        if not self._check_prerequisites():
            return

        admin_user = User.objects.filter(username='admin').first()
        employee_user = User.objects.filter(username='employee').first()

        doc_types = {dt.name: dt for dt in DocumentType.objects.all()}
        entities = {ie.name: ie for ie in IssuingEntity.objects.all()}

        gazettes = self._seed_gazettes()
        self._seed_documents(gazettes, doc_types, entities, admin_user, employee_user)

        self.stdout.write(self.style.SUCCESS('🎉 Datos de demostración cargados correctamente'))

    # ========================================================================
    # VALIDACIONES PREVIAS
    # ========================================================================

    def _check_prerequisites(self):
        missing = []
        if not DocumentType.objects.exists():
            missing.append('DocumentType (correr seed_basic_data primero)')
        if not IssuingEntity.objects.exists():
            missing.append('IssuingEntity (correr seed_basic_data primero)')
        if not User.objects.filter(username='admin').exists():
            missing.append('Usuario "admin" (correr seed_users primero)')
        if not User.objects.filter(username='employee').exists():
            missing.append('Usuario "employee" (correr seed_users primero)')

        if missing:
            self.stdout.write(self.style.ERROR('❌ Faltan prerrequisitos:'))
            for item in missing:
                self.stdout.write(f'   • {item}')
            return False
        return True

    # ========================================================================
    # GACETAS
    # ========================================================================

    def _seed_gazettes(self):
        """
        10 gacetas:
        - 5 ordinarias: números 1, 2, 3 (2025) y 1, 2 (2026).
        - 5 extraordinarias: números 50, 70 (2025) y 80, 100, 121 (2026).
        La última (121/2026) queda VACÍA para mostrar el estado sin documentos.
        """
        self.stdout.write('\n📰 Cargando gacetas...')

        gazettes_data = [
            # --- ORDINARIAS (consecutivas desde 1) ---
            {'number': 1, 'year': 2025, 'is_extraordinary': False,
             'emission_date': date(2025, 1, 20),
             'description': 'Gaceta con las ordenanzas aprobadas en la primera sesión del año.'},
            {'number': 2, 'year': 2025, 'is_extraordinary': False,
             'emission_date': date(2025, 3, 15),
             'description': 'Acuerdos y resoluciones del primer trimestre.'},
            {'number': 3, 'year': 2025, 'is_extraordinary': False,
             'emission_date': date(2025, 4, 22),
             'description': 'Publicación de ordenanzas de gestión ambiental.'},
            {'number': 1, 'year': 2026, 'is_extraordinary': False,
             'emission_date': date(2026, 1, 20),
             'description': 'Primera gaceta ordinaria del año 2026.'},
            {'number': 2, 'year': 2026, 'is_extraordinary': False,
             'emission_date': date(2026, 2, 15),
             'description': 'Segunda gaceta ordinaria del año 2026.'},

            # --- EXTRAORDINARIAS (números salteados para verificar orden y formato) ---
            {'number': 50, 'year': 2025, 'is_extraordinary': True,
             'emission_date': date(2025, 7, 10),
             'description': 'Publicación extraordinaria sobre el presupuesto del segundo semestre.'},
            {'number': 70, 'year': 2025, 'is_extraordinary': True,
             'emission_date': date(2025, 9, 15),
             'description': 'Edición extraordinaria con ordenanzas de emergencia.'},
            {'number': 80, 'year': 2026, 'is_extraordinary': True,
             'emission_date': date(2026, 3, 10),
             'description': 'Publicación extraordinaria sobre régimen tributario municipal.'},
            {'number': 100, 'year': 2026, 'is_extraordinary': True,
             'emission_date': date(2026, 5, 5),
             'description': 'Gaceta extraordinaria de mitad de año.'},
            {'number': 121, 'year': 2026, 'is_extraordinary': True,
             'emission_date': date(2026, 7, 22),
             'description': 'Última gaceta extraordinaria — sin documentos asociados para probar el estado vacío.'},
        ]

        gazettes = {}
        for data in gazettes_data:
            gazette, created = Gazette.objects.get_or_create(
                number=data['number'],
                year=data['year'],
                is_extraordinary=data['is_extraordinary'],
                defaults={
                    'emission_date': data['emission_date'],
                    'description': data['description'],
                }
            )
            key = (data['number'], data['year'], data['is_extraordinary'])
            gazettes[key] = gazette

            if created:
                self.stdout.write(self.style.SUCCESS(f'   ✓ {gazette}'))
            else:
                self.stdout.write(self.style.WARNING(f'   ⚠ {gazette} (ya existía)'))

        return gazettes

    # ========================================================================
    # DOCUMENTOS
    # ========================================================================

    def _seed_documents(self, gazettes, doc_types, entities, admin_user, employee_user):
        """
        12 documentos distribuidos en 9 gacetas (la 121/2026 queda vacía).

        Distribución:
        - Primeros 5 documentos: números 1, 2, 3, 4, 5 (consecutivos).
        - Otros 7 documentos: números salteados (10, 50, 70, 80, 90, 100, 110).
        - Estados: 2 aprobados, 1 anulado, 9 pendientes.
        - submitted_by: 7 admin, 5 employee.
        """
        self.stdout.write('\n📄 Cargando documentos...')

        def g(number, year, extra=False):
            return gazettes[(number, year, extra)]

        documents_data = [
            # --- APROBADOS (admin) ---
            {
                'gazette': g(1, 2025), 'number': 1,
                'title': 'Ordenanza sobre la Protección y Fomento del Café en el Municipio Junín',
                'description': (
                    'Normativa que declara el café como patrimonio cultural y establece '
                    'incentivos para los productores locales del municipio andino.'
                ),
                'document_type': 'Ordenanza', 'issuing_entity': 'Concejo Municipal de Junín',
                'submitted_by': admin_user, 'emission_date': date(2025, 1, 25),
                'is_approved': True, 'is_annulled': False,
            },
            {
                'gazette': g(2, 2025), 'number': 2,
                'title': 'Acuerdo de Reconocimiento a los «Ángeles de la Autopista»',
                'description': (
                    'Acuerdo mediante el cual el Concejo Municipal reconoce la labor del cuerpo '
                    'paramédico y de rescate en la vía Rubio-San Cristóbal.'
                ),
                'document_type': 'Acuerdo', 'issuing_entity': 'Concejo Municipal de Junín',
                'submitted_by': admin_user, 'emission_date': date(2025, 3, 18),
                'is_approved': True, 'is_annulled': False,
            },

            # --- PENDIENTES (admin) ---
            {
                'gazette': g(3, 2025), 'number': 3,
                'title': 'Resolución sobre la Conformación de la Comisión de Hacienda y Contraloría',
                'description': (
                    'Resolución interna que designa a los integrantes de la Comisión Permanente '
                    'de Hacienda y Contraloría para el período legislativo vigente.'
                ),
                'document_type': 'Resolución', 'issuing_entity': 'Concejo Municipal de Junín',
                'submitted_by': admin_user, 'emission_date': date(2025, 4, 25),
                'is_approved': False, 'is_annulled': False,
            },
            {
                'gazette': g(1, 2026), 'number': 4,
                'title': 'Ordenanza para la Gestión Integral de Residuos Sólidos Urbanos',
                'description': (
                    'Instrumento jurídico que regula la recolección, tratamiento y disposición '
                    'final de residuos en el municipio, con enfoque en sostenibilidad ambiental.'
                ),
                'document_type': 'Ordenanza', 'issuing_entity': 'Concejo Municipal de Junín',
                'submitted_by': admin_user, 'emission_date': date(2026, 1, 22),
                'is_approved': False, 'is_annulled': False,
            },
            {
                'gazette': g(2, 2026), 'number': 5,
                'title': 'Acta de la Sesión Ordinaria N° 55 del Concejo Municipal',
                'description': (
                    'Acta oficial que recoge los puntos tratados, deliberaciones y acuerdos '
                    'alcanzados durante la Sesión Ordinaria N° 55.'
                ),
                'document_type': 'Acta', 'issuing_entity': 'Concejo Municipal de Junín',
                'submitted_by': admin_user, 'emission_date': date(2026, 2, 20),
                'is_approved': False, 'is_annulled': False,
            },

            # --- PENDIENTES / ANULADOS (employee) ---
            {
                'gazette': g(50, 2025, extra=True), 'number': 70,
                'title': 'Decreto de Creación del Instituto Municipal del Deporte',
                'description': (
                    'Decreto ejecutivo que crea el Instituto Municipal del Deporte de Junín, '
                    'con personalidad jurídica y patrimonio propio.'
                ),
                'document_type': 'Decreto', 'issuing_entity': 'Alcaldía de Junín',
                'submitted_by': employee_user, 'emission_date': date(2025, 7, 15),
                'is_approved': False, 'is_annulled': False,
            },
            {
                'gazette': g(70, 2025, extra=True), 'number': 80,
                'title': 'Oficio de la Contraloría Municipal sobre Auditoría del Ejercicio 2025',
                'description': (
                    'Oficio mediante el cual la Contraloría Municipal remite las observaciones '
                    'preliminares de la auditoría correspondiente al ejercicio fiscal 2025.'
                ),
                'document_type': 'Oficio', 'issuing_entity': 'Contraloría Municipal',
                'submitted_by': employee_user, 'emission_date': date(2025, 9, 20),
                'is_approved': False, 'is_annulled': True,
            },
            {
                'gazette': g(80, 2026, extra=True), 'number': 100,
                'title': 'Informe de la Comisión Permanente de Servicios Públicos',
                'description': (
                    'Informe de gestión presentado por la Comisión de Servicios Públicos '
                    'sobre las labores realizadas durante el período agosto-diciembre 2025.'
                ),
                'document_type': 'Informe de Comisión', 'issuing_entity': 'Concejo Municipal de Junín',
                'submitted_by': admin_user, 'emission_date': date(2026, 3, 12),
                'is_approved': False, 'is_annulled': False,
            },
            {
                'gazette': g(80, 2026, extra=True), 'number': 10,
                'title': 'Providencia Administrativa del Cuerpo de Bomberos',
                'description': (
                    'Providencia que establece los procedimientos internos para la atención '
                    'de emergencias en el municipio Junín.'
                ),
                'document_type': 'Providencia', 'issuing_entity': 'Cuerpo de Bomberos',
                'submitted_by': employee_user, 'emission_date': date(2026, 3, 18),
                'is_approved': False, 'is_annulled': False,
            },
            {
                'gazette': g(100, 2026, extra=True), 'number': 50,
                'title': 'Informe de Gestión Trimestral — Enero a Marzo 2026',
                'description': (
                    'Informe trimestral de gestión del Concejo Municipal correspondiente '
                    'al primer trimestre del año 2026.'
                ),
                'document_type': 'Informe Trimestral', 'issuing_entity': 'Concejo Municipal de Junín',
                'submitted_by': employee_user, 'emission_date': date(2026, 4, 5),
                'is_approved': False, 'is_annulled': False,
            },
            {
                'gazette': g(100, 2026, extra=True), 'number': 90,
                'title': 'Resolución de Reconocimiento al Consejo Comunal Santa Rosalía',
                'description': (
                    'Resolución del Concejo Municipal que reconoce la labor comunitaria '
                    'del Consejo Comunal Santa Rosalía en favor de la parroquia Rubio.'
                ),
                'document_type': 'Resolución', 'issuing_entity': 'Otros',
                'other_entity_description': 'Consejo Comunal Santa Rosalía',
                'submitted_by': employee_user, 'emission_date': date(2026, 5, 8),
                'is_approved': False, 'is_annulled': False,
            },
            {
                'gazette': g(100, 2026, extra=True), 'number': 110,
                'title': 'Acuerdo de Apoyo a la Junta Parroquial de Rubio',
                'description': (
                    'Acuerdo mediante el cual el Concejo Municipal brinda respaldo institucional '
                    'a los proyectos de infraestructura comunitaria de la Junta Parroquial.'
                ),
                'document_type': 'Acuerdo', 'issuing_entity': 'Concejo Municipal de Junín',
                'submitted_by': admin_user, 'emission_date': date(2026, 5, 15),
                'is_approved': False, 'is_annulled': False,
            },
        ]

        created_count = 0
        for data in documents_data:
            gazette = data['gazette']
            number = data['number']
            doc_type = doc_types.get(data['document_type'])
            entity = entities.get(data['issuing_entity'])

            if not doc_type or not entity:
                self.stdout.write(self.style.ERROR(
                    f'   ✗ Tipo "{data["document_type"]}" o ente "{data["issuing_entity"]}" no existe. '
                    'Correr seed_basic_data primero.'
                ))
                continue

            extra_fields = {}
            if 'other_entity_description' in data:
                extra_fields['other_entity_description'] = data['other_entity_description']

            document, created = Document.objects.get_or_create(
                gazette=gazette,
                number=number,
                defaults={
                    'title': data['title'],
                    'description': data['description'],
                    'document_type': doc_type,
                    'issuing_entity': entity,
                    'submitted_by': data['submitted_by'],
                    'emission_date': data['emission_date'],
                    'is_approved': data['is_approved'],
                    'is_annulled': data['is_annulled'],
                    'pdf_file': None,
                    'image': None,
                    **extra_fields,
                }
            )

            if created:
                created_count += 1
                estado = '✓' if data['is_approved'] else ('✗' if data['is_annulled'] else '⏳')
                self.stdout.write(self.style.SUCCESS(
                    f'   ✓ [{estado}] {document.document_type.name} N° {document.formatted_number}-{gazette.year}'
                ))
            else:
                self.stdout.write(self.style.WARNING(f'   ⚠ Documento ya existía: {document}'))

        self.stdout.write(f'\n📊 Total de documentos creados: {created_count} / {len(documents_data)}')