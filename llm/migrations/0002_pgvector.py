# Generated by Django 4.2.6 on 2023-10-17 05:06

from django.db import migrations
import pgvector.django


class Migration(migrations.Migration):
    dependencies = [
        ("llm", "0001_initial"),
    ]

    operations = [pgvector.django.VectorExtension()]
