from rest_framework.views import APIView
from rest_framework.permissions import AllowAny
from areas.models import Area, GeoPoint
from rest_framework.response import Response


# noinspection PyMethodMayBeStatic,PyUnusedLocal
class Areas(APIView):
    permission_classes = (AllowAny,)
    http_method_names = ['get', 'post']

    def get(self, request, f=None):
        res = []
        for area in Area.objects.all():
            points = \
                [{'timestamp': p.timestamp, 'lon': p.lon, 'lat': p.lat} for p in GeoPoint.objects.filter(area=area)]
            res.append({'name': area.name, 'points': points})
        return Response(dict(response=res, return_code=12))

    def post(self, request, f=None):
        area_name = request.data.get("name", None)
        points = request.data.get("points", [])

        if not (area_name and points):
            return Response(dict(response=[], return_code=1))

        area = Area.objects.create(name=area_name)

        for o in points:
            GeoPoint.objects.create(area=area, timestamp=o['timestamp'], lon=o['lon'], lat=o['lat'])
            print(o['lat'], o['lon'])
        return Response(dict(response=[], return_code=0))
