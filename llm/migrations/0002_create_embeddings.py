# Generated by Django 4.2.4 on 2023-10-16 05:34

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('llm', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Embeddings',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False)),
                ('raw_text', models.TextField()),
                ('text_source', models.TextField()),
                ('doc_vectors', models.BinaryField(max_length=1536)),
            ],
            options={
                'db_table': 'embeddings',
            },
        ),
    ]
