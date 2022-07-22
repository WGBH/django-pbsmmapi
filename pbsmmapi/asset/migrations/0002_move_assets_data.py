# Generated by Django 4.0.6 on 2022-07-21 07:54
from functools import lru_cache
from django.db import migrations, connections
from django.db.models import Manager

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
        fields = {f.column for f in fields if f.name != 'id'}

        for a in Asset.objects.raw(f'SELECT * FROM {table_name}'):
            yield Asset(**{f: a.__dict__.get(f) for f in fields})

    for table in old_asset_tables:
        Asset.objects.bulk_create(make_assets(table))


def get_type(asset: dict, apps):
    '''
    returns PBSMMAsset type based on Asset foreignkey
    >>> get_type(asset, apps)
    PBSMMEpisodeAsset
    '''
    @lru_cache(maxsize=1)
    def asset_type():
        # this will execute only once no matter of how many times is called
        return dict(zip(('episode_id', 'season_id', 'show_id', 'special_id',),
                        old_asset_tables))
    _type = asset_type()
    return next(_type[t] for t in _type.keys() if asset.get(t))


def backwards(apps, schema):
    Asset = apps.get_model('asset', 'Asset')

    for asset in Asset.objects.values().iterator():
        table = get_type(asset, apps)
        del asset['id']
        with connections['write'].cursor() as c:
            c.execute(f"INSERT INTO {table} {', '.join(asset.keys())}"
                      f"VALUES {', '.join(asset.values())}")


class Migration(migrations.Migration):
    dependencies = [
        ('asset', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(forwards, backwards)
    ]
