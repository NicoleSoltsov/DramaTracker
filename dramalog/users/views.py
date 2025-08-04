from django.shortcuts import render

# Create your views here.
from rest_framework import generics
from django.contrib.auth import get_user_model
from .serializers import UserSerializer
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.authtoken.models import Token
from django.contrib.auth import authenticate
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from tracker.models import WatchStatus
from dramas.models import Drama
from reviews.models import Review
from dramas.serializers import DramaSerializer
from reviews.serializers import ReviewSerializer
from tracker.serializers import WatchStatusSerializer

User = get_user_model()

class UserListCreateView(generics.ListCreateAPIView):
    queryset = User.objects.all()
    serializer_class = UserSerializer

class RegisterView(APIView):
    def post(self, request):
        username = request.data.get("username")
        password = request.data.get("password")

        if not username or not password:
            return Response({"error": "Username and password required"}, status=400)

        if User.objects.filter(username=username).exists():
            return Response({"error": "User already exists"}, status=400)

        user = User.objects.create_user(username=username, password=password)
        token, _ = Token.objects.get_or_create(user=user)
        return Response({"token": token.key}, status=201)

class LoginView(APIView):
    def post(self, request):
        username = request.data.get("username")
        password = request.data.get("password")

        user = authenticate(username=username, password=password)
        if not user:
            return Response({"error": "Invalid credentials"}, status=401)

        token, _ = Token.objects.get_or_create(user=user)
        return Response({"token": token.key})

class LogoutView(APIView):
    def post(self, request):
        request.auth.delete()  # deletes the token
        return Response(status=204)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def dashboard_view(request):
    user = request.user

    user_dramas = Drama.objects.filter(user=user)
    user_reviews = Review.objects.filter(user=user)
    user_trackers = WatchStatus.objects.filter(user=user)

    dramas_data = DramaSerializer(user_dramas, many=True).data
    reviews_data = ReviewSerializer(user_reviews, many=True).data
    trackers_data = WatchStatusSerializer(user_trackers, many=True).data

    return Response({
        "user": {
            "username": user.username,
            "email": user.email
        },
        "added_dramas": dramas_data,
        "reviews": reviews_data,
        "tracked_dramas": trackers_data
    })