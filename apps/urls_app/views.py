import logging
from django.shortcuts import render
from django.views import View
from django.http import HttpResponsePermanentRedirect, Http404, JsonResponse
from django.core.cache import cache
from django.utils import timezone

from .models import ShortURL
from .forms import ShortURLForm
from apps.analytics_app.tasks import record_click_task

logger = logging.getLogger('linkforge')

class CreateURLView(View):
    """
    Handles request to create short URLs.
    Includes forms parsing and rendering.
    """
    def get(self, request):
        form = ShortURLForm()
        return render(request, 'urls_app/create.html', {'form': form})

    def post(self, request):
        form = ShortURLForm(request.POST)
        if form.is_valid():
            short_url = form.save(commit=False)
            custom_code = form.cleaned_data.get('custom_code')
            if custom_code:
                short_url.short_code = custom_code
            short_url.save()
            
            scheme = request.scheme
            host = request.get_host()
            absolute_short_url = f"{scheme}://{host}/{short_url.short_code}"
            
            logger.info(f"Created short URL: {short_url.short_code} -> {short_url.original_url}")
            
            # Check if JSON is expected (helpful for API-like scripts/tests)
            if request.headers.get('x-requested-with') == 'XMLHttpRequest' or 'application/json' in request.META.get('HTTP_ACCEPT', ''):
                return JsonResponse({
                    "short_code": short_url.short_code,
                    "original_url": short_url.original_url,
                    "short_url": absolute_short_url
                }, status=201)
                
            return render(request, 'urls_app/create.html', {
                'form': ShortURLForm(),
                'short_url': short_url,
                'absolute_short_url': absolute_short_url
            })
            
        if request.headers.get('x-requested-with') == 'XMLHttpRequest' or 'application/json' in request.META.get('HTTP_ACCEPT', ''):
            return JsonResponse({"errors": form.errors}, status=400)
            
        return render(request, 'urls_app/create.html', {'form': form})


class RedirectURLView(View):
    """
    Performs high-performance redirection.
    Utilizes Redis cache for O(1) response, falling back to PostgreSQL database.
    """
    def get(self, request, short_code):
        cache_key = f"short_url:{short_code}"
        
        cached_data = None
        try:
            cached_data = cache.get(cache_key)
        except Exception as e:
            logger.error(f"Cache backend error while fetching code '{short_code}': {str(e)}")

        if cached_data:
            original_url = cached_data.get('original_url')
            short_url_id = cached_data.get('id')
            logger.info(f"Redirect: Cache hit for '{short_code}' -> {original_url}")
        else:
            try:
                short_url = ShortURL.objects.get(short_code=short_code)
                original_url = short_url.original_url
                short_url_id = short_url.id
                logger.info(f"Redirect: Cache miss. Database hit for '{short_code}' -> {original_url}")
                
                # Populating cache (24 hours TTL)
                cache_data = {'original_url': original_url, 'id': short_url_id}
                try:
                    cache.set(cache_key, cache_data, timeout=86400)
                except Exception as cache_err:
                    logger.error(f"Failed to cache code '{short_code}': {str(cache_err)}")
            except ShortURL.DoesNotExist:
                logger.warning(f"Redirect failed: Short code '{short_code}' does not exist.")
                raise Http404("Short URL not found")

        # Capture visitor metadata for async tracking
        ip_address = self.get_client_ip(request)
        user_agent = request.META.get('HTTP_USER_AGENT', '')
        referrer = request.META.get('HTTP_REFERER', '')
        clicked_at = timezone.now().isoformat()
        
        # Trigger Celery Task asynchronously to record analytics (PostgreSQL writes are offloaded)
        try:
            from django.conf import settings
            if getattr(settings, 'CELERY_TASK_ALWAYS_EAGER', False):
                import sys
                if 'test' in sys.argv:
                    # In tests: run synchronously to allow test assertions and avoid DB teardown races
                    record_click_task(short_url_id, ip_address, user_agent, referrer, clicked_at)
                else:
                    # Local dev without Redis: run task in a background daemon thread
                    import threading
                    threading.Thread(
                        target=record_click_task,
                        args=[short_url_id, ip_address, user_agent, referrer, clicked_at],
                        daemon=True
                    ).start()
            else:
                # Production: push to Celery/Redis queue
                record_click_task.apply_async(
                    args=[short_url_id, ip_address, user_agent, referrer, clicked_at],
                    retry=False
                )
        except Exception as e:
            logger.error(f"Background task routing failure for code '{short_code}': {str(e)}")
            
        # Return HTTP 301 Permanent Redirect
        return HttpResponsePermanentRedirect(original_url)

    def get_client_ip(self, request):
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0].strip()
        else:
            ip = request.META.get('REMOTE_ADDR', '127.0.0.1')
        return ip
