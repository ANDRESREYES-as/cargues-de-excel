from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('excel/', include('excel_processor.urls')),
    path('production/', include('production_sheets.urls', namespace='production_sheets')),
    path('secretadmin/', include('backend.admin_urls', namespace='custom_admin')),  # Nueva URL secreta
    path('calculadora/', include('excel_calculator.urls')),  # Nueva app de calculadora
]

if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
