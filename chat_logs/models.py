"""Chat log model — records every AI interaction with token counts and INR cost."""

from django.db import models


class ChatLog(models.Model):
    MODULE_CHOICES = [
        ('USB', 'Unified Strategy Builder'),
        ('ISE', 'Indicator Signal Engine'),
        ('ISB', 'Inbound Signal Bridge'),
        ('RES', 'Rapid Execution Scalper'),
        ('MLH', 'Multi-Leg Hedger'),
    ]

    timestamp       = models.DateTimeField(auto_now_add=True, db_index=True)
    module          = models.CharField(max_length=10, choices=MODULE_CHOICES, db_index=True)
    session_id      = models.CharField(max_length=100, db_index=True)
    user_message    = models.TextField()
    ai_response     = models.TextField()
    input_tokens    = models.IntegerField(default=0)
    output_tokens   = models.IntegerField(default=0)
    total_tokens    = models.IntegerField(default=0)
    cost_usd        = models.DecimalField(max_digits=12, decimal_places=8, default=0)
    cost_inr        = models.DecimalField(max_digits=12, decimal_places=4, default=0)
    model_used      = models.CharField(max_length=100, default='')

    class Meta:
        ordering = ['-timestamp']

    def __str__(self):
        return f"[{self.module}] {self.session_id} @ {self.timestamp:%Y-%m-%d %H:%M:%S}"
