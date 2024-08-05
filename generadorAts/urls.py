from django.urls import path
from . import views

urlpatterns = [
    path('crearats', views.crearats, name='crearats'),
    path('check_xml_files', views.check_xml_files, name='check_xml_files'),  # Nueva URL para la vista check_xml_files
    path('check_xml_files_recibidos', views.check_xml_files_emitidos, name='check_xml_files_recibidos'),
    path('guardar_anulados/', views.guardar_anulados, name='guardar_anulados'),
]
