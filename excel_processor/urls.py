from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('upload/', views.upload_excel_web, name='upload_excel_web'),
    path('historico/', views.historico, name='historico'),
    path('exportar_excel_historico/', views.exportar_excel_historico, name='exportar_excel_historico'),
    path('upload_api/', views.upload_excel, name='upload_excel'),
    path('pdfs/', views.pdf_list, name='pdf_list'),
]
