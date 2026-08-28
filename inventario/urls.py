from django.urls import path
from . import views

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    
    # Personal CRUD
    path('personal/', views.personal_list, name='personal_list'),
    path('personal/nuevo/', views.personal_create, name='personal_create'),
    path('personal/<int:pk>/editar/', views.personal_update, name='personal_update'),
    
    # Activos CRUD
    path('activos/', views.activo_list, name='activo_list'),
    path('activos/nuevo/', views.activo_create, name='activo_create'),
    path('activos/<int:pk>/editar/', views.activo_update, name='activo_update'),
    
    # Check-Out / Check-In
    path('checkout/', views.check_out_view, name='check_out'),
    path('checkin/<int:pk>/', views.check_in_view, name='check_in'),
    path('asignaciones/<int:pk>/firma/', views.upload_signature_view, name='upload_signature'),
    
    # Buscador e Historial
    path('historial/', views.historial_view, name='historial'),
    
    # Seguridad / Remote Wipe
    path('activos/<int:pk>/remote-wipe/', views.remote_wipe_view, name='remote_wipe'),
]
