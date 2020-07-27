
from django.contrib import admin
from django.urls import path, include
from django.conf import settings

urlpatterns = [
    path('api/v1/', include('api.urls')),
    path('', include('website.urls')),
]

handler404 = 'website.views.handler404'

if settings.DEBUG:
    urlpatterns.append(path('admin/', admin.site.urls))
