from django.test import TestCase, Client
from django.urls import reverse
from apps.urls_app.models import ShortURL
from apps.urls_app.utils import encode_base62, decode_base62, generate_random_code
from apps.urls_app.forms import ShortURLForm

class Base62Tests(TestCase):
    def test_encode_zero(self):
        self.assertEqual(encode_base62(0), "0")

    def test_encode_large_number(self):
        val = 123456789
        encoded = encode_base62(val)
        decoded = decode_base62(encoded)
        self.assertEqual(decoded, val)

    def test_encode_negative_raises_error(self):
        with self.assertRaises(ValueError):
            encode_base62(-5)

    def test_decode_invalid_character_raises_error(self):
        with self.assertRaises(ValueError):
            decode_base62("invalid_char_#")


class ShortURLModelTests(TestCase):
    def test_short_code_generated_automatically(self):
        url = ShortURL.objects.create(original_url="https://google.com")
        self.assertIsNotNone(url.short_code)
        self.assertEqual(len(url.short_code), 6)

    def test_custom_short_code_preserved(self):
        url = ShortURL.objects.create(original_url="https://google.com", short_code="google")
        self.assertEqual(url.short_code, "google")


class ShortURLFormTests(TestCase):
    def test_valid_original_url(self):
        form = ShortURLForm(data={"original_url": "https://github.com"})
        self.assertTrue(form.is_valid())

    def test_invalid_original_url(self):
        form = ShortURLForm(data={"original_url": "not-a-url"})
        self.assertFalse(form.is_valid())

    def test_valid_custom_code(self):
        form = ShortURLForm(data={"original_url": "https://github.com", "custom_code": "my-git_1"})
        self.assertTrue(form.is_valid())

    def test_invalid_custom_code_chars(self):
        form = ShortURLForm(data={"original_url": "https://github.com", "custom_code": "git#code!"})
        self.assertFalse(form.is_valid())
        self.assertIn("custom_code", form.errors)

    def test_duplicate_custom_code_rejected(self):
        ShortURL.objects.create(original_url="https://existing.com", short_code="taken")
        form = ShortURLForm(data={"original_url": "https://new.com", "custom_code": "taken"})
        self.assertFalse(form.is_valid())


class CreateURLViewTests(TestCase):
    def setUp(self):
        self.client = Client()

    def test_get_creation_page(self):
        response = self.client.get(reverse('create_url'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'urls_app/create.html')

    def test_post_creation_success(self):
        response = self.client.post(reverse('create_url'), data={"original_url": "https://news.ycombinator.com"})
        self.assertEqual(response.status_code, 200)
        self.assertTrue(ShortURL.objects.filter(original_url="https://news.ycombinator.com").exists())

    def test_post_json_api_response(self):
        response = self.client.post(
            reverse('create_url'), 
            data={"original_url": "https://reddit.com"},
            headers={"x-requested-with": "XMLHttpRequest"}
        )
        self.assertEqual(response.status_code, 201)
        data = response.json()
        self.assertIn("short_code", data)
        self.assertIn("short_url", data)
