from rest_framework.views import APIView
from rest_framework.permissions import AllowAny
from areas.models import Area, GeoPoint
from rest_framework.response import Response


class Areas(APIView):
    permission_classes = (AllowAny,)
    http_method_names = ['get', 'post']

    def get(self, request, format=None):
        res = []
        for area in Area.objects.all():
            res.append({'name': area.name, 'points':
                ([{'timestamp': p.timestamp, 'lon': p.lon, 'lat': p.lat} for p in GeoPoint.objects.filter(area=area)])})
        return Response(dict(response=res))
