from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0002_userbearertoken_encrypted_password'),
    ]

    operations = [
        migrations.AddField(
            model_name='userbearertoken',
            name='cached_point_balance',
            field=models.FloatField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='userbearertoken',
            name='cached_strategy_counts',
            field=models.JSONField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='userbearertoken',
            name='data_cached_at',
            field=models.DateTimeField(blank=True, null=True),
        ),
    ]
