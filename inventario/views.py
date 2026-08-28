import time
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.cache import cache
from django.utils import timezone
from django.http import HttpResponse, Http404

from .models import Personal, ActivoTI, Asignacion, AuditLog
from .forms import PersonalForm, ActivoTIForm, CheckOutForm, CheckInForm, UploadSignatureForm
from .services.services import ServicioAsignacion

def get_client_ip(request):
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip

def index(request):
    # Redirigir al dashboard
    return redirect('dashboard')

@login_required
def dashboard(request):
    cache_key = "dashboard_metrics"
    metrics = cache.get(cache_key)
    
    if not metrics:
        total_assets = ActivoTI.objects.count()
        in_stock = ActivoTI.objects.filter(status='BODEGA').count()
        assigned = ActivoTI.objects.filter(status='ASIGNADO').count()
        maintenance = ActivoTI.objects.filter(status='MANTENIMIENTO').count()
        retired = ActivoTI.objects.filter(status='BAJA').count()
        
        total_employees = Personal.objects.count()
        active_employees = Personal.objects.filter(is_active=True).count()
        
        # Tipos de activos para gráficos
        types_data = []
        for t_code, t_name in ActivoTI.ASSET_TYPES:
            count = ActivoTI.objects.filter(asset_type=t_code).count()
            types_data.append({'type': t_name, 'count': count})
            
        recent_logs = AuditLog.objects.all()[:8]
        
        metrics = {
            'total_assets': total_assets,
            'in_stock': in_stock,
            'assigned': assigned,
            'maintenance': maintenance,
            'retired': retired,
            'total_employees': total_employees,
            'active_employees': active_employees,
            'types_data': types_data,
            'recent_logs': recent_logs,
            'calculated_at': timezone.now().strftime('%H:%M:%S'),
        }
        # Caché por 30 segundos para demostración y latencia reducida (Redis)
        cache.set(cache_key, metrics, timeout=30)
        from_cache = False
    else:
        from_cache = True

    context = {
        'metrics': metrics,
        'from_cache': from_cache,
    }
    return render(request, 'inventario/dashboard.html', context)

# --- CRUD PERSONAL ---
@login_required
def personal_list(request):
    employees = Personal.objects.all()
    return render(request, 'inventario/personal_list.html', {'employees': employees})

@login_required
def personal_create(request):
    if request.method == 'POST':
        form = PersonalForm(request.POST)
        if form.is_valid():
            employee = form.save()
            AuditLog.objects.create(
                user=request.user,
                action="CREAR_PERSONAL",
                details=f"Registrado colaborador: {employee.first_name} {employee.last_name} (ID: {employee.employee_id})",
                ip_address=get_client_ip(request)
            )
            messages.success(request, "Colaborador registrado exitosamente.")
            return redirect('personal_list')
    else:
        form = PersonalForm()
    return render(request, 'inventario/personal_form.html', {'form': form, 'title': 'Registrar Colaborador'})

@login_required
def personal_update(request, pk):
    employee = get_object_or_404(Personal, pk=pk)
    if request.method == 'POST':
        form = PersonalForm(request.POST, instance=employee)
        if form.is_valid():
            # Si se pasa a inactivo, verificar si tiene activos pendientes
            is_active = form.cleaned_data.get('is_active')
            pending_assets = Asignacion.objects.filter(employee=employee, is_returned=False)
            if not is_active and pending_assets.exists():
                messages.error(request, f"No se puede desactivar al colaborador porque tiene {pending_assets.count()} activos asignados pendientes de devolución.")
                return render(request, 'inventario/personal_form.html', {'form': form, 'title': 'Editar Colaborador'})
            
            form.save()
            AuditLog.objects.create(
                user=request.user,
                action="EDITAR_PERSONAL",
                details=f"Actualizado colaborador: {employee.first_name} {employee.last_name} (ID: {employee.employee_id})",
                ip_address=get_client_ip(request)
            )
            messages.success(request, "Colaborador actualizado exitosamente.")
            return redirect('personal_list')
    else:
        form = PersonalForm(instance=employee)
    return render(request, 'inventario/personal_form.html', {'form': form, 'title': 'Editar Colaborador'})


# --- CRUD ACTIVOS ---
@login_required
def activo_list(request):
    assets = ActivoTI.objects.all()
    return render(request, 'inventario/activo_list.html', {'assets': assets})

@login_required
def activo_create(request):
    if request.method == 'POST':
        form = ActivoTIForm(request.POST, request.FILES)
        if form.is_valid():
            asset = form.save(commit=False)
            # Autogeneración de código de barras simple para visualización
            asset.barcode = f"BAR-{asset.serial_number}"
            asset.save()
            AuditLog.objects.create(
                user=request.user,
                action="CREAR_ACTIVO",
                details=f"Creado activo tecnológico: {asset.custom_code} ({asset.brand} {asset.model}, S/N: {asset.serial_number})",
                ip_address=get_client_ip(request)
            )
            messages.success(request, "Activo tecnológico registrado exitosamente.")
            return redirect('activo_list')
    else:
        form = ActivoTIForm()
    return render(request, 'inventario/activo_form.html', {'form': form, 'title': 'Registrar Activo TI'})

@login_required
def activo_update(request, pk):
    asset = get_object_or_404(ActivoTI, pk=pk)
    if request.method == 'POST':
        form = ActivoTIForm(request.POST, request.FILES, instance=asset)
        if form.is_valid():
            form.save()
            AuditLog.objects.create(
                user=request.user,
                action="EDITAR_ACTIVO",
                details=f"Modificado activo tecnológico: {asset.custom_code} ({asset.brand} {asset.model})",
                ip_address=get_client_ip(request)
            )
            messages.success(request, "Activo tecnológico actualizado exitosamente.")
            return redirect('activo_list')
    else:
        form = ActivoTIForm(instance=asset)
    return render(request, 'inventario/activo_form.html', {'form': form, 'title': 'Editar Activo TI'})


# --- FLUJOS CHECK-OUT / CHECK-IN ---
@login_required
def check_out_view(request):
    if request.method == 'POST':
        form = CheckOutForm(request.POST, request.FILES)
        if form.is_valid():
            employee = form.cleaned_data['employee']
            asset = form.cleaned_data['asset']
            notes = form.cleaned_data['notes']
            accessories = form.cleaned_data['accessories']
            image_file = form.cleaned_data['evidence_image']
            
            servicio = ServicioAsignacion()
            try:
                assignment = servicio.check_out(
                    employee_id=employee.id,
                    asset_id=asset.id,
                    notes=notes,
                    accessories=accessories,
                    image_file=image_file,
                    officer=request.user,
                    ip_address=get_client_ip(request)
                )
                messages.success(request, f"Activo {asset.custom_code} asignado con éxito a {employee}. Acta PDF generada.")
                return redirect('upload_signature', pk=assignment.pk)
            except Exception as e:
                messages.error(request, f"Error en la asignación: {str(e)}")
    else:
        form = CheckOutForm()
    return render(request, 'inventario/check_out.html', {'form': form})

@login_required
def check_in_view(request, pk):
    assignment = get_object_or_404(Asignacion, pk=pk, is_returned=False)
    if request.method == 'POST':
        form = CheckInForm(request.POST, request.FILES)
        if form.is_valid():
            notes = form.cleaned_data['notes']
            accessories = form.cleaned_data['accessories']
            status_after = form.cleaned_data['status_after']
            image_file = form.cleaned_data['evidence_image']
            
            servicio = ServicioAsignacion()
            try:
                servicio.check_in(
                    assignment_id=assignment.id,
                    notes=notes,
                    accessories=accessories,
                    image_file=image_file,
                    status_after=status_after,
                    officer=request.user,
                    ip_address=get_client_ip(request)
                )
                messages.success(request, f"Devolución procesada con éxito. El activo ha retornado a: {status_after}.")
                return redirect('dashboard')
            except Exception as e:
                messages.error(request, f"Error en la devolución: {str(e)}")
    else:
        form = CheckInForm()
    return render(request, 'inventario/check_in.html', {'form': form, 'assignment': assignment})

@login_required
def upload_signature_view(request, pk):
    assignment = get_object_or_404(Asignacion, pk=pk)
    if request.method == 'POST':
        form = UploadSignatureForm(request.POST, request.FILES, instance=assignment)
        if form.is_valid():
            form.save()
            AuditLog.objects.create(
                user=request.user,
                action="CARGA_FIRMA",
                details=f"Acta firmada cargada exitosamente para asignación de {assignment.asset.custom_code} a {assignment.employee}.",
                ip_address=get_client_ip(request)
            )
            messages.success(request, "Acta firmada cargada exitosamente. Proceso finalizado.")
            return redirect('activo_list')
    else:
        form = UploadSignatureForm(instance=assignment)
    return render(request, 'inventario/upload_signature.html', {'form': form, 'assignment': assignment})


# --- BUSCADOR E HISTORIAL ---
@login_required
def historial_view(request):
    query = request.GET.get('q', '').strip()
    timeline = []
    asset = None
    employee = None
    search_type = None

    if query:
        # Intentar buscar por activo (Código interno o serial)
        asset_q = ActivoTI.objects.filter(custom_code__iexact=query) | ActivoTI.objects.filter(serial_number__iexact=query)
        if asset_q.exists():
            asset = asset_q.first()
            search_type = 'asset'
            # Cargar timeline del activo
            timeline = Asignacion.objects.filter(asset=asset).order_by('-check_out_date')
        else:
            # Intentar buscar por empleado (ID de empleado)
            emp_q = Personal.objects.filter(employee_id__iexact=query)
            if emp_q.exists():
                employee = emp_q.first()
                search_type = 'employee'
                # Cargar timeline del empleado
                timeline = Asignacion.objects.filter(employee=employee).order_by('-check_out_date')
            else:
                messages.warning(request, "No se encontraron activos o colaboradores con los criterios de búsqueda provistos.")
                
    return render(request, 'inventario/historial.html', {
        'query': query,
        'timeline': timeline,
        'asset': asset,
        'employee': employee,
        'search_type': search_type
    })


# --- CONTROL DE ROBO/EXTRAVÍO E ISO 27001 REMOTO WIPE ---
@login_required
def remote_wipe_view(request, pk):
    asset = get_object_or_404(ActivoTI, pk=pk)
    if request.method == 'POST':
        # Registrar orden de borrado remoto inmutable en Auditoría
        AuditLog.objects.create(
            user=request.user,
            action="REMOTE_WIPE_ORDERED",
            details=f"ORDEN DE BORRADO REMOTO (REMOTE WIPE) ENVIADA para el activo {asset.custom_code} (S/N: {asset.serial_number}) debido a pérdida o robo.",
            ip_address=get_client_ip(request)
        )
        
        # Cambiar estado del activo a Baja
        asset.status = 'BAJA'
        asset.save()
        
        # Cerrar cualquier asignación activa del equipo
        active_assignments = Asignacion.objects.filter(asset=asset, is_returned=False)
        for assignment in active_assignments:
            assignment.is_returned = True
            assignment.check_in_date = timezone.now()
            assignment.check_in_notes = "Devolución forzosa debido a Borrado Remoto / Pérdida del dispositivo."
            assignment.save()
            
        messages.warning(request, f"Orden de borrado remoto (Remote Wipe) enviada y registrada con éxito. El activo {asset.custom_code} ha sido dado de baja.")
        return redirect('activo_list')
        
    return render(request, 'inventario/remote_wipe_confirm.html', {'asset': asset})
