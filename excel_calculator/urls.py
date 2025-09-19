from django.urls import path
from . import views
from . import views_historico

urlpatterns = [
    path('upload/', views.upload_files, name='upload_files'),
    path('resultados/', views.ver_resultados, name='ver_resultados'),
    path('historico/', views_historico.historico_calculos, name='historico_calculos'),
    path('exportar/', views.exportar_excel, name='exportar_excel'),
    path('exportar-pivotado/', views.exportar_excel_pivotado, name='exportar_excel_pivotado'),
]