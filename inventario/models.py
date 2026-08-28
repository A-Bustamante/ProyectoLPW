from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone

class Personal(models.Model):
    employee_id = models.CharField(max_length=50, unique=True, verbose_name="ID de Empleado / Cédula")
    first_name = models.CharField(max_length=100, verbose_name="Nombres")
    last_name = models.CharField(max_length=100, verbose_name="Apellidos")
    email = models.EmailField(max_length=255, verbose_name="Correo Institucional")
    role = models.CharField(max_length=100, verbose_name="Rol / Cargo")
    department = models.CharField(max_length=100, verbose_name="Área / Departamento")
    is_active = models.BooleanField(default=True, verbose_name="Activo")

    def __str__(self):
        return f"{self.first_name} {self.last_name} ({self.employee_id})"

    class Meta:
        verbose_name = "Personal"
        verbose_name_plural = "Personal"

class ActivoTI(models.Model):
    ASSET_TYPES = [
        ('LAPTOP', 'Computador Portátil'),
        ('SMARTPHONE', 'Smartphone'),
        ('TABLET', 'Tablet'),
        ('MONITOR', 'Monitor'),
        ('PRINTER', 'Impresora'),
        ('PERIPHERAL', 'Periférico'),
        ('OTHER', 'Otro'),
    ]

    STATUS_CHOICES = [
        ('BODEGA', 'En Bodega'),
        ('ASIGNADO', 'Asignado'),
        ('MANTENIMIENTO', 'En Mantenimiento'),
        ('BAJA', 'Dado de Baja'),
    ]

    custom_code = models.CharField(max_length=50, unique=True, verbose_name="Código Interno")
    barcode = models.CharField(max_length=100, blank=True, null=True, verbose_name="Código de Barras")
    serial_number = models.CharField(max_length=100, unique=True, verbose_name="Número de Serie")
    imei = models.CharField(max_length=50, blank=True, null=True, verbose_name="IMEI (Móviles)")
    asset_type = models.CharField(max_length=20, choices=ASSET_TYPES, verbose_name="Tipo de Activo")
    brand = models.CharField(max_length=100, verbose_name="Marca")
    model = models.CharField(max_length=100, verbose_name="Modelo")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='BODEGA', verbose_name="Estado")
    acquisition_date = models.DateField(verbose_name="Fecha de Adquisición")
    evidence_image = models.ImageField(upload_to='evidences/assets/', blank=True, null=True, verbose_name="Foto de Evidencia Física")

    def __str__(self):
        return f"{self.custom_code} - {self.brand} {self.model} ({self.serial_number})"

    class Meta:
        verbose_name = "Activo TI"
        verbose_name_plural = "Activos TI"

class Asignacion(models.Model):
    employee = models.ForeignKey(Personal, on_delete=models.PROTECT, related_name='assignments', verbose_name="Empleado")
    asset = models.ForeignKey(ActivoTI, on_delete=models.PROTECT, related_name='assignments', verbose_name="Activo TI")
    
    # Check-Out Details
    check_out_date = models.DateTimeField(default=timezone.now, verbose_name="Fecha de Entrega")
    check_out_notes = models.TextField(verbose_name="Notas de Entrega")
    check_out_accessories = models.JSONField(default=list, verbose_name="Accesorios Entregados")
    check_out_image = models.ImageField(upload_to='evidences/checkouts/', blank=True, null=True, verbose_name="Foto de Evidencia Entrega")
    
    # Check-In Details
    check_in_date = models.DateTimeField(blank=True, null=True, verbose_name="Fecha de Devolución")
    check_in_notes = models.TextField(blank=True, null=True, verbose_name="Notas de Devolución")
    check_in_accessories = models.JSONField(default=list, blank=True, null=True, verbose_name="Accesorios Recibidos")
    check_in_image = models.ImageField(upload_to='evidences/checkins/', blank=True, null=True, verbose_name="Foto de Evidencia Recepción")
    
    # Files
    pdf_acta = models.FileField(upload_to='actas/', blank=True, null=True, verbose_name="Acta de Responsabilidad (PDF)")
    signature_pdf = models.FileField(upload_to='signatures/', blank=True, null=True, verbose_name="Acta Firmada (PDF)")
    
    # Auditor / IT Admin in charge
    officer = models.ForeignKey(User, on_delete=models.PROTECT, related_name='assignments_handled', verbose_name="Analista de TI")
    is_returned = models.BooleanField(default=False, verbose_name="Devuelto")

    def __str__(self):
        return f"{self.asset.custom_code} -> {self.employee} ({'Devuelto' if self.is_returned else 'Asignado'})"

    class Meta:
        verbose_name = "Asignación / Préstamo"
        verbose_name_plural = "Asignaciones / Préstamos"

class AuditLog(models.Model):
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Usuario")
    action = models.CharField(max_length=255, verbose_name="Acción")
    timestamp = models.DateTimeField(auto_now_add=True, verbose_name="Fecha y Hora")
    details = models.TextField(verbose_name="Detalles")
    ip_address = models.GenericIPAddressField(null=True, blank=True, verbose_name="Dirección IP")

    def __str__(self):
        return f"{self.timestamp} - {self.user} - {self.action}"

    class Meta:
        verbose_name = "Log de Auditoría"
        verbose_name_plural = "Logs de Auditoría"
        ordering = ['-timestamp']
