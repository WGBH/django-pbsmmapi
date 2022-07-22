# Generated by Django 4.0.6 on 2022-07-21 07:54
from functools import lru_cache
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


def get_type(asset: dict, apps):
    '''
    returns PBSMMAsset type based on Asset foreignkey
    >>> get_type(asset, apps)
    PBSMMEpisodeAsset
    '''
    @lru_cache(maxsize=1)
    def asset_type():
        # this will execute only once no matter of how many times is called
        return dict(
            episode_id=apps.get_model('episode', 'PBSMMEpisodeAsset'),
            season_id=apps.get_model('season', 'PBSMMSeasonAsset'),
            show_id=apps.get_model('show', 'PBSMMShowAsset'),
            special_id=apps.get_model('special', 'PBSMMSpecialAsset'),
        )
    _type = asset_type()
    return next(_type[t] for t in _type.keys() if asset.get(t))


@lru_cache(maxsize=4)
def get_common_fields(asset_model, pbsmm_model):
    '''
    maxsize is set to 4 because there are only 4 types of old assets
    this return only common fields of new and old asset
    '''
    return ({f.name for f in pbsmm_model._meta.get_fields()}
            .intersection(
            {f.name for f in asset_model._meta.get_fields()}))


def backwards(apps, schema):
    Asset = apps.get_model('asset', 'Asset')

    for a in Asset.objects.values().iterator():
        AssetType = get_type(a, apps)
        fields = get_common_fields(Asset, AssetType)
        entity = dict(k=v for k, v in a.items() if k in fields)
        del entity['id']
        AssetType.objects.create(**entity)


class Migration(migrations.Migration):
    dependencies = [
        ('asset', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(forwards, backwards)
    ]
