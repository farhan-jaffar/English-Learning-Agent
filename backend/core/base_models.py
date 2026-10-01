from django.db import models

class BaseTimeModel(models.Model):
    """
    Abstract base model providing self-updating created_at and updated_at fields.
    created_at is explicitly indexed for efficient time-based table partitioning.
    """
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True
