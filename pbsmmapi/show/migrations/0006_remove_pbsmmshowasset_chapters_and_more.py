# Generated by Django 4.0.6 on 2022-07-18 10:42

from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("show", "0005_pbsmmshow_images_json_pbsmmshowasset_images_json_and_more"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="pbsmmshowasset",
            name="chapters",
        ),
        migrations.RemoveField(
            model_name="pbsmmshowasset",
            name="content_rating",
        ),
        migrations.RemoveField(
            model_name="pbsmmshowasset",
            name="content_rating_description",
        ),
        migrations.RemoveField(
            model_name="pbsmmshowasset",
            name="topics",
        ),
    ]
