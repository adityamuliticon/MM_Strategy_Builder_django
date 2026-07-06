from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0003_userbearertoken_cached_fields'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='userbearertoken',
            name='cached_point_balance',
        ),
        migrations.RemoveField(
            model_name='userbearertoken',
            name='cached_strategy_counts',
        ),
        migrations.RemoveField(
            model_name='userbearertoken',
            name='data_cached_at',
        ),
    ]
