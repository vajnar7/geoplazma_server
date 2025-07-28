import datetime
import os

from django.core.management import BaseCommand
from pykml import parser
import pandas as pd
from areas.models import Area, Kataster, GeoPoint, MyUser


class Command(BaseCommand):
    help = "Build a database of areas from KML files"

    def add_arguments(self, parser):
        # parser.add_argument('kml_file', nargs=1)
        parser.add_argument('-kataster', dest='kataster', type=str, help='set kataster name e.g. GOZD (2170)')
        parser.add_argument('-user', dest='user', type=str, help='set user name e.g. vajnar7@gmail.net')
        parser.add_argument('-dir', dest='dir', type=str, help='directory containing kml files for specific kataster and user')

    def handle(self, *args, **options):
        kataster = options['kataster']
        user = options['user']
        directory = options['dir']
        user = MyUser.objects.get(email=user)
        for file in os.listdir(directory):
            area_name = file.split('_')
            area_name = area_name[0] + '/' + area_name[1]
            file = os.path.join(directory, file)
            with open(file, 'r', encoding="utf-8") as f:
                root = parser.parse(f).getroot()

            k = Kataster.objects.get(name=kataster)
            a = Area.objects.create(name=area_name, kataster=k)
            user.area.add(a)
            res = root.Document.Placemark.Polygon.outerBoundaryIs.LinearRing.coordinates.text.strip().split(' ')
            stamp = 0
            for p in res:
                c = p.split(',')
                lon, lat = float(c[0]), float(c[1])
                GeoPoint.objects.create(area=a, lat=lat, lon=lon, timestamp=stamp)
                stamp += 1
