# this is just a clipboard until I figure out where this code should go

#### RELATIONSHIPS
    relationships = {}
    new_related_assets = []
    if instance.pk: 
        if instance.ingest_related_assets:
            related_assets_endpoint = links.get('assets', None)

            (status, json) = get_PBSMM_record(related_assets_endpoint)
            if status == 200:
                asset_list = json['data']

                for asset in asset_list:
                    asset_id = asset.get('id', None)
                    (op, asset_pk) = ingest_related_asset(asset_id)                    
                    if op == 'new' and asset_pk:
                        new_related_assets.append(asset_pk)
            if len(new_related_assets) > 0:
                relationships['new_assets'] = new_related_assets