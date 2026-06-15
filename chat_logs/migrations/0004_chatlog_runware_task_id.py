from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('chat_logs', '0003_apicalllog'),
    ]

    operations = [
        migrations.AddField(
            model_name='chatlog',
            name='runware_task_id',
            field=models.CharField(blank=True, default='', max_length=100),
        ),
    ]
