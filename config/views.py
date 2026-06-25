from django.http import JsonResponse
from django.db import connection
from django.core.cache import cache
import logging

logger = logging.getLogger('linkforge')

def health_check(request):
    """
    Service health check endpoint.
    Checks database connection and cache (Redis) responsiveness.
    Returns HTTP 200 if healthy, HTTP 503 if any service is down.
    """
    status_code = 200
    health_status = {
        "status": "healthy",
        "database": "ok",
        "cache": "ok",
    }
    
    # Check Database
    try:
        connection.ensure_connection()
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1;")
    except Exception as e:
        logger.error(f"Health check: Database connection failed: {str(e)}")
        health_status["database"] = "down"
        health_status["status"] = "unhealthy"
        status_code = 503
        
    # Check Cache (Redis)
    try:
        cache.set("health_check_ping", "pong", timeout=5)
        ping_res = cache.get("health_check_ping")
        if ping_res != "pong":
            raise Exception(f"Cache write/read mismatch. Expected 'pong', got '{ping_res}'")
    except Exception as e:
        logger.error(f"Health check: Cache connection failed: {str(e)}")
        health_status["cache"] = "down"
        health_status["status"] = "unhealthy"
        status_code = 503

    return JsonResponse(health_status, status=status_code)
