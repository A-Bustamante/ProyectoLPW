import os
from django import forms
from django.core.exceptions import ValidationError
from .models import Personal, ActivoTI, Asignacion

def validate_image_file(file):
    if not file:
        return
    # Validar tamaño (máximo 5MB)
    limit = 5 * 1024 * 1024
    if file.size > limit:
        raise ValidationError("El tamaño del archivo no debe superar los 5MB.")
    # Validar extensión (solo JPG/PNG)
    ext = os.path.splitext(file.name)[1].lower()
    valid_extensions = ['.jpg', '.jpeg', '.png']
    if ext not in valid_extensions:
        raise ValidationError("Solo se permiten imágenes en formato JPG, JPEG o PNG.")

def validate_pdf_file(file):
    if not file:
        return
    # Validar extensión (solo PDF)
    ext = os.path.splitext(file.name)[1].lower()
    if ext != '.pdf':
        raise ValidationError("El documento de acta firmada debe estar en formato PDF.")

class PersonalForm(forms.ModelForm):
    class Meta:
        model = Personal
        fields = ['employee_id', 'first_name', 'last_name', 'email', 'role', 'department', 'is_active']
        widgets = {
            'employee_id': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej. 10203040'}),
            'first_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej. Juan'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej. Pérez Gómez'}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Ej. juan.perez@empresa.com'}),
            'role': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej. Desarrollador Full-Stack'}),
            'department': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej. Tecnología'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

class ActivoTIForm(forms.ModelForm):
    evidence_image = forms.ImageField(
        required=False,
        validators=[validate_image_file],
        widget=forms.ClearableFileInput(attrs={'class': 'form-control-file'}),
        label="Foto de Evidencia Física"
    )

    class Meta:
        model = ActivoTI
        fields = ['custom_code', 'serial_number', 'imei', 'asset_type', 'brand', 'model', 'status', 'acquisition_date', 'evidence_image']
        widgets = {
            'custom_code': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej. LAP-2026-0042'}),
            'serial_number': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej. SN1234567890'}),
            'imei': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej. 351234567890123 (si aplica)'}),
            'asset_type': forms.Select(attrs={'class': 'form-control'}),
            'brand': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej. Dell'}),
            'model': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej. Latitude 5420'}),
            'status': forms.Select(attrs={'class': 'form-control'}),
            'acquisition_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
        }

class CheckOutForm(forms.Form):
    ACCESSORY_CHOICES = [
        ('Bateria', 'Batería Integrada/Extraíble'),
        ('Cable USB', 'Cable USB de datos'),
        ('Cargador', 'Cargador / Cable de corriente'),
        ('Audifonos', 'Audífonos manos libres'),
        ('Funda', 'Funda protectora / Maletín'),
    ]

    employee = forms.ModelChoiceField(
        queryset=Personal.objects.filter(is_active=True),
        widget=forms.Select(attrs={'class': 'form-control select2'}),
        label="Colaborador Responsable"
    )
    
    asset = forms.ModelChoiceField(
        queryset=ActivoTI.objects.filter(status='BODEGA'),
        widget=forms.Select(attrs={'class': 'form-control select2'}),
        label="Dispositivo TI Disponible"
    )

    notes = forms.CharField(
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Detalle el estado físico de entrega, rasguños, etc.'}),
        label="Notas de Entrega"
    )

    accessories = forms.MultipleChoiceField(
        choices=ACCESSORY_CHOICES,
        widget=forms.CheckboxSelectMultiple(attrs={'class': 'form-check-input'}),
        label="Accesorios Entregados",
        required=False
    )

    evidence_image = forms.ImageField(
        validators=[validate_image_file],
        widget=forms.ClearableFileInput(attrs={'class': 'form-control-file'}),
        label="Foto de Evidencia de Entrega",
        required=False
    )

class CheckInForm(forms.Form):
    ACCESSORY_CHOICES = [
        ('Bateria', 'Batería Integrada/Extraíble'),
        ('Cable USB', 'Cable USB de datos'),
        ('Cargador', 'Cargador / Cable de corriente'),
        ('Audifonos', 'Audífonos manos libres'),
        ('Funda', 'Funda protectora / Maletín'),
    ]

    STATUS_AFTER_CHOICES = [
        ('BODEGA', 'Volver a Bodega (Disponible)'),
        ('MANTENIMIENTO', 'Enviar a Mantenimiento (Daños)'),
        ('BAJA', 'Dar de Baja definitivo'),
    ]

    notes = forms.CharField(
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Detalle el estado de recepción, accesorios faltantes o daños.'}),
        label="Notas de Devolución"
    )

    accessories = forms.MultipleChoiceField(
        choices=ACCESSORY_CHOICES,
        widget=forms.CheckboxSelectMultiple(attrs={'class': 'form-check-input'}),
        label="Accesorios Recibidos",
        required=False
    )

    status_after = forms.ChoiceField(
        choices=STATUS_AFTER_CHOICES,
        widget=forms.Select(attrs={'class': 'form-control'}),
        label="Estado de Destino del Activo"
    )

    evidence_image = forms.ImageField(
        validators=[validate_image_file],
        widget=forms.ClearableFileInput(attrs={'class': 'form-control-file'}),
        label="Foto de Evidencia de Recepción",
        required=False
    )

class UploadSignatureForm(forms.ModelForm):
    signature_pdf = forms.FileField(
        validators=[validate_pdf_file],
        widget=forms.ClearableFileInput(attrs={'class': 'form-control'}),
        label="Cargar Acta Firmada (PDF)"
    )

    class Meta:
        model = Asignacion
        fields = ['signature_pdf']
