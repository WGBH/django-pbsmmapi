# Generated by Django 4.0.7 on 2022-09-28 10:01

from django.db import (
    migrations,
    models,
)


class Migration(migrations.Migration):
    dependencies = [
        ("asset", "0004_alter_asset_date_last_api_update"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="asset",
            name="object_type",
        ),
        migrations.AddField(
            model_name="asset",
            name="asset_type",
            field=models.CharField(
                blank=True, max_length=40, null=True, verbose_name="Asset Type"
            ),
        ),
    ]
