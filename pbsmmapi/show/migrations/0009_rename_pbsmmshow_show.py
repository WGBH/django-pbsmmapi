# Generated by Django 4.0.7 on 2022-08-29 12:37

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('season', '0014_rename_pbsmmseason_season'),
        ('asset', '0004_alter_asset_date_last_api_update'),
        ('special', '0010_alter_pbsmmspecial_date_last_api_update'),
        ('show', '0008_alter_pbsmmshow_date_last_api_update'),
    ]

    operations = [
        migrations.RenameModel(
            old_name='PBSMMShow',
            new_name='Show',
        ),
    ]
