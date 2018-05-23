from django.db import models
from django.utils.translation import ugettext_lazy as _

from jsonfield import JSONField

PUBLISH_STATUS_LIST = (
    (0, 'NOT AVAIL.'),
    (1, 'AVAILABLE')
)

### THESE ARE THE FIELDS THAT ARE IN EVERY MODEL
class PBSMMLightGlobalAbstract(models.Model):
    
    date_created = models.DateTimeField (
        _('Created On'),
        auto_now_add = True,
        help_text = "Not set by API",
    )
    
    object_id = models.UUIDField (
        _('Object ID'),
        unique = True,
        null = True, blank = True # does this work?
    )
    
    title = models.CharField (
        _('Title'),
        max_length = 200,
        null = True, blank = True
    )

    publish_status = models.PositiveIntegerField (
        _('Publish Status'),
        default = 0, null = False,
        choices = PUBLISH_STATUS_LIST
    )
    
    # Exists for all objects
    api_endpoint = models.URLField (
        _('API Endpoint'),
        null = True, blank = True,
        help_text = 'Endpoint to original record from the API'
    )
    #
    # This just makes the field clickable in the Admin (why cut and paste when you can click?)
    def link_to_api_record(self):
        return '<a href="%s" target="_new">%s</a>' % (self.api_endpoint, self.api_endpoint)
    link_to_api_record.allow_tags = True
    link_to_api_record.short_description = 'Link to API'
    
    def show_publish_status(self):
        if self.publish_status == 0:
            return "<span style=\"color:#f00;\">NO</span>"
        else:
            return "<span style=\"color:#0c0;\">Yes</span>"
    show_publish_status.allow_tags = True
    show_publish_status.short_description = 'Published?'
    
    class Meta:
        abstract = True
        
        
class PBSMMLightSlug(models.Model):
# These exist for all objects EXCEPT Season
    slug = models.SlugField (
        _('Slug'),
        unique = True,
        max_length = 200,
    )
    
    class Meta:
        abstract = True
        
class PBSMMLightSortableTitle(models.Model):
# Exists for all objects EXCEPT Collection - so we have to separate it 
# (I don't understand why the API just didn't create this across records...)    
    title_sortable = models.CharField (
        _('Sortable Title'),
        max_length = 200,
        null = True, blank = True
    )
    class Meta:
        abstract = True
        
class PBSMMLightIngest(models.Model):
    date_last_api_update = models.DateTimeField (
        _('Last API Retrieval'),
        help_text = "Not set by API",
        null = True
    )
    ingest_on_save = models.BooleanField (
        _('Ingest on Save'),
        default = False,
        help_text = 'If true, then will update values from the PBSMM API on save()'
    )
    last_api_status = models.PositiveIntegerField (
        _('Last API Status'),
        null = True, blank = True
    )
    
    json = JSONField (
        _('JSON'),
        null = True, blank = True
    )
    
    class Meta:
        abstract = True
        
    def last_api_status_color(self):
        template = '<b><span style="color:#%s;">%d</span></b>'
        if self.last_api_status:
            if self.last_api_status == 200:
                return template % ('0c0', self.last_api_status)
            else:
                return template % ('f00', self.last_api_status)
        return self.last_api_status
    last_api_status_color.allow_tags = True
    last_api_status_color.short_description = 'Status'
        

# This is the base class for EVERYTHING but Season abd Collection
class PBSMMLightObject(PBSMMLightGlobalAbstract, PBSMMLightSlug, PBSMMLightIngest, 
PBSMMLightSortableTitle):
    pass
    class Meta:
        abstract = True
        
# Collection has custom fields
class PBSMMLightCollectionObject(PBSMMLightGlobalAbstract, PBSMMLightIngest, PBSMMLightSlug):
    pass
    class Meta:
        abstract = True
        
# Season has custom fields
class PBSMMLightSeasonObject(PBSMMLightGlobalAbstract, PBSMMLightIngest, PBSMMLightSortableTitle):
    pass
    class Meta:
        abstract = True