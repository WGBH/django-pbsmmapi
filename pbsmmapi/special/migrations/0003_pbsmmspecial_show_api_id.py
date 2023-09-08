# Generated by Django 2.2 on 2019-04-30 19:26

from django.db import (
    migrations,
    models,
)


class Migration(migrations.Migration):
    dependencies = [
        ("special", "0002_auto_20190430_1853"),
    ]

    operations = [
        migrations.AddField(
            model_name="pbsmmspecial",
            name="show_api_id",
            field=models.UUIDField(
                blank=True, null=True, unique=True, verbose_name="Show Object ID"
            ),
        ),
    ]
