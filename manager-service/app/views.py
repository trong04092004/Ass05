from rest_framework.views import APIView
from rest_framework.response import Response
from .models import Promotion, SupplyOrder
from .serializers import PromotionSerializer, SupplyOrderSerializer


class PromotionListCreate(APIView):
    def get(self, request):
        return Response(PromotionSerializer(Promotion.objects.all().order_by('-created_at'), many=True).data)
    def post(self, request):
        s = PromotionSerializer(data=request.data)
        if s.is_valid():
            s.save()
            return Response(s.data, status=201)
        return Response(s.errors, status=400)


class SupplyOrderListCreate(APIView):
    def get(self, request):
        return Response(SupplyOrderSerializer(SupplyOrder.objects.all().order_by('-created_at'), many=True).data)
    def post(self, request):
        s = SupplyOrderSerializer(data=request.data)
        if s.is_valid():
            s.save()
            return Response(s.data, status=201)
        return Response(s.errors, status=400)
