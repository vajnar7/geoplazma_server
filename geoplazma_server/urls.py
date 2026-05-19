from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from rest_framework.authtoken import views as auth_views
from areas.views import IndexView

urlpatterns = [
    # API endpoints
    path('api/', include('areas.urls')),
    path('token/', auth_views.obtain_auth_token),
    
    # Admin
    path('admin/', admin.site.urls),
    
    # Frontend
    path('', IndexView.as_view(), name='index'),
]

# Serve static files in development
if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

