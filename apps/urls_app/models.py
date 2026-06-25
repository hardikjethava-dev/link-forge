from django.db import models

class ShortURL(models.Model):
    """
    Model representing a shortened URL mapping.
    """
    short_code = models.CharField(
        max_length=20, 
        unique=True, 
        db_index=True,
        help_text="Unique base62 short identifier."
    )
    original_url = models.URLField(
        max_length=2048,
        help_text="The destination URL."
    )
    click_count = models.PositiveIntegerField(
        default=0,
        help_text="Cache fallback click count counter."
    )
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['short_code']),
            models.Index(fields=['created_at']),
        ]

    def save(self, *args, **kwargs):
        if not self.short_code:
            from .utils import generate_unique_short_code
            self.short_code = generate_unique_short_code(ShortURL)
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.short_code} -> {self.original_url[:50]}"
