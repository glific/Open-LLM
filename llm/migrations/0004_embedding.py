# Generated by Django 4.2.6 on 2023-10-17 05:42

from django.db import migrations, models
import django.db.models.deletion
import pgvector.django


class Migration(migrations.Migration):

    dependencies = [
        ('llm', '0003_pgvector'),
    ]

    operations = [
        migrations.CreateModel(
            name='Embedding',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False)),
                ('source_name', models.TextField()),
                ('original_text', models.TextField()),
                ('text_vectors', pgvector.django.VectorField(dimensions=1536, null=True)),
                ('organization', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='llm.organization')),
            ],
            options={
                'db_table': 'embedding',
            },
        ),
    ]