from django.contrib import admin
from .models import Personal, ActivoTI, Asignacion, AuditLog

@admin.register(Personal)
class PersonalAdmin(admin.ModelAdmin):
    list_display = ('employee_id', 'first_name', 'last_name', 'email', 'role', 'department', 'is_active')
    list_filter = ('is_active', 'department')
    search_fields = ('employee_id', 'first_name', 'last_name', 'email')
    ordering = ('last_name', 'first_name')

@admin.register(ActivoTI)
class ActivoTIAdmin(admin.ModelAdmin):
    list_display = ('custom_code', 'brand', 'model', 'asset_type', 'serial_number', 'status', 'acquisition_date')
    list_filter = ('asset_type', 'status', 'brand')
    search_fields = ('custom_code', 'serial_number', 'brand', 'model', 'imei')
    ordering = ('custom_code',)

@admin.register(Asignacion)
class AsignacionAdmin(admin.ModelAdmin):
    list_display = ('asset', 'employee', 'check_out_date', 'check_in_date', 'is_returned', 'officer')
    list_filter = ('is_returned', 'check_out_date', 'check_in_date')
    search_fields = ('asset__custom_code', 'asset__serial_number', 'employee__first_name', 'employee__last_name', 'employee__employee_id')
    raw_id_fields = ('employee', 'asset')
    readonly_fields = ('pdf_acta',)

@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ('timestamp', 'user', 'action', 'ip_address')
    list_filter = ('action', 'timestamp')
    search_fields = ('action', 'details', 'user__username')

    # Logs de auditoría inmutables: desactivar creación, edición y eliminación en panel admin
    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
