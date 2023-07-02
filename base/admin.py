from django.contrib import admin
from .models import User, Topic, Room, Message
# Register your models here.

admin.site.register(User)
admin.site.register(Topic)
admin.site.register(Room)
admin.site.register(Message)
