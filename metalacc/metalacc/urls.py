
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.contrib.sitemaps.views import sitemap

from metalacc.sitemap import metalacc_sitemaps

urlpatterns = [
    path('api/v1/', include('api.urls')),
    path('', include('website.urls')),
    path('sitemap.xml', sitemap, {'sitemaps': metalacc_sitemaps}, name='django.contrib.sitemaps.views.sitemap'),
]

if settings.SHOW_DOCS:
    urlpatterns.append(path('docs/', include('docs.urls')))

if settings.DEBUG:
    urlpatterns.append(path('admin/', admin.site.urls))
