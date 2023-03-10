# Generated by Django 3.2.18 on 2023-03-02 00:30

from django.db import migrations, models
import django.db.models.deletion
import uuid


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('customers', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='BankAccount',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_date', models.DateTimeField(auto_now_add=True)),
                ('modified_date', models.DateTimeField(auto_now=True)),
                ('deleted_date', models.DateTimeField(blank=True, null=True)),
                ('is_deleted', models.BooleanField(default=False)),
                ('guid', models.UUIDField(default=uuid.uuid4, editable=False, unique=True)),
                ('account_number', models.CharField(max_length=15, unique=True)),
                ('is_active', models.BooleanField(default=False)),
                ('owner', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, to='customers.customer')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='BankTransaction',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_date', models.DateTimeField(auto_now_add=True)),
                ('modified_date', models.DateTimeField(auto_now=True)),
                ('deleted_date', models.DateTimeField(blank=True, null=True)),
                ('is_deleted', models.BooleanField(default=False)),
                ('amount', models.DecimalField(decimal_places=2, max_digits=12)),
                ('is_debit', models.BooleanField(default=False)),
                ('description', models.TextField()),
                ('bank_account', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='mutations', to='management.bankaccount')),
                ('receiver', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='receiver', to='customers.customer')),
                ('sender', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='sender', to='customers.customer')),
            ],
            options={
                'abstract': False,
            },
        ),
    ]
