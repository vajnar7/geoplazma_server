from django.urls import path

from areas.rest import Areas

urlpatterns = [
    path('', Areas.as_view(), name='areas'),
]