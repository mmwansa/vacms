from django.db import migrations, models
import uuid
import simple_history.models


class Migration(migrations.Migration):

    dependencies = [
        ('va_data_management', '0028_auto_20250708_0000'),
    ]

    operations = [
        migrations.CreateModel(
            name='PregnancyFieldReference',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False)),
                ('uuid', models.UUIDField(default=uuid.uuid4, editable=False, unique=True)),
                ('name', models.CharField(max_length=255, unique=True)),
                ('list_name', models.CharField(max_length=255)),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('updated', models.DateTimeField(auto_now=True)),
                ('history', simple_history.models.HistoricalRecords()),
            ],
        ),
        migrations.CreateModel(
            name='PregnancyChoiceReference',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False)),
                ('uuid', models.UUIDField(default=uuid.uuid4, editable=False, unique=True)),
                ('list_name', models.CharField(max_length=255)),
                ('name', models.CharField(max_length=255)),
                ('label', models.TextField(blank=True)),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('updated', models.DateTimeField(auto_now=True)),
                ('history', simple_history.models.HistoricalRecords()),
            ],
            options={
                'unique_together': {('list_name', 'name')},
            },
        ),
    ]
