import logging
from collections import Counter
from datetime import timedelta
from django.shortcuts import render
from django.views import View
from django.utils import timezone
from django.db.models import Count
from django.core.cache import cache

from apps.urls_app.models import ShortURL
from apps.analytics_app.models import ClickEvent

logger = logging.getLogger('linkforge')

class StatsDashboardView(View):
    """
    Renders the LinkForge metrics and analytics dashboard.
    Leverages Redis caching for compiled analytics to avoid heavy aggregation on PostgreSQL.
    """
    def get(self, request):
        cache_key = "dashboard_stats"
        stats = None
        
        try:
            stats = cache.get(cache_key)
        except Exception as e:
            logger.error(f"Dashboard: Cache retrieval failed: {str(e)}")

        if not stats:
            logger.info("Dashboard: Cache miss. Re-compiling analytics...")
            
            # Simple counts
            total_urls = ShortURL.objects.count()
            total_clicks = ClickEvent.objects.count()
            
            # Top 10 most clicked URLs (Uses indexed click_count field)
            top_urls_query = ShortURL.objects.order_by('-click_count')[:10]
            top_urls = [
                {
                    "short_code": url.short_code,
                    "original_url": url.original_url,
                    "click_count": url.click_count,
                    "created_at": url.created_at.strftime('%Y-%m-%d')
                }
                for url in top_urls_query
            ]
            
            # Country distribution
            country_dist = list(
                ClickEvent.objects.values('country')
                .annotate(count=Count('id'))
                .order_by('-count')[:5]
            )
            
            # Browser distribution
            browser_dist = list(
                ClickEvent.objects.values('browser')
                .annotate(count=Count('id'))
                .order_by('-count')[:5]
            )
            
            # Operating System distribution
            os_dist = list(
                ClickEvent.objects.values('operating_system')
                .annotate(count=Count('id'))
                .order_by('-count')[:5]
            )
            
            # Compile time-series data
            daily_data, weekly_data, monthly_data = self.get_time_series_data()
            
            avg_clicks = round(total_clicks / total_urls, 1) if total_urls > 0 else 0.0

            stats = {
                'total_urls': total_urls,
                'total_clicks': total_clicks,
                'avg_clicks': avg_clicks,
                'top_urls': top_urls,
                'country_dist': country_dist,
                'browser_dist': browser_dist,
                'os_dist': os_dist,
                'daily_data': daily_data,
                'weekly_data': weekly_data,
                'monthly_data': monthly_data,
                'computed_at': timezone.now().strftime('%Y-%m-%d %H:%M:%S UTC')
            }
            
            try:
                # Cache stats for 5 minutes (300 seconds)
                cache.set(cache_key, stats, timeout=300)
            except Exception as e:
                logger.error(f"Dashboard: Cache write failed: {str(e)}")
        else:
            logger.info("Dashboard: Cache hit. Returning cached analytics.")

        # Generate a sample relative URL for redirection lookup
        scheme = request.scheme
        host = request.get_host()
        stats['base_short_url'] = f"{scheme}://{host}/"

        return render(request, 'dashboard_app/stats.html', stats)

    def get_time_series_data(self):
        """
        Gathers time-series click events and aggregates them database-agnostically in Python.
        """
        now = timezone.now()
        
        # 1. Daily clicks (Last 7 Days)
        seven_days_ago = now - timedelta(days=7)
        daily_events = ClickEvent.objects.filter(clicked_at__gte=seven_days_ago).values('clicked_at')
        daily_counts = Counter()
        for e in daily_events:
            dt = e['clicked_at'].strftime('%Y-%m-%d')
            daily_counts[dt] += 1
            
        # Ensure last 7 days are initialized even if they have 0 clicks
        for i in range(8):
            day_str = (now - timedelta(days=i)).strftime('%Y-%m-%d')
            if day_str not in daily_counts:
                daily_counts[day_str] = 0
                
        # 2. Weekly clicks (Last 4 Weeks)
        four_weeks_ago = now - timedelta(weeks=4)
        weekly_events = ClickEvent.objects.filter(clicked_at__gte=four_weeks_ago).values('clicked_at')
        weekly_counts = Counter()
        for e in weekly_events:
            dt = e['clicked_at'].strftime('%Y-W%U')
            weekly_counts[dt] += 1
            
        for i in range(5):
            week_str = (now - timedelta(weeks=i)).strftime('%Y-W%U')
            if week_str not in weekly_counts:
                weekly_counts[week_str] = 0
                
        # 3. Monthly clicks (Last 6 Months)
        six_months_ago = now - timedelta(days=180)
        monthly_events = ClickEvent.objects.filter(clicked_at__gte=six_months_ago).values('clicked_at')
        monthly_counts = Counter()
        for e in monthly_events:
            dt = e['clicked_at'].strftime('%Y-%m')
            monthly_counts[dt] += 1
            
        for i in range(6):
            # approximate 30 days per month
            month_str = (now - timedelta(days=30 * i)).strftime('%Y-%m')
            if month_str not in monthly_counts:
                monthly_counts[month_str] = 0

        # Sort chronologically
        daily_data = [{"label": k, "value": v} for k, v in sorted(daily_counts.items())]
        weekly_data = [{"label": k, "value": v} for k, v in sorted(weekly_counts.items())]
        monthly_data = [{"label": k, "value": v} for k, v in sorted(monthly_counts.items())]
        
        return daily_data, weekly_data, monthly_data
