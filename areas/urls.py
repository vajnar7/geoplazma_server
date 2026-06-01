from django.urls import path

from areas.rest import Areas, Login, Status, Logout, LogFile, StartNTRIP

urlpatterns = [
    path('areas/', Areas.as_view(), name='areas'),
    path('login/', Login.as_view(), name='login'),
    path('status/', Status.as_view(), name='status'),
    path('logout/', Logout.as_view(), name='logout'),
    path('logfile/', LogFile.as_view(), name='logfile'),
    path('ntrip/', StartNTRIP.as_view(), name='ntrip'),
]