from django.db import models
from django.utils.translation import gettext_lazy as _


class Area(models.Model):
    name = models.CharField(max_length=32, verbose_name=_('Ime'), db_index=True)

    def __str__(self):
        return "Area: %s" % self.name


class GeoPoint(models.Model):
    area = models.ForeignKey(Area, verbose_name=_('Območje'), on_delete=models.CASCADE)
    timestamp = models.BigIntegerField(verbose_name=_('Timestamp'), default=0, unique=True)
    lon = models.FloatField(verbose_name=_('GEO dolžina'), default=0.0)
    lat = models.FloatField(verbose_name=_('GEO širina'), default=0.0)

    def __str__(self):
        return "GeoPoint:(%s, %s)" % (self.lon, self.lat)
