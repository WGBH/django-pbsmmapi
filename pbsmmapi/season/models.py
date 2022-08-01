# -*- coding: utf-8 -*-
from http import HTTPStatus
from uuid import UUID

from django.db import models
from django.dispatch import receiver
from django.utils.safestring import mark_safe
from django.utils.translation import gettext_lazy as _
from pbsmmapi.abstract.helpers import time_zone_aware_now
from pbsmmapi.abstract.models import PBSMMGenericSeason
from pbsmmapi.api.api import get_PBSMM_record, PBSMM_SEASON_ENDPOINT
from pbsmmapi.api.helpers import check_pagination
from pbsmmapi.asset.ingest_asset import process_asset_record
from pbsmmapi.asset.models import Asset
from pbsmmapi.season.ingest_children import process_episodes


class PBSMMSeason(PBSMMGenericSeason):
    '''
    These are the fields that are unique to PBSMMSeason
    '''
    ordinal = models.PositiveIntegerField(_('Ordinal'), null=True, blank=True)

    # This is the parental Show
    show_api_id = models.UUIDField(
        _('Show Object ID'),
        null=True,
        blank=True  # does this work?
    )
    show = models.ForeignKey(
        'show.PBSMMShow',
        related_name='seasons',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
    )

    # This triggers cascading ingestion of child Episodes - set from the admin
    # before a save()
    ingest_episodes = models.BooleanField(
        _('Ingest Episodes'),
        default=False,
        help_text='Also ingest all Episodes (for each Season)'
    )

    def create_table_line(self):
        this_title = "Season %d: %s" % (self.ordinal, self.title)
        out = "<tr style=\"background-color: #ddd;\">"
        out += "<td colspan=\"3\"><a href=\"/admin/season/pbsmmseason/%d/change/\"><b>%s</b></a></td>" % (
            self.id, this_title
        )
        out += "<td><a href=\"%s\" target=\"_new\">API</a></td>" % self.api_endpoint
        out += "\n\t<td>%d</td>" % self.assets.count()
        out += "\n\t<td>%s</td>" % self.date_last_api_update.strftime("%x %X")
        out += "\n\t<td>%s</td>" % self.last_api_status_color()
        return mark_safe(out)

    @property
    def object_model_type(self):
        '''
        This return the object type.
        '''
        # This handles the correspondence to the "type" field in the PBSMM JSON
        # object
        return 'season'

    @property
    def printable_title(self):
        '''
        This creates a human friendly title out of the Season metadata
        if an explicit title is not set from the Show title and Episode ordinal.
        '''
        if self.show:
            return f'{self.show.title} Season {self.ordinal}'
        return 'Season {self.ordinal}'

    def __str__(self):
        return f'{self.object_id} | {self.ordinal} | {self.title}'

    class Meta:
        verbose_name = 'PBS MM Season'
        verbose_name_plural = 'PBS MM Seasons'
        db_table = 'pbsmm_season'
        ordering = ['-ordinal']

    def save(self, *args, **kwargs):
        self.pre_save()
        super().save(args, kwargs)
        self.post_save()

    def pre_save(self):
        self.self_process(PBSMM_SEASON_ENDPOINT)
        object_id = str(self.object_id or "").strip()
        if not self.ingest_on_save or self.pk or not object_id:
            return  # we need processing only for new objects
        status, json = get_PBSMM_record(f"{PBSMM_SEASON_ENDPOINT}{object_id}/")
        self.last_api_status = status
        self.date_last_api_update = time_zone_aware_now()
        if status != HTTPStatus.OK:
            return
        attrs = json.get('attributes', json['data'].get('attributes'))
        fields = (f.name for f in PBSMMSeason._meta.get_fields())
        for field in (f for f in fields if f != 'id'):
            setattr(self, field, attrs.get(field))
        self.ingest_on_save = False

    def post_save(self):
        pass


def process_season_assets(endpoint, this_season):
    '''
    For each Asset associated with this Season, ingest them page by page.
    '''
    keep_going = True
    scraped_object_ids = []
    while keep_going:
        (status, json) = get_PBSMM_record(endpoint)
        asset_list = json['data']

        for item in asset_list:
            object_id = item.get('id')
            scraped_object_ids.append(UUID(object_id))

            try:
                instance = Asset.objects.get(object_id=object_id)
            except Asset.DoesNotExist:
                instance = Asset()

            instance = process_asset_record(item, instance, origin='special')
            instance.season = this_season

            # For now - borrow from the parent object
            instance.last_api_status = status
            instance.date_last_api_update = time_zone_aware_now()

            instance.ingest_on_save = True

            # This needs to be here because otherwise it never updates...
            instance.save()

        (keep_going, endpoint) = check_pagination(json)

    for asset in Asset.objects.filter(season=this_season):
        if asset.object_id not in scraped_object_ids:
            asset.delete()


# @receiver(models.signals.pre_save, sender=PBSMMSeason)
# def scrape_PBSMMAPI(sender, instance, **kwargs):
#     '''
#     Get a Season's data from the PBS MM API.   Either update or create a
#     PBSMMSeason record.
#
#     The interface/access is done with a 'pre_save' receiver based on the value of
#     'ingest_on_save'
#
#     That way, one can force a reingestion from the Admin OR one can do it from a
#     management script by simply getting the record, setting ingest_on_save on the
#     record, and calling save().
#     '''
#     if instance.__class__ is not PBSMMSeason:
#         return
#
#     # If this is a new record, then someone has started it in the Admin using
#     # EITHER a legacy COVE ID OR a PBSMM UUID.   Depending on which, the
#     # retrieval endpoint is slightly different, so this sets the appropriate
#     # URL to access.
#     if instance.pk and instance.object_id and str(instance.object_id).strip():
#         # Object is being edited
#         if not instance.ingest_on_save:
#             return  # do nothing - can't get an ID to look up!
#
#     else:  # object is being added
#         if not instance.object_id:
#             return  # do nothing - can't get an ID to look up!
#
#     url = f'{PBSMM_SEASON_ENDPOINT}{instance.object_id}/'
#
#     # OK - get the record from the API
#     (status, json) = get_PBSMM_record(url)
#
#     instance.last_api_status = status
#     # Update this record's time stamp (the API has its own)
#     instance.date_last_api_update = time_zone_aware_now()
#
#     # If we didn't get a record, abort (there's no sense crying over spilled
#     # bits)
#     if status != 200:
#         return
#
#     # Process the record (code is in ingest.py)
#     instance = process_season_record(json, instance)
#
#     # continue saving, but turn off the ingest_on_save flag
#     instance.ingest_on_save = False  # otherwise we could end up in an infinite loop!
#
#     # We're done here - continue with the save() operation
#     return


@receiver(models.signals.post_save, sender=PBSMMSeason)
def handle_children(sender, instance, *args, **kwargs):
    '''
    If the ingest_episodes flag is set, then also ingest every episode for this Season.

    Also, always ingest the Assets associated with this Season.

    '''
    if instance.ingest_episodes:
        # This is the FIRST endpoint - there might be more, depending on
        # pagination!
        episodes_endpoint = instance.json['links'].get('episodes')

        if episodes_endpoint:
            process_episodes(episodes_endpoint, instance)

    # ALWAYS GET CHILD ASSETS
    assets_endpoint = instance.json['links'].get('assets')
    if assets_endpoint:
        process_season_assets(assets_endpoint, instance)

    # This is a tricky way to unset ingest_seasons without calling save()
    rec = PBSMMSeason.objects.filter(pk=instance.id)
    rec.update(ingest_episodes=False)
