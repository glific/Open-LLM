# Generated by Django 4.2.6 on 2024-04-17 02:55

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('llm', '0013_knowledgecategory_file_embedding_file'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='file',
            name='type',
        ),
    ]
