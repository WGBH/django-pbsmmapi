# Generated by Django 4.0.7 on 2022-08-11 19:29

from django.db import (
    migrations,
    models,
)


class Migration(migrations.Migration):
    dependencies = [
        ("season", "0012_remove_pbsmmseason_images_json"),
    ]

    operations = [
        migrations.AlterField(
            model_name="pbsmmseason",
            name="date_last_api_update",
            field=models.DateTimeField(
                auto_now=True,
                help_text="Not set by API",
                null=True,
                verbose_name="Last API Retrieval",
            ),
        ),
    ]
