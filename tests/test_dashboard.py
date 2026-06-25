from django.test import TestCase, Client, override_settings
from django.urls import reverse
from django.core.cache import cache
from unittest.mock import patch

from apps.urls_app.models import ShortURL
from apps.analytics_app.models import ClickEvent

class RedirectViewTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.url = ShortURL.objects.create(original_url="https://django-project.org", short_code="django")
        cache.clear()

    def test_redirect_hits_database_and_caches_result(self):
        cache_key = f"short_url:{self.url.short_code}"
        self.assertIsNone(cache.get(cache_key))

        # First access (Cache Miss -> DB hit)
        response = self.client.get(reverse('redirect_url', kwargs={"short_code": self.url.short_code}))
        self.assertEqual(response.status_code, 301)
        self.assertEqual(response.url, self.url.original_url)

        # Check cache now populated
        cached = cache.get(cache_key)
        self.assertIsNotNone(cached)
        self.assertEqual(cached['original_url'], self.url.original_url)
        self.assertEqual(cached['id'], self.url.id)

    def test_redirect_resolves_from_cache(self):
        cache_key = f"short_url:{self.url.short_code}"
        cache.set(cache_key, {"original_url": "https://cached-url.com", "id": self.url.id}, timeout=30)

        # Access (Cache Hit)
        response = self.client.get(reverse('redirect_url', kwargs={"short_code": self.url.short_code}))
        self.assertEqual(response.status_code, 301)
        # Should redirect to cached destination instead of database destination
        self.assertEqual(response.url, "https://cached-url.com")

    def test_non_existent_short_code_returns_404(self):
        response = self.client.get(reverse('redirect_url', kwargs={"short_code": "unknown_code"}))
        self.assertEqual(response.status_code, 404)


class DashboardViewTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.url = ShortURL.objects.create(original_url="https://linkforge.io", short_code="forge")
        cache.clear()

    def test_dashboard_renders_metrics_and_caches_response(self):
        response = self.client.get(reverse('stats_dashboard'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'dashboard_app/stats.html')

        # Check caching of compiled dictionary
        stats = cache.get("dashboard_stats")
        self.assertIsNotNone(stats)
        self.assertEqual(stats['total_urls'], 1)
        self.assertEqual(stats['total_clicks'], 0)


@override_settings(
    RATE_LIMIT_CREATION_LIMIT=3,
    RATE_LIMIT_CREATION_WINDOW=60
)
class RateLimitingMiddlewareTests(TestCase):
    def setUp(self):
        self.client = Client()
        cache.clear()

    def test_rate_limiter_allows_under_limit(self):
        for _ in range(3):
            response = self.client.post(reverse('create_url'), data={"original_url": "https://test.com"})
            self.assertEqual(response.status_code, 200) # Form renders / success

    def test_rate_limiter_blocks_above_limit(self):
        # Consume limit of 3
        for _ in range(3):
            self.client.post(reverse('create_url'), data={"original_url": "https://test.com"})

        # 4th request should block
        response = self.client.post(reverse('create_url'), data={"original_url": "https://exceeded.com"})
        self.assertEqual(response.status_code, 429)
        self.assertTemplateUsed(response, 'urls_app/error.html')
