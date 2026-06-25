from django.db import models
from apps.urls_app.models import ShortURL

class ClickEvent(models.Model):
    """
    Model representing a single URL click event.
    Stores detailed analytics captured asynchronously.
    """
    short_url = models.ForeignKey(
        ShortURL, 
        on_delete=models.CASCADE, 
        related_name='clicks',
        help_text="The associated shortened URL."
    )
    ip_address = models.GenericIPAddressField(
        null=True, 
        blank=True, 
        db_index=True,
        help_text="IP address of the visitor."
    )
    country = models.CharField(
        max_length=100, 
        default='Unknown', 
        db_index=True,
        help_text="Country resolved from the visitor's IP address."
    )
    browser = models.CharField(
        max_length=100, 
        default='Unknown', 
        db_index=True,
        help_text="Browser name resolved from the visitor's User-Agent."
    )
    operating_system = models.CharField(
        max_length=100, 
        default='Unknown', 
        db_index=True,
        help_text="Operating system resolved from the visitor's User-Agent."
    )
    referrer = models.TextField(
        null=True, 
        blank=True,
        help_text="HTTP Referer header."
    )
    user_agent = models.TextField(
        null=True, 
        blank=True,
        help_text="Raw HTTP User-Agent header."
    )
    clicked_at = models.DateTimeField(
        db_index=True,
        help_text="Exact timestamp of the redirection."
    )

    class Meta:
        ordering = ['-clicked_at']
        indexes = [
            models.Index(fields=['clicked_at']),
            models.Index(fields=['short_url', 'clicked_at']),
            models.Index(fields=['country']),
            models.Index(fields=['browser']),
            models.Index(fields=['operating_system']),
        ]

    def __str__(self):
        return f"Click on {self.short_url.short_code} at {self.clicked_at}"
