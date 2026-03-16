import subprocess
import os

from rest_framework.views import APIView
from areas.models import Area, GeoPoint, MyUser, Kataster
from rest_framework.response import Response
from rest_framework.authentication import TokenAuthentication
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from pathlib import Path

from geoplazma_server.ntrip_client import start_ntrip_client, stop_ntrip_client, write_rtcm_data

logfile = "logfile.txt"
posfile = "rover.pos"


def store_raw_gnss_data(res):
    if Path(logfile).exists():
        Path(logfile).unlink()
    with open(logfile, "a") as f:
        f.write(res)


def post_process(res):
    # 1. raw GNSS data from rower and convert it to RINEX .obs file
    path = "/home/vajnar/Projects/android_rinex"
    os.environ["PYTHONPATH"] = path
    subprocess.run([f"{path}/bin/gnsslogger_to_rnx", "--output", "rover.obs", logfile])
    # 2. NTRIP caster Base Station data; .nav and .obs files
    stop_ntrip_client()
    # 3. Execute RTKLIB post processing
    subprocess.run(["/home/vajnar/Projects/RTKLIB/bin/rtkpost_qt"])
    # 4. Write result to file
    path = "/home/vajnar/Projects/pos_parser"
    os.environ["PYTHONPATH"] = path
    subprocess.run([f"{path}/bin/pos-parser", posfile])


def is_user_valid(request, login=False):
    my_user = request.data.get("user", "")
    try:
        my_user = MyUser.objects.get(email=my_user)
    except MyUser.DoesNotExist:
        return None

    if login and my_user and not my_user.logged_in:
        my_user.logged_in = True
        my_user.save()
        return my_user
    elif not login and my_user and my_user.logged_in:
        return my_user

    return None


class Login(APIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request, f=None):
        res = dict(user=request.data.get("user", ""))

        if is_user_valid(request, True):
            return Response(res, status=status.HTTP_200_OK)

        return Response(res, status=status.HTTP_400_BAD_REQUEST)


class LogFile(APIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request, f=None):
        res = request.data.get("data", "")
        store_raw_gnss_data(res)

        return Response({"result": "OK"}, status=status.HTTP_200_OK)


class PrecisePosition(APIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request, f=None):
        res = request.data.get("position", "")
        print(request.data.get("action", ""))
        print(res)
        if request.data.get("action", "") == "START":
            start_ntrip_client()
            return Response(dict(lon=0.0, lat=0.0, h=0.0), status.HTTP_200_OK)
        else:
            post_process(res)
            filename = "/home/vajnar/Projects/geoplazma_server/gnss_result"
            f = open(filename, "r")
            # TODO naj bodo serialize podatki kot v datoteki, da se samo pos poslje
            pos = f.readline().split(' ')
            if pos and pos[0] != "Empty":
                return Response(dict(lon=float(pos[1]), lat=float(pos[0]), h=float(pos[2])), status.HTTP_200_OK)
            else:
                return Response(dict(lon=0.0, lat=0.0, h=0.0), status.HTTP_500_INTERNAL_SERVER_ERROR)

        # tle se nauc cellery uporabljat
        return Response(dict(lon=0.0, lat=0.0, h=0.0), status.HTTP_200_OK)


class BinaryData(APIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request, f=None):
        res = request.data.get("data", "")
        bData = bytes(res, "utf-8")
        write_rtcm_data(bData)

        return Response({"result": "OK"}, status=status.HTTP_200_OK)


class StartNTRIP(APIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request, f=None):
        params = request.data.get("params", "")

        if params == "START":
            start_ntrip_client()
        else:
            stop_ntrip_client()

        return Response({"result": "OK"}, status=status.HTTP_200_OK)


class Areas(APIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def delete(self, request):
        my_user = is_user_valid(request)
        if not my_user:
            return Response(dict(response=[]), status=status.HTTP_400_BAD_REQUEST)

        area = Area.objects.get(name=request.data['name'])
        my_user.area.remove(area)
        GeoPoint.objects.filter(area=area).delete()
        area.delete()
        return Response(dict(response=[]), status=status.HTTP_200_OK)

    def get(self, request, f=None):
        my_user = is_user_valid(request)
        if not my_user:
            return Response(dict(response=[]), status=status.HTTP_400_BAD_REQUEST)
        
        res = []
        for area in my_user.area.all():
            points = \
                [{'timestamp': p.timestamp, 'lon': p.lon, 'lat': p.lat} for p in GeoPoint.objects.filter(area=area)]
            res.append({'name': area.name, 'points': points})
        return Response(dict(response=res))

    def post(self, request, f=None):
        area_name = request.data.get("name", None)
        points = request.data.get("points", [])

        # get
        if not area_name:
            return self.get(request, f)

        my_user = is_user_valid(request)
        if not my_user:
            return Response(dict(response=[]), status=status.HTTP_400_BAD_REQUEST)

        area = Area.objects.create(name=area_name, kataster=Kataster.objects.get(name=my_user.email))
        my_user.area.add(area)
        for o in points:
            GeoPoint.objects.create(area=area, timestamp=o['timestamp'], lon=o['lon'], lat=o['lat'])
            print(o['lat'], o['lon'])
        return Response(dict(response=[]), status=status.HTTP_200_OK)
