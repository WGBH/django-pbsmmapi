# Generated by Django 4.0.5 on 2022-06-22 18:39
import json

from django.db import migrations


def move_string_to_json(apps, schema_editor):
    PBSMMSpecialAsset = apps.get_model('special', 'PBSMMSpecialAsset')

    for asset in PBSMMSpecialAsset.objects.all():
        asset.images_json = json.loads(asset.images)
        asset.save()


def undo(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('special', '0008_pbsmmspecialasset_images_json'),
    ]

    operations = [
        migrations.RunPython(move_string_to_json, undo),
    ]
