from django.contrib import admin
from django.contrib.sitemaps.views import sitemap
from django.urls import path, include

from interview.sitemaps import StaticViewSitemap

sitemaps = {'static': StaticViewSitemap}

urlpatterns = [
    path('', include('interview.urls')),
    path('admin/', admin.site.urls),
    path('accounts/', include('allauth.urls')),
    path('sitemap.xml', sitemap, {'sitemaps': sitemaps}, name='django.contrib.sitemaps.views.sitemap'),
]
