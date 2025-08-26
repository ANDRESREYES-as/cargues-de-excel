from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
<<<<<<< HEAD
    path('',include('excel_processor.urls')),
=======
    path('', include('excel_processor.urls')),
>>>>>>> 266efed70bdfc9ac9684e988c6ce63eb5256dc2d
    path('admin/', admin.site.urls),
    path('excel/', include('excel_processor.urls')),
    path('excel_processor/', include('excel_processor.urls')),
]

# IMPORTANTE: Esta línea debe estar al final
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
