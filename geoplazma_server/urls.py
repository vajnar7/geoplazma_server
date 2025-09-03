from django.contrib import admin
from django.urls import path, include
from rest_framework.authtoken import views as auth_views
from areas.rest import Login, LogFile

urlpatterns = [
    path('userlogin/', Login.as_view(), name='Login'),
    path('logfile/', LogFile.as_view(), name='LogFile'),
    path('areas/', include('areas.urls')),
    path('admin/', admin.site.urls),
    path('token/', auth_views.obtain_auth_token),
]
