# Generated by Django 4.2.6 on 2023-10-25 16:31

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('llm', '0006_rename_type_message_role'),
    ]

    operations = [
        migrations.AddField(
            model_name='message',
            name='evaluation_score',
            field=models.JSONField(null=True),
        ),
        migrations.AddField(
            model_name='organization',
            name='evaluator_prompt',
            field=models.TextField(null=True),
        ),
    ]