from django.db import models
from django.utils.translation import gettext_lazy as _
from django.conf import settings

class Kataster(models.Model):
    name = models.CharField(max_length=32, verbose_name=_('Kataster'), db_index=True)
    country = models.CharField(verbose_name=_('Country'), max_length=32)
    custom = models.BooleanField(verbose_name=_('Custom'), default=False)

class Area(models.Model):
    name = models.CharField(max_length=32, verbose_name=_('Ime'), db_index=True)
    kataster = models.ForeignKey(Kataster, verbose_name=_('Kataster'), on_delete=models.CASCADE)

    def __str__(self):
        return "Area: %s" % self.name

class MyUser(models.Model):
    email = models.EmailField(verbose_name=_('E-mail'), unique=True)
    logged_in = models.BooleanField(default=False)
    area = models.ManyToManyField(Area)

class GeoPoint(models.Model):
    area = models.ForeignKey(Area, verbose_name=_('Območje'), on_delete=models.CASCADE)
    timestamp = models.BigIntegerField(verbose_name=_('Timestamp'), default=0)
    lon = models.FloatField(verbose_name=_('GEO dolžina'), default=0.0)
    lat = models.FloatField(verbose_name=_('GEO širina'), default=0.0)

    def __str__(self):
        return "GeoPoint:(%s, %s)" % (self.lon, self.lat)
