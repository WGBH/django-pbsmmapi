# Generated by Django 4.0.5 on 2022-06-17 12:38

from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("special", "0005_remove_pbsmmspecial_live_as_of_and_more"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="pbsmmspecialasset",
            name="override_default_asset",
        ),
    ]
