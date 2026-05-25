from django.urls import path
from . import views

urlpatterns = [
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('', views.resumen, name='resumen'),
    path('resumen/', views.resumen, name='resumen'),
    path('registro-diario/', views.registro_diario, name='registro_diario'),
    path('predicciones/', views.predicciones, name='predicciones'),
    path('analisis-mermas/', views.analisis_mermas, name='analisis_mermas'),
    path('inventario/', views.inventario, name='inventario'),
    path('catalogo/', views.catalogo, name='catalogo'),
    path('ordenes-compra/', views.ordenes_compra, name='ordenes_compra'),
    path('reportes-financieros/', views.reportes_financieros, name='reportes_financieros'),
    path('modelo-estadistico/', views.modelo_estadistico, name='modelo_estadistico'),
    
    # APIs
    path('api/productos/', views.api_productos, name='api_productos'),
    path('api/ventas/', views.api_ventas, name='api_ventas'),
    path('api/insumos/', views.api_insumos, name='api_insumos'),
    path('api/ordenes/', views.api_ordenes, name='api_ordenes'),
    path('api/ordenes/<int:orden_id>/recibir/', views.api_recibir_orden, name='api_recibir_orden'),
    
    # ML APIs (llaman internamente al backend)
    path('api/ml/seed/', views.ml_cargar_seed, name='ml_seed'),
    path('api/ml/entrenar/', views.ml_entrenar, name='ml_entrenar'),
    path('api/ml/clima/', views.ml_sincronizar_clima, name='ml_clima'),
    path('api/ml/predicciones/', views.ml_generar_predicciones, name='ml_predicciones'),
    
    # Chatbot
    path('api/chatbot/', views.api_chatbot, name='chatbot'),
    
    # Reportes Financieros
    path('api/reportes/estado-resultados/', views.reportes_estado_resultados, name='reportes_estado'),
    path('api/reportes/ventas-diarias/', views.reportes_ventas_diarias, name='reportes_ventas'),
    path('api/reportes/rentabilidad/', views.reportes_rentabilidad, name='reportes_rentabilidad'),
    path('api/reportes/porcentaje/', views.reportes_porcentaje, name='reportes_porcentaje'),
]