from django.test import TestCase
from django.utils import timezone
from unittest.mock import patch, MagicMock

from apps.urls_app.models import ShortURL
from apps.analytics_app.models import ClickEvent
from apps.analytics_app.utils import parse_user_agent, get_country_from_ip
from apps.analytics_app.tasks import record_click_task

class UserAgentParsingTests(TestCase):
    def test_parse_standard_browser(self):
        # Chrome on Windows User Agent
        ua_str = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        browser, os_name = parse_user_agent(ua_str)
        self.assertIn("Chrome", browser)
        self.assertIn("Windows", os_name)

    def test_parse_empty_ua(self):
        browser, os_name = parse_user_agent("")
        self.assertEqual(browser, "Unknown")
        self.assertEqual(os_name, "Unknown")


class IPGeolocationTests(TestCase):
    def test_localhost_ip(self):
        country = get_country_from_ip("127.0.0.1")
        self.assertEqual(country, "Localhost")

    def test_private_class_a_ip(self):
        country = get_country_from_ip("10.0.0.1")
        self.assertEqual(country, "Local Network")

    @patch('urllib.request.urlopen')
    def test_public_ip_geolocates(self, mock_urlopen):
        # Mock API response
        mock_response = MagicMock()
        mock_response.read.return_value = b'{"status": "success", "country": "Canada"}'
        mock_urlopen.return_value.__enter__.return_value = mock_response

        country = get_country_from_ip("8.8.8.8")
        self.assertEqual(country, "Canada")

    @patch('urllib.request.urlopen')
    def test_api_timeout_returns_unknown(self, mock_urlopen):
        mock_urlopen.side_effect = Exception("Timeout")
        country = get_country_from_ip("8.8.8.8")
        self.assertEqual(country, "Unknown")


class AnalyticsCeleryTaskTests(TestCase):
    def setUp(self):
        self.url = ShortURL.objects.create(original_url="https://python.org")

    @patch('apps.analytics_app.tasks.get_country_from_ip')
    @patch('apps.analytics_app.tasks.parse_user_agent')
    def test_record_click_task_runs_successfully(self, mock_parse_ua, mock_get_country):
        mock_parse_ua.return_value = ("Firefox", "Linux")
        mock_get_country.return_value = "France"

        timestamp_iso = timezone.now().isoformat()
        
        # Invoke task synchronously
        res = record_click_task(
            short_url_id=self.url.id,
            ip_address="192.168.1.100",
            user_agent="Firefox UA",
            referrer="https://link.com",
            clicked_at_iso=timestamp_iso
        )

        self.assertTrue(res)
        
        # Verify ClickEvent was created
        click = ClickEvent.objects.get(short_url=self.url)
        self.assertEqual(click.browser, "Firefox")
        self.assertEqual(click.operating_system, "Linux")
        self.assertEqual(click.country, "France")
        self.assertEqual(click.referrer, "https://link.com")

        # Verify atomic click count increment
        self.url.refresh_from_db()
        self.assertEqual(self.url.click_count, 1)

    def test_record_click_non_existent_url_aborts(self):
        res = record_click_task(
            short_url_id=99999,
            ip_address="127.0.0.1",
            user_agent="UA",
            referrer="",
            clicked_at_iso=timezone.now().isoformat()
        )
        self.assertFalse(res)
