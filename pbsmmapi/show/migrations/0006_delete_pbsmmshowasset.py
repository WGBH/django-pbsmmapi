# Generated by Django 4.0.6 on 2022-07-20 12:15

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('show', '0005_pbsmmshow_images_json_pbsmmshowasset_images_json_and_more'),
        ('asset', '0002_move_assets_data'),
    ]

    operations = [
        migrations.DeleteModel(
            name='PBSMMShowAsset',
        ),
    ]
