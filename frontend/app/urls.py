# app/urls.py
from django.urls import path
from . import views

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('configuracion/', views.enviar_configuracion, name='configuracion'),
    path('consumo/', views.enviar_consumo, name='consumo'),
    path('operaciones/inicializar/', views.inicializar_sistema, name='inicializar'),
    path('operaciones/consultar/', views.consultar_datos, name='consultar'),
    path('operaciones/crear/', views.crear_datos, name='crear'),
    path('operaciones/facturacion/', views.proceso_facturacion, name='facturacion'),
    path('reportes/detalle/<int:factura_id>/', views.reporte_detalle_factura, name='detalle_factura'),
    path('reportes/ventas/', views.reporte_analisis_ventas, name='analisis_ventas'),
    path('ayuda/estudiante/', views.info_estudiante, name='info_estudiante'),
]