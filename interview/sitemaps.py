from django.contrib.sitemaps import Sitemap
from django.urls import reverse


class StaticViewSitemap(Sitemap):
    changefreq = 'weekly'

    def items(self):
        # Public pages only; pages behind login are not useful to search engines
        return ['interview:index', 'interview:contact', 'interview:feedback',
                'interview:privacy_policy', 'interview:terms_of_use']

    def location(self, item):
        return reverse(item)
