
from django.contrib import sitemaps
from django.urls import reverse
from django.conf import settings

class StaticViewSitemap(sitemaps.Sitemap):
    changefreq = 'monthly'
    protocol = 'https' if not settings.DEBUG else 'http'
    static_priorities = {
        'anon-landing': 1.0,
        'docs-quick-start-guide':0.9,
        'docs-home':0.7,
        'docs-company-export':0.7,
        'docs-account-tags':0.7,
        'docs-assets':0.7,
        'docs-liabilites':0.7,
        'docs-equity':0.7,
        'docs-revenue':0.7,
        'docs-expense':0.7,
        'docs-balance-sheet':0.7,
        'docs-income-statement':0.7,
        'docs-cash-flow-statement':0.7,
        'docs-trial-balance':0.7,
        'docs-statement-of-retained-earnings':0.7,
        'docs-entry-types':0.7,
        'anon-pp':0.5,
        'anon-tos':0.5,
    }

    def items(self):
        return list(self.static_priorities.keys())

    def location(self, item):
        return reverse(item)

    def priority(self, item):
        return self.static_priorities[item]



metalacc_sitemaps = {
    'static':StaticViewSitemap,
}
