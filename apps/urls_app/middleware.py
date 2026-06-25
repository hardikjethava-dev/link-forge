import logging
from django.core.cache import cache
from django.conf import settings
from django.shortcuts import render
from django.http import JsonResponse

logger = logging.getLogger('linkforge')

class RedisRateLimitMiddleware:
    """
    Middleware that implements a Redis-backed rate limiting mechanism.
    Enforces a configurable limit of POST requests to the URL creation view.
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        return self.get_response(request)

    def process_view(self, request, view_func, view_args, view_kwargs):
        # Only rate limit URL creation (POST request on 'create_url')
        resolver_match = getattr(request, 'resolver_match', None)
        if request.method == 'POST' and resolver_match and resolver_match.url_name == 'create_url':
            ip = self.get_client_ip(request)
            limit = getattr(settings, 'RATE_LIMIT_CREATION_LIMIT', 100)
            window = getattr(settings, 'RATE_LIMIT_CREATION_WINDOW', 3600)
            
            cache_key = f"rate_limit:create_url:{ip}"
            
            try:
                current_requests = cache.get(cache_key)
            except Exception as e:
                # If cache is down, fail open but log error to not break production creation
                logger.error(f"Rate Limiter: cache error: {str(e)}")
                return None
                
            if current_requests is None:
                try:
                    cache.set(cache_key, 1, timeout=window)
                except Exception as e:
                    logger.error(f"Rate Limiter: cache set error: {str(e)}")
            elif int(current_requests) >= limit:
                logger.warning(f"Rate limit exceeded for IP: {ip}. Requests: {current_requests}, Limit: {limit}/{window}s")
                
                # Check format response type
                accept_header = request.META.get('HTTP_ACCEPT', '')
                if 'application/json' in accept_header or request.headers.get('x-requested-with') == 'XMLHttpRequest':
                    return JsonResponse({
                        "error": "Rate limit exceeded",
                        "message": f"You have exceeded the limit of {limit} URL creations per hour. Please try again later."
                    }, status=429)
                
                return render(request, 'urls_app/error.html', {
                    "title": "Too Many Requests",
                    "message": f"You have exceeded the rate limit of {limit} URL creations per hour. Please try again later."
                }, status=429)
            else:
                try:
                    cache.incr(cache_key)
                except ValueError:
                    # Occurs if key expires between get and incr
                    try:
                        cache.set(cache_key, 1, timeout=window)
                    except Exception as e:
                        logger.error(f"Rate Limiter: cache set retry error: {str(e)}")
                except Exception as e:
                    logger.error(f"Rate Limiter: cache incr error: {str(e)}")
                    
        return None

    def get_client_ip(self, request):
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0].strip()
        else:
            ip = request.META.get('REMOTE_ADDR', '127.0.0.1')
        return ip
