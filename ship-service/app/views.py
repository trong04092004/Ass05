from rest_framework.views import APIView
from rest_framework.response import Response
from .models import Shipping
from .serializers import ShippingSerializer


class ShippingListCreate(APIView):
    def get(self, request):
        return Response(ShippingSerializer(Shipping.objects.all().order_by('-created_at'), many=True).data)
    def post(self, request):
        s = ShippingSerializer(data=request.data)
        if s.is_valid():
            s.save()
            return Response(s.data, status=201)
        return Response(s.errors, status=400)

class ShippingByOrder(APIView):
    def get(self, request, order_id):
        try:
            return Response(ShippingSerializer(Shipping.objects.get(order_id=order_id)).data)
        except Shipping.DoesNotExist:
            return Response({'error': 'Not found'}, status=404)
