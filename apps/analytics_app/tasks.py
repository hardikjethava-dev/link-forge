import logging
from celery import shared_task
from django.utils import timezone
from django.db import transaction
from django.db.models import F
from django.utils.dateparse import parse_datetime

from apps.urls_app.models import ShortURL
from .models import ClickEvent
from .utils import parse_user_agent, get_country_from_ip

logger = logging.getLogger('linkforge')

@shared_task(name="apps.analytics_app.tasks.record_click_task")
def record_click_task(short_url_id, ip_address, user_agent, referrer, clicked_at_iso):
    """
    Celery task run asynchronously.
    Resolves country from IP, extracts OS/Browser details from User-Agent,
    persists the ClickEvent, and atomically increments the click count of the ShortURL.
    """
    logger.info(f"Celery task started: Processing click analytics for short_url_id={short_url_id}")
    
    try:
        short_url = ShortURL.objects.get(id=short_url_id)
    except ShortURL.DoesNotExist:
        logger.error(f"Celery task aborted: ShortURL ID {short_url_id} not found in database.")
        return False

    # Resolve visitor details (potentially slow third-party API call geolocating IP is safe here)
    browser, operating_system = parse_user_agent(user_agent)
    country = get_country_from_ip(ip_address)
    
    clicked_at = parse_datetime(clicked_at_iso)
    if not clicked_at:
        clicked_at = timezone.now()

    # Save to database and update counter atomically
    try:
        with transaction.atomic():
            # Persist visitor click detail record
            ClickEvent.objects.create(
                short_url=short_url,
                ip_address=ip_address,
                country=country,
                browser=browser,
                operating_system=operating_system,
                referrer=referrer,
                user_agent=user_agent,
                clicked_at=clicked_at
            )
            
            # Atomically increment click count on ShortURL using ORM F expression
            ShortURL.objects.filter(id=short_url_id).update(click_count=F('click_count') + 1)
            
        logger.info(f"Celery task finished successfully: Click recorded for '{short_url.short_code}' from {country}")
        return True
    except Exception as e:
        logger.error(f"Celery task failed to record click: {str(e)}")
        # Raise so Celery knows the task failed (and can retry if configured)
        raise e
