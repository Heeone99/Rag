from django.db import models

class LectureSummary(models.Model):
    unique_name = models.CharField(max_length=100, unique=True)
    collection_name = models.CharField(max_length=100, unique=True, null=True, blank=True)
    db_path = models.CharField(max_length=255, null=True, blank=True)
    summary = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.unique_name
