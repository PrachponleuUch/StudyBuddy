from base.models import Room
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from .serializers import RoomSerializer
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework.permissions import IsAuthenticated, IsAdminUser # ADDED

# Customize token info

class MyTokenObtainPairSerializer(TokenObtainPairSerializer):
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)

        # Add custom claims
        token['username'] = user.username
        # ...

        return token

class MyTokenObtainPairView(TokenObtainPairView):
    serializer_class = MyTokenObtainPairSerializer

@api_view(['GET'])
def getRoutes(request):
    routes = [
        'GET /api',
        'GET /api/token', # For getting token
        'GET /api/token/refresh', # For refreshing token
        'GET /api/rooms',
        'GET /api/rooms/:id',
        'POST /api/create-room/',
        'POST /api/update-room/:id',
        'DELETE /api/delete-room/:id',
    ]
    return Response(routes) 

@api_view(['GET'])
@permission_classes([IsAuthenticated, IsAdminUser])
def getRooms(request):
    rooms = Room.objects.all()
    serializer = RoomSerializer(rooms, many=True)
    return Response(serializer.data)

@api_view(['GET'])
@permission_classes([IsAuthenticated, IsAdminUser])
def getRoom(request, pk):
    room = Room.objects.get(id=pk)
    serializer = RoomSerializer(room, many=False)
    return Response(serializer.data)

@api_view(['POST'])
@permission_classes([IsAdminUser])
def createRoom(request):
    serializer = RoomSerializer( data = request.data)
    if serializer.is_valid():
        serializer.save()
    return Response(serializer.data)

@api_view(['POST'])
@permission_classes([IsAdminUser])
def updateRoom(request, pk):
    room = Room.objects.get(id=pk)
    serializer = RoomSerializer(instance = room, data = request.data)
    if serializer.is_valid():
        serializer.save()
    return Response(serializer.data)

@api_view(['DELETE'])
@permission_classes([IsAdminUser])
def deleteRoom(request, pk):
    room = Room.objects.get(id=pk)
    room.delete()
    return Response('Item deleted successfully')