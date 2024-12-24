from django.db import models

class Announcement(models.Model):
    announcementid = models.AutoField(primary_key=True)
    offer_type = models.IntegerField()
    timestamp = models.DateTimeField()
    update_date = models.DateTimeField()
    construction_date = models.DateTimeField()
    title = models.CharField(max_length=255)
    description = models.CharField(max_length=255)
    location = models.CharField(max_length=255)
    owner = models.CharField(max_length=255)
    price = models.FloatField()
    rooms = models.IntegerField()
    constructed_m2 = models.FloatField()
    url = models.CharField(max_length=255)
    image_urls = models.CharField(max_length=999)
    ref = models.CharField(max_length=255)

    class Meta:
        db_table = 'announcement'
