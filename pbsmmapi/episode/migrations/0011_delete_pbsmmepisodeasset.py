# Generated by Django 4.0.6 on 2022-07-20 12:15

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('episode', '0010_pbsmmepisodeasset_images_json'),
        ('asset', '0002_move_assets_data'),
    ]

    operations = [
        migrations.DeleteModel(
            name='PBSMMEpisodeAsset',
        ),
    ]
