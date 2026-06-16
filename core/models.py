from django.db import models
from django.conf import settings


class BaseModel(models.Model):
    """
    Abstract base model providing common timestamp and user tracking fields.
    
    All domain models should inherit from this to ensure consistent
    created_at, updated_at, and created_by fields across the application.
    """
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='%(class)s_created',
        verbose_name='Creado por',
    )

    class Meta:
        abstract = True
        ordering = ['-created_at']
