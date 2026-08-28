import os
from django.conf import settings
from django.utils import timezone
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors

from .interfaces import ICodeGenerator, IPDFGenerator
from ..models import Personal, ActivoTI, Asignacion, AuditLog

class StandardCodeGenerator(ICodeGenerator):
    def generate_code(self, asset_type: str, next_id: int) -> str:
        prefixes = {
            'LAPTOP': 'LAP',
            'SMARTPHONE': 'TEL',
            'TABLET': 'TAB',
            'MONITOR': 'MON',
            'PRINTER': 'PRI',
            'PERIPHERAL': 'PER',
            'OTHER': 'OTH',
        }
        prefix = prefixes.get(asset_type.upper(), 'ACT')
        year = timezone.now().year
        return f"{prefix}-{year}-{next_id:04d}"

class ReportLabPDFGenerator(IPDFGenerator):
    def generate_assignment_act(self, assignment) -> str:
        # Asegurar directorio de actas en media
        actas_dir = os.path.join(settings.MEDIA_ROOT, 'actas')
        os.makedirs(actas_dir, exist_ok=True)
        
        filename = f"acta_{assignment.id}_{assignment.asset.custom_code}.pdf"
        filepath = os.path.join(actas_dir, filename)
        
        doc = SimpleDocTemplate(filepath, pagesize=letter)
        styles = getSampleStyleSheet()
        
        # Estilos personalizados
        title_style = ParagraphStyle(
            'TitleStyle',
            parent=styles['Heading1'],
            fontName='Helvetica-Bold',
            fontSize=16,
            textColor=colors.HexColor('#002B49'),
            alignment=1,
            spaceAfter=15
        )
        subtitle_style = ParagraphStyle(
            'SubtitleStyle',
            parent=styles['Heading2'],
            fontName='Helvetica-Bold',
            fontSize=12,
            textColor=colors.HexColor('#333333'),
            spaceBefore=10,
            spaceAfter=5
        )
        normal_style = ParagraphStyle(
            'NormalStyle',
            parent=styles['Normal'],
            fontName='Helvetica',
            fontSize=10,
            leading=14,
            textColor=colors.HexColor('#555555')
        )
        
        story = []
        
        # Título
        story.append(Paragraph("ACTA DE RESPONSABILIDAD LEGAL DE ACTIVO TI", title_style))
        story.append(Spacer(1, 10))
        
        # Introducción
        intro_text = (
            f"En la fecha {assignment.check_out_date.strftime('%d/%m/%Y %H:%M')}, se hace entrega formal del siguiente "
            "activo tecnológico en calidad de herramienta de trabajo. El colaborador firmante se compromete a hacer uso adecuado "
            "del mismo y a seguir los lineamientos de seguridad de la información corporativos."
        )
        story.append(Paragraph(intro_text, normal_style))
        story.append(Spacer(1, 15))
        
        # Datos del Empleado
        story.append(Paragraph("DATOS DEL COLABORADOR", subtitle_style))
        emp = assignment.employee
        employee_data = [
            ["Nombre Completo:", f"{emp.first_name} {emp.last_name}"],
            ["Identificación (ID):", emp.employee_id],
            ["Cargo / Rol:", emp.role],
            ["Área / Depto:", emp.department],
            ["Correo Electrónico:", emp.email]
        ]
        t1 = Table(employee_data, colWidths=[150, 300])
        t1.setStyle(TableStyle([
            ('GRID', (0,0), (-1,-1), 0.5, colors.grey),
            ('BACKGROUND', (0,0), (0,-1), colors.HexColor('#F4F6F9')),
            ('FONTNAME', (0,0), (0,-1), 'Helvetica-Bold'),
            ('BOTTOMPADDING', (0,0), (-1,-1), 5),
            ('TOPPADDING', (0,0), (-1,-1), 5),
        ]))
        story.append(t1)
        story.append(Spacer(1, 15))
        
        # Datos del Activo
        story.append(Paragraph("DETALLES DEL ACTIVO TI", subtitle_style))
        asset = assignment.asset
        asset_data = [
            ["Código Interno:", asset.custom_code],
            ["Número de Serie:", asset.serial_number],
            ["IMEI (si aplica):", asset.imei or "N/A"],
            ["Tipo de Dispositivo:", asset.get_asset_type_display()],
            ["Marca y Modelo:", f"{asset.brand} {asset.model}"]
        ]
        t2 = Table(asset_data, colWidths=[150, 300])
        t2.setStyle(TableStyle([
            ('GRID', (0,0), (-1,-1), 0.5, colors.grey),
            ('BACKGROUND', (0,0), (0,-1), colors.HexColor('#F4F6F9')),
            ('FONTNAME', (0,0), (0,-1), 'Helvetica-Bold'),
            ('BOTTOMPADDING', (0,0), (-1,-1), 5),
            ('TOPPADDING', (0,0), (-1,-1), 5),
        ]))
        story.append(t2)
        story.append(Spacer(1, 15))
        
        # Accesorios
        story.append(Paragraph("ACCESORIOS Y CONDICIÓN DE ENTREGA", subtitle_style))
        acc_text = ", ".join(assignment.check_out_accessories) if assignment.check_out_accessories else "Ninguno"
        acc_data = [
            ["Accesorios Entregados:", acc_text],
            ["Notas / Estado:", assignment.check_out_notes or "Buen estado"]
        ]
        t3 = Table(acc_data, colWidths=[150, 300])
        t3.setStyle(TableStyle([
            ('GRID', (0,0), (-1,-1), 0.5, colors.grey),
            ('BACKGROUND', (0,0), (0,-1), colors.HexColor('#F4F6F9')),
            ('FONTNAME', (0,0), (0,-1), 'Helvetica-Bold'),
            ('BOTTOMPADDING', (0,0), (-1,-1), 5),
            ('TOPPADDING', (0,0), (-1,-1), 5),
        ]))
        story.append(t3)
        story.append(Spacer(1, 20))
        
        # Términos legales
        terms = (
            "El colaborador acepta la responsabilidad legal y administrativa por el cuidado, custodia y buen uso del equipo "
            "asignado. En caso de pérdida, daño malicioso o negligencia comprobada, el colaborador autoriza a la organización "
            "a realizar los cobros administrativos o de nómina pertinentes por reparación o reposición."
        )
        story.append(Paragraph(terms, normal_style))
        story.append(Spacer(1, 40))
        
        # Firmas
        sig_data = [
            [f"_____________________________\nFirma del Colaborador\nID: {emp.employee_id}", 
             f"_____________________________\nFirma de TI Recibe/Entrega\nAnalista: {assignment.officer.username}"]
        ]
        t4 = Table(sig_data, colWidths=[220, 220])
        t4.setStyle(TableStyle([
            ('ALIGN', (0,0), (-1,-1), 'CENTER'),
            ('FONTNAME', (0,0), (-1,-1), 'Helvetica'),
            ('FONTSIZE', (0,0), (-1,-1), 9),
        ]))
        story.append(t4)
        
        doc.build(story)
        return f"actas/{filename}"

class ServicioAsignacion:
    def __init__(self, code_generator: ICodeGenerator = None, pdf_generator: IPDFGenerator = None):
        self.code_generator = code_generator or StandardCodeGenerator()
        self.pdf_generator = pdf_generator or ReportLabPDFGenerator()

    def check_out(self, employee_id: str, asset_id: int, notes: str, accessories: list, image_file, officer, ip_address: str = None) -> Asignacion:
        # 1. Obtener y validar personal activo
        try:
            employee = Personal.objects.get(pk=employee_id)
        except Personal.DoesNotExist:
            raise ValueError("El colaborador especificado no existe.")
            
        if not employee.is_active:
            raise ValueError("No se puede asignar un equipo a un colaborador inactivo.")

        # 2. Obtener y validar activo disponible
        try:
            asset = ActivoTI.objects.get(pk=asset_id)
        except ActivoTI.DoesNotExist:
            raise ValueError("El activo tecnológico especificado no existe.")

        if asset.status != 'BODEGA':
            raise ValueError(f"El activo no está disponible para asignación (Estado actual: {asset.get_status_display()}).")

        # 3. Crear asignación
        assignment = Asignacion.objects.create(
            employee=employee,
            asset=asset,
            check_out_notes=notes,
            check_out_accessories=accessories,
            check_out_image=image_file,
            officer=officer
        )

        # 4. Actualizar estado del activo
        asset.status = 'ASIGNADO'
        asset.save()

        # 5. Generar PDF
        pdf_path = self.pdf_generator.generate_assignment_act(assignment)
        assignment.pdf_acta = pdf_path
        assignment.save()

        # 6. Registrar en Log de Auditoría
        AuditLog.objects.create(
            user=officer,
            action="CHECK-OUT",
            details=f"Asignado activo {asset.custom_code} ({asset.brand} {asset.model}) al colaborador {employee}. Acta generada: {pdf_path}",
            ip_address=ip_address
        )

        return assignment

    def check_in(self, assignment_id: int, notes: str, accessories: list, image_file, status_after: str, officer, ip_address: str = None) -> Asignacion:
        # 1. Validar asignación activa
        try:
            assignment = Asignacion.objects.get(pk=assignment_id)
        except Asignacion.DoesNotExist:
            raise ValueError("La asignación especificada no existe.")

        if assignment.is_returned:
            raise ValueError("Este equipo ya fue devuelto anteriormente.")

        # 2. Registrar devolución
        assignment.check_in_date = timezone.now()
        assignment.check_in_notes = notes
        assignment.check_in_accessories = accessories
        assignment.check_in_image = image_file
        assignment.is_returned = True
        assignment.save()

        # 3. Actualizar estado del activo
        asset = assignment.asset
        if status_after not in ['BODEGA', 'MANTENIMIENTO', 'BAJA']:
            status_after = 'BODEGA'
        asset.status = status_after
        asset.save()

        # 4. Enviar Alerta si se reportan daños o accesorios faltantes por mal uso
        has_damage = "daño" in notes.lower() or "dañado" in notes.lower() or "roto" in notes.lower() or status_after in ['MANTENIMIENTO', 'BAJA']
        if has_damage:
            # Aquí se dispara la alerta a Gerente de Operaciones y Recursos Humanos (simulada por log)
            alert_details = f"[ALERTA DE DAÑO] Retorno de activo {asset.custom_code} con daños. Notas de devolución: {notes}."
            AuditLog.objects.create(
                user=officer,
                action="ALERTA_DANOS",
                details=alert_details,
                ip_address=ip_address
            )

        # 5. Registrar en Log de Auditoría
        AuditLog.objects.create(
            user=officer,
            action="CHECK-IN",
            details=f"Devolución del activo {asset.custom_code}. Estado de destino: {asset.get_status_display()}.",
            ip_address=ip_address
        )

        return assignment
