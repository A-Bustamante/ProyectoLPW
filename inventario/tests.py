import os
import datetime
from django.test import TestCase
from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.exceptions import ValidationError

from .models import Personal, ActivoTI, Asignacion, AuditLog
from .forms import validate_image_file
from .services.services import StandardCodeGenerator, ServicioAsignacion

class ITAssetInventoryTests(TestCase):
    def setUp(self):
        # Configurar analista de TI
        self.officer = User.objects.create_user(username="test_analyst", password="testpassword123")
        
        # Colaborador activo
        self.emp_active = Personal.objects.create(
            employee_id="101010",
            first_name="Juan",
            last_name="Perez",
            email="juan.perez@empresa.com",
            role="Desarrollador",
            department="Tecnología",
            is_active=True
        )

        # Colaborador inactivo
        self.emp_inactive = Personal.objects.create(
            employee_id="202020",
            first_name="Maria",
            last_name="Gomez",
            email="maria.gomez@empresa.com",
            role="Diseñadora",
            department="Mercadeo",
            is_active=False
        )

        # Activo disponible
        self.asset_available = ActivoTI.objects.create(
            custom_code="LAP-2026-0001",
            serial_number="SN9999",
            asset_type="LAPTOP",
            brand="Lenovo",
            model="ThinkPad",
            status="BODEGA",
            acquisition_date=datetime.date.today()
        )

        # Activo ya asignado
        self.asset_assigned = ActivoTI.objects.create(
            custom_code="TEL-2026-0002",
            serial_number="SN8888",
            asset_type="SMARTPHONE",
            brand="Samsung",
            model="Galaxy S23",
            status="ASIGNADO",
            acquisition_date=datetime.date.today()
        )

    # 1. PRUEBAS DE VALIDACIÓN DE ARCHIVOS
    def test_image_file_validation_valid(self):
        # Crear un archivo de imagen simulado pequeño y correcto
        small_image = SimpleUploadedFile("test.png", b"file_content", content_type="image/png")
        try:
            validate_image_file(small_image)
        except ValidationError:
            self.fail("validate_image_file lanzó ValidationError para un archivo correcto.")

    def test_image_file_validation_invalid_type(self):
        # Archivo que no es imagen
        text_file = SimpleUploadedFile("test.txt", b"file_content", content_type="text/plain")
        with self.assertRaises(ValidationError) as context:
            validate_image_file(text_file)
        self.assertIn("Solo se permiten imágenes en formato JPG, JPEG o PNG", str(context.exception))

    def test_image_file_validation_invalid_size(self):
        # Simular un archivo mayor a 5MB (ej: 6MB)
        large_file = SimpleUploadedFile("test.png", b"0" * (6 * 1024 * 1024), content_type="image/png")
        with self.assertRaises(ValidationError) as context:
            validate_image_file(large_file)
        self.assertIn("El tamaño del archivo no debe superar los 5MB", str(context.exception))

    # 2. PRUEBA DE PRINCIPIOS SOLID (GENERACIÓN DE CÓDIGO)
    def test_standard_code_generator(self):
        generator = StandardCodeGenerator()
        code1 = generator.generate_code("LAPTOP", 42)
        code2 = generator.generate_code("SMARTPHONE", 123)
        current_year = datetime.date.today().year
        
        self.assertEqual(code1, f"LAP-{current_year}-0042")
        self.assertEqual(code2, f"TEL-{current_year}-0123")

    # 3. PRUEBA DE FLUJO DE ASIGNACIÓN (CHECK-OUT) Y CONCURRENCIA
    def test_check_out_successful(self):
        service = ServicioAsignacion()
        
        # Realizar asignación exitosa
        assignment = service.check_out(
            employee_id=self.emp_active.id,
            asset_id=self.asset_available.id,
            notes="Entrega con cargador y funda",
            accessories=["Cargador", "Funda"],
            image_file=None,
            officer=self.officer
        )
        
        # Verificar estado del activo
        self.asset_available.refresh_from_db()
        self.assertEqual(self.asset_available.status, "ASIGNADO")
        
        # Verificar que se creó el registro
        self.assertIsNotNone(assignment.pk)
        self.assertEqual(assignment.employee, self.emp_active)
        self.assertEqual(assignment.asset, self.asset_available)
        self.assertTrue(assignment.pdf_acta.name.startswith("actas/acta_"))

    def test_check_out_inactive_employee(self):
        service = ServicioAsignacion()
        # Intentar asignar a un colaborador inactivo
        with self.assertRaises(ValueError) as context:
            service.check_out(
                employee_id=self.emp_inactive.id,
                asset_id=self.asset_available.id,
                notes="Notas",
                accessories=[],
                image_file=None,
                officer=self.officer
            )
        self.assertIn("No se puede asignar un equipo a un colaborador inactivo", str(context.exception))

    def test_check_out_concurrency_lock(self):
        service = ServicioAsignacion()
        # Intentar asignar un activo que ya está en estado ASIGNADO
        with self.assertRaises(ValueError) as context:
            service.check_out(
                employee_id=self.emp_active.id,
                asset_id=self.asset_assigned.id,
                notes="Notas",
                accessories=[],
                image_file=None,
                officer=self.officer
            )
        self.assertIn("El activo no está disponible para asignación", str(context.exception))

    # 4. PRUEBA DE FLUJO DE RETORNO (CHECK-IN) y DAÑOS
    def test_check_in_successful(self):
        service = ServicioAsignacion()
        # Crear asignación previa
        assignment = Asignacion.objects.create(
            employee=self.emp_active,
            asset=self.asset_assigned,
            check_out_notes="Entrega inicial",
            check_out_accessories=["Cargador"],
            officer=self.officer
        )
        
        # Procesar devolución
        returned_assignment = service.check_in(
            assignment_id=assignment.id,
            notes="Devolución con cargador completo y pantalla intacta",
            accessories=["Cargador"],
            image_file=None,
            status_after="BODEGA",
            officer=self.officer
        )
        
        self.assertTrue(returned_assignment.is_returned)
        self.asset_assigned.refresh_from_db()
        self.assertEqual(self.asset_assigned.status, "BODEGA")

    # 5. PRUEBA DE LOGS DE AUDITORÍA INMUTABLES
    def test_audit_logs_creation(self):
        service = ServicioAsignacion()
        
        # Realizar checkout
        service.check_out(
            employee_id=self.emp_active.id,
            asset_id=self.asset_available.id,
            notes="Entrega",
            accessories=[],
            image_file=None,
            officer=self.officer,
            ip_address="192.168.1.50"
        )
        
        # Verificar log en base de datos
        logs = AuditLog.objects.filter(action="CHECK-OUT")
        self.assertEqual(logs.count(), 1)
        log = logs.first()
        self.assertEqual(log.user, self.officer)
        self.assertEqual(log.ip_address, "192.168.1.50")
        self.assertIn(self.asset_available.custom_code, log.details)
