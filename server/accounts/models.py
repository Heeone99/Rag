from django.db import models

class User(models.Model):
    """
    MySQL User 모델
    """
    username = models.CharField(max_length=150, unique=True)
    password = models.CharField(max_length=255)

    def __str__(self):
        return self.username
