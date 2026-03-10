from rest_framework import viewsets
from .models import Staff
from .models import StaffPermission
from .serializers import StaffSerializer, StaffPermissionSerializer

class StaffViewSet(viewsets.ModelViewSet):
    queryset = Staff.objects.all()
    serializer_class = StaffSerializer

class StaffPermissionViewSet(viewsets.ModelViewSet):
    queryset = StaffPermission.objects.all()
    serializer_class = StaffPermissionSerializer

