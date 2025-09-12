from django.urls import path
from . import views

app_name = 'production_sheets'

urlpatterns = [
    path('upload/', views.process_production_sheet, name='upload'),
    path('detail/<int:pk>/', views.production_sheet_detail, name='production_sheet_detail'),
    path('historic/', views.production_sheets_historic, name='historic'),
]