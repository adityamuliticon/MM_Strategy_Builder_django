import uuid
from django.db import models


class AppUser(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    email = models.EmailField(unique=True)
    display_name = models.CharField(max_length=200, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    last_login = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-last_login', '-created_at']

    def __str__(self):
        return self.email


class UserBearerToken(models.Model):
    user = models.OneToOneField(AppUser, on_delete=models.CASCADE, related_name='bearer_token')
    token = models.TextField()
    encrypted_password = models.TextField(blank=True, default='')
    expires_at = models.DateTimeField(null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True)
    # Cached API data updated on every balance/strategy-counts page load
    cached_point_balance = models.FloatField(null=True, blank=True)
    cached_strategy_counts = models.JSONField(null=True, blank=True)
    data_cached_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"Token({self.user.email})"
