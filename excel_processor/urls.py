from django.urls import path
from . import views
from . import views_batch
from . import views_historic

urlpatterns = [
    path('', views.home, name='home'),
    path('upload/', views.upload_excel_web, name='upload_excel_web'),
    path('historico/', views.historico, name='historico'),
    path('production/historic/', views_historic.exportar_excel_historico, name='exportar_excel_historico'),
    path('exportar-manifiestos/', views_historic.form_exportar_manifiestos, name='form_exportar_manifiestos'),
    path('upload_api/', views.upload_excel, name='upload_excel'),
    path('pdfs/', views.pdf_list, name='pdf_list'),
    path('pdf-batch/', views_batch.pdf_batch_process, name='pdf_batch_process'),
    path('manifiestos/', views.manifiestos, name='manifiestos'),
    path('produccion/', views.produccion, name='produccion'),
]
