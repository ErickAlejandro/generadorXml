from django.urls import path
from . import views

urlpatterns = [
    path('crearats', views.crearats, name='crearats'),
    path('check_xml_files', views.check_xml_files, name='check_xml_files'),  # Nueva URL para la vista check_xml_files
    path('check_xml_files_recibidos', views.check_xml_files_emitidos, name='check_xml_files_recibidos'),
    path('guardar_anulados/', views.guardar_anulados, name='guardar_anulados'),
    path('delete_files/', views.delete_files, name='delete_files'),
    path('send-state/', views.sendState, name='send_state'),
    path('get-estado/', views.getEstado, name='get_estado'),
    path('send-stateEmit/', views.sendStateEmit, name='send_state_emit'),
    path('get-estadoEmit/', views.getEstadoEmit, name='get_estado_emit'),
]
