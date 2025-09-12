from django.urls import path
from . import admin_views

app_name = 'custom_admin'

urlpatterns = [
    # Panel principal
    path('', admin_views.AdminHomeView.as_view(), name='home'),
    
    # Procesos Excel
    path('excel/', admin_views.ExcelProcessListView.as_view(), name='excel_process_list'),
    path('excel/delete/<int:pk>/', admin_views.ExcelProcessDeleteView.as_view(), name='excel_process_delete'),
    
    # Registros Excel
    path('registros/', admin_views.RegistroExcelListView.as_view(), name='registro_excel_list'),
    path('registros/edit/<int:pk>/', admin_views.RegistroExcelEditView.as_view(), name='registro_excel_edit'),
    path('registros/delete/<int:pk>/', admin_views.RegistroExcelDeleteView.as_view(), name='registro_excel_delete'),
    
    # Procesos PDF
    path('pdf/', admin_views.PDFProcessListView.as_view(), name='pdf_process_list'),
    path('pdf/delete/<int:pk>/', admin_views.PDFProcessDeleteView.as_view(), name='pdf_process_delete'),
    
    # Planillas de Producción
    path('production/', admin_views.ProductionSheetListView.as_view(), name='production_sheet_list'),
    path('production/edit/<int:pk>/', admin_views.ProductionSheetEditView.as_view(), name='production_sheet_edit'),
    path('production/delete/<int:pk>/', admin_views.ProductionSheetDeleteView.as_view(), name='production_sheet_delete'),
    
    # Detalles de Producción
    path('details/', admin_views.ProductionDetailListView.as_view(), name='production_detail_list'),
    path('details/edit/<int:pk>/', admin_views.ProductionDetailEditView.as_view(), name='production_detail_edit'),
    path('details/delete/<int:pk>/', admin_views.ProductionDetailDeleteView.as_view(), name='production_detail_delete'),
]