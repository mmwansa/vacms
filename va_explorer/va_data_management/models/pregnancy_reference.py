import uuid

from django.db import models
from simple_history.models import HistoricalRecords


class PregnancyFieldReference(models.Model):
    """Reference mapping of pregnancy form fields to choice lists."""

    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    name = models.CharField(max_length=255, unique=True)
    list_name = models.CharField(max_length=255)
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)
    history = HistoricalRecords()

    def __str__(self):
        return f"{self.name} -> {self.list_name}"


class PregnancyChoiceReference(models.Model):
    """Reference mapping of list values to labels."""

    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    list_name = models.CharField(max_length=255)
    name = models.CharField(max_length=255)
    label = models.TextField(blank=True)
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)
    history = HistoricalRecords()

    class Meta:
        unique_together = ("list_name", "name")

    def __str__(self):
        return f"{self.list_name}:{self.name} -> {self.label}"
