# Generated by Django 4.2.6 on 2024-03-09 05:44

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('llm', '0010_organization_examples_text'),
    ]

    operations = [
        migrations.AddField(
            model_name='organization',
            name='openai_key',
            field=models.CharField(max_length=255, null=True, unique=True),
        ),
    ]
