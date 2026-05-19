import datetime
import os

from django.core.management import BaseCommand
from pykml import parser
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
        email = options['user']
        directory = options['dir']
        if MyUser.objects.filter(email=email).exists():
            user = MyUser.objects.get(email=email)
        else:
            user = MyUser.objects.create(email=email)

        for file in os.listdir(directory):
            area_name = file.split('_')
            area_name = area_name[0] + '/' + area_name[1]
            file = os.path.join(directory, file)
            with open(file, 'r', encoding="utf-8") as f:
                root = parser.parse(f).getroot()
            # define kataster object
            if Kataster.objects.filter(name=kataster).exists():
                k = Kataster.objects.get(name=kataster)
            else:
                k = Kataster.objects.create(name=kataster)
            # define area object
            if Area.objects.filter(name=area_name, kataster=k).exists():
                a = Area.objects.get(name=area_name, kataster=k)
            else:
                a = Area.objects.create(name=area_name, kataster=k)

            user.area.add(a)
            res = root.Document.Placemark.Polygon.outerBoundaryIs.LinearRing.coordinates.text.strip().split(' ')
            stamp = 0
            for p in res:
                c = p.split(',')
                lon, lat = float(c[0]), float(c[1])
                GeoPoint.objects.create(area=a, lat=lat, lon=lon, timestamp=stamp)
                stamp += 1
