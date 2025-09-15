from django.urls import path
from . import views

urlpatterns = [
    path('upload/', views.upload_files, name='upload_files'),
    path('resultados/', views.ver_resultados, name='ver_resultados'),
]