# Generated by Django 4.0.6 on 2022-07-21 07:54

from django.db import migrations

old_asset_tables = (
    'pbsmm_episode_asset',
    'pbsmm_season_asset',
    'pbsmm_show_asset',
    'pbsmm_special_asset',
)


def forwards(apps, schema):
    Asset = apps.get_model('asset', 'Asset')

    def make_assets(table_name):
        fields = Asset._meta.get_fields()
        fields = ', '.join(f.name for f in fields if f.name != 'id')
        query = f'SELECT {fields} FROM {table_name}'
        for a in Asset.objects.raw(query).values():
            yield Asset(**a)

    for table in old_asset_tables:
        Asset.objects.bulk_create(make_assets(table))


def backwards(apps, schema):
    Asset = apps.get_model('asset', 'Asset')

    for a in Asset.objects.values().iterator():
        pass


class Migration(migrations.Migration):

    dependencies = [
        ('asset', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(forwards, backwards)
    ]
