# Generated by Django 4.0.6 on 2022-07-18 10:42

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('season', '0010_pbsmmseason_images_json_pbsmmseasonasset_images_json'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='pbsmmseasonasset',
            name='chapters',
        ),
        migrations.RemoveField(
            model_name='pbsmmseasonasset',
            name='content_rating',
        ),
        migrations.RemoveField(
            model_name='pbsmmseasonasset',
            name='content_rating_description',
        ),
        migrations.RemoveField(
            model_name='pbsmmseasonasset',
            name='topics',
        ),
    ]
