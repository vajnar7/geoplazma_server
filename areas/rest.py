import subprocess
import os
from functools import wraps

from rest_framework.views import APIView
from areas.models import Area, GeoPoint, MyUser, Kataster
from rest_framework.response import Response
from rest_framework.authentication import TokenAuthentication
from rest_framework.permissions import IsAuthenticated
from rest_framework import status, serializers
from pathlib import Path
from django.core.cache import cache
from django.views.decorators.cache import cache_page
from django.utils.decorators import method_decorator

from geoplazma_server.ntrip_client import start_ntrip_client, stop_ntrip_client

logfile = "logfile.txt"
CACHE_TIMEOUT = 300  # 5 minutes


class GeoPointSerializer(serializers.ModelSerializer):
    class Meta:
        model = GeoPoint
        fields = ['timestamp', 'lon', 'lat']


class AreaSerializer(serializers.ModelSerializer):
    points = serializers.SerializerMethodField()

    class Meta:
        model = Area
        fields = ['id', 'name', 'points']

    def get_points(self, obj):
        points = obj.geopoint_set.all().values('timestamp', 'lon', 'lat')
        return list(points)


def get_user_from_request(request, login=False):
    """Optimized user validation with better error handling."""
    user_email = request.data.get("user", "").strip()
    
    if not user_email:
        return None
    
    try:
        my_user = MyUser.objects.get(email=user_email)
        
        if login and not my_user.logged_in:
            my_user.logged_in = True
            my_user.save()
            # Clear user cache on login
            cache.delete(f"user_{my_user.id}")
            return my_user
        elif not login and my_user.logged_in:
            return my_user
            
    except MyUser.DoesNotExist:
        pass
    
    return None


class Login(APIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request):
        user_email = request.data.get("user", "").strip()
        
        if not user_email:
            return Response(
                {"user": user_email, "error": "User email required"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        my_user = get_user_from_request(request, login=True)
        
        if my_user:
            return Response(
                {"user": user_email, "status": "logged_in"},
                status=status.HTTP_200_OK
            )
        
        return Response(
            {"user": user_email, "error": "Invalid user or already logged in"},
            status=status.HTTP_400_BAD_REQUEST
        )


class Logout(APIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request):
        user_email = request.data.get("user", "").strip()
        
        try:
            my_user = MyUser.objects.get(email=user_email)
            my_user.logged_in = False
            my_user.save()
            cache.delete(f"user_{my_user.id}")
            
            return Response(
                {"status": "logged_out"},
                status=status.HTTP_200_OK
            )
        except MyUser.DoesNotExist:
            return Response(
                {"error": "User not found"},
                status=status.HTTP_404_NOT_FOUND
            )


class LogFile(APIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request):
        my_user = get_user_from_request(request)
        if not my_user:
            return Response(
                {"error": "Unauthorized"},
                status=status.HTTP_401_UNAUTHORIZED
            )
        
        data = request.data.get("data", "").strip()
        
        if not data:
            return Response(
                {"error": "No data provided"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            # Clean up old logfile
            if Path(logfile).exists():
                Path(logfile).unlink()
            
            # Write new data
            with open(logfile, "a") as f:
                f.write(data)
            
            # Process with external tool
            os.environ["PYTHONPATH"] = "/home/vajnar/Projects/android_rinex"
            result = subprocess.run(
                ["/home/vajnar/Projects/android_rinex/bin/gnsslogger_to_rnx",
                 "--output", "rover.obs", logfile],
                capture_output=True,
                timeout=30
            )
            
            if result.returncode != 0:
                return Response(
                    {"error": "Processing failed"},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            return Response({"result": "OK"}, status=status.HTTP_200_OK)
            
        except subprocess.TimeoutExpired:
            return Response(
                {"error": "Processing timeout"},
                status=status.HTTP_504_GATEWAY_TIMEOUT
            )
        except Exception as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class StartNTRIP(APIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request):
        my_user = get_user_from_request(request)
        if not my_user:
            return Response(
                {"error": "Unauthorized"},
                status=status.HTTP_401_UNAUTHORIZED
            )
        
        params = request.data.get("params", "").strip().upper()
        
        try:
            if params == "START":
                start_ntrip_client()
                action = "started"
            elif params == "STOP":
                stop_ntrip_client()
                action = "stopped"
            else:
                return Response(
                    {"error": "Invalid parameter. Use START or STOP"},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            return Response(
                {"result": "OK", "action": action},
                status=status.HTTP_200_OK
            )
        except Exception as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class Areas(APIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """Get all areas for authenticated user with optimized queries."""
        my_user = get_user_from_request(request)
        if not my_user:
            return Response(
                {"error": "Unauthorized"},
                status=status.HTTP_401_UNAUTHORIZED
            )
        
        # Check cache first
        cache_key = f"user_areas_{my_user.id}"
        cached_data = cache.get(cache_key)
        
        if cached_data:
            return Response({"response": cached_data}, status=status.HTTP_200_OK)
        
        # Optimized query: use prefetch_related to avoid N+1
        areas = (
            my_user.area.all()
            .prefetch_related('geopoint_set')
            .select_related('kataster')
        )
        
        serializer = AreaSerializer(areas, many=True)
        response_data = serializer.data
        
        # Cache the result
        cache.set(cache_key, response_data, CACHE_TIMEOUT)
        
        return Response({"response": response_data}, status=status.HTTP_200_OK)

    def post(self, request):
        """Create new area with geospatial points."""
        my_user = get_user_from_request(request)
        if not my_user:
            return Response(
                {"error": "Unauthorized"},
                status=status.HTTP_401_UNAUTHORIZED
            )
        
        area_name = request.data.get("name", "").strip()
        points = request.data.get("points", [])
        
        if not area_name:
            return Response(
                {"error": "Area name is required"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if not isinstance(points, list):
            return Response(
                {"error": "Points must be a list"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            # Get or create kataster
            kataster, _ = Kataster.objects.get_or_create(
                name=my_user.email,
                defaults={"country": "Unknown"}
            )
            
            # Create area
            area = Area.objects.create(name=area_name, kataster=kataster)
            my_user.area.add(area)
            
            # Bulk create geopoints for better performance
            geopoints = [
                GeoPoint(
                    area=area,
                    timestamp=point.get('timestamp', 0),
                    lon=point.get('lon', 0.0),
                    lat=point.get('lat', 0.0)
                )
                for point in points
            ]
            GeoPoint.objects.bulk_create(geopoints)
            
            # Clear user cache
            cache.delete(f"user_areas_{my_user.id}")
            
            serializer = AreaSerializer(area)
            return Response(
                {"response": serializer.data},
                status=status.HTTP_201_CREATED
            )
            
        except Exception as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    def delete(self, request):
        """Delete area and associated geopoints."""
        my_user = get_user_from_request(request)
        if not my_user:
            return Response(
                {"error": "Unauthorized"},
                status=status.HTTP_401_UNAUTHORIZED
            )
        
        area_name = request.data.get("name", "").strip()
        
        if not area_name:
            return Response(
                {"error": "Area name is required"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            area = Area.objects.get(name=area_name)
            
            # Check if user owns this area
            if area not in my_user.area.all():
                return Response(
                    {"error": "Area not found or unauthorized"},
                    status=status.HTTP_404_NOT_FOUND
                )
            
            # Delete geopoints and area
            GeoPoint.objects.filter(area=area).delete()
            my_user.area.remove(area)
            area.delete()
            
            # Clear cache
            cache.delete(f"user_areas_{my_user.id}")
            
            return Response(
                {"result": "Area deleted successfully"},
                status=status.HTTP_200_OK
            )
            
        except Area.DoesNotExist:
            return Response(
                {"error": "Area not found"},
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
