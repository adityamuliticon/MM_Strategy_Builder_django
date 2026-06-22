from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='userbearertoken',
            name='encrypted_password',
            field=models.TextField(blank=True, default=''),
        ),
    ]
