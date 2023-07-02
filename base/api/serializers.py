from rest_framework.serializers import ModelSerializer #turns to JSON data
from base.models import Room

class RoomSerializer(ModelSerializer):
    class Meta:
        model = Room
        fields = '__all__'