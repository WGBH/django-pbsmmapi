from django.db import models
from django.utils.translation import ugettext_lazy as _

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
    link_to_api_record = models.URLField (
        _('Link to API Record'),
        null = True, blank = True,
        help_text = 'Endpoint to original record from the API'
    )
    #
    # This just makes the field clickable in the Admin (why cut and paste when you can click?)
    def link_to_api_record_link(self):
        return '<a href="%s" target="_new">%s</a>' % (self.link_to_api_record, self.link_to_api_record)
    link_to_api_record_link.allow_tags = True
    link_to_api_record_link.short_description = 'Link to API'
    
    class Meta:
        abstract = True
        
        
class PBSMMLightGenerallyAbstract(models.Model):
    
# These exist for all objects EXCEPT Season
    slug = models.SlugField (
        _('Slug'),
        unique = True,
        max_length = 200,
    )
    
    class Meta:
        abstract = True
        

# This is the base class for EVERYTHING but Season
class PBSMMLightObject(PBSMMLightGlobalAbstract, PBSMMLightGenerallyAbstract):
    pass
    
    class Meta:
        abstract = True
        
