# Generated by Django 4.0.5 on 2022-06-16 19:53

from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("episode", "0004_auto_20190430_1949"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="pbsmmepisode",
            name="live_as_of",
        ),
        migrations.RemoveField(
            model_name="pbsmmepisode",
            name="publish_status",
        ),
    ]
