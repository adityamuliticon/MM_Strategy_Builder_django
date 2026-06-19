from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('chat_logs', '0004_chatlog_runware_task_id'),
        ('users', '0001_initial'),
    ]

    operations = [
        # Add user FK to ChatLog
        migrations.AddField(
            model_name='chatlog',
            name='user',
            field=models.ForeignKey(
                blank=True, null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='chat_logs',
                to='users.appuser',
            ),
        ),
        # Add user FK to APICallLog
        migrations.AddField(
            model_name='apicalllog',
            name='user',
            field=models.ForeignKey(
                blank=True, null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='api_call_logs',
                to='users.appuser',
            ),
        ),
        # Create ChatMessage table
        migrations.CreateModel(
            name='ChatMessage',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('module', models.CharField(
                    choices=[
                        ('USB', 'Unified Strategy Builder'),
                        ('ISE', 'Indicator Signal Engine'),
                        ('ISB', 'Inbound Signal Bridge'),
                        ('RES', 'Rapid Execution Scalper'),
                        ('MLH', 'Multi-Leg Hedger'),
                    ],
                    db_index=True, max_length=10,
                )),
                ('role', models.CharField(
                    choices=[('user', 'User'), ('assistant', 'Assistant')],
                    max_length=20,
                )),
                ('content', models.TextField()),
                ('timestamp', models.DateTimeField(auto_now_add=True)),
                ('user', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='messages',
                    to='users.appuser',
                )),
            ],
            options={
                'ordering': ['timestamp'],
            },
        ),
        migrations.AddIndex(
            model_name='chatmessage',
            index=models.Index(fields=['user', 'module', 'timestamp'], name='chatmsg_user_module_ts_idx'),
        ),
    ]
