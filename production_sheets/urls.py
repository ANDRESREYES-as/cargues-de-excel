from django.urls import path
from . import views
from . import admin_views

app_name = 'production_sheets'

urlpatterns = [
    path('upload/', views.process_production_sheet, name='upload'),
    path('detail/<int:pk>/', views.production_sheet_detail, name='production_sheet_detail'),
    path('historic/', views.production_sheets_historic, name='historic'),
    
    # URLs administrativas (solo accesibles por URL directa)
    path('admin/list/', admin_views.AdminListView.as_view(), name='admin_list'),
    path('admin/edit/<int:pk>/', admin_views.AdminEditView.as_view(), name='admin_edit'),
    path('admin/delete/<int:pk>/', admin_views.AdminDeleteView.as_view(), name='admin_delete'),
]