from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .models import Payment
from .serializers import PaymentSerializer


class PaymentListCreate(APIView):
    """POST /payments/ | GET /payments/"""
    def get(self, request):
        qs = Payment.objects.all().order_by('-created_at')
        return Response(PaymentSerializer(qs, many=True).data)

    def post(self, request):
        s = PaymentSerializer(data=request.data)
        if s.is_valid():
            s.save()
            return Response(s.data, status=201)
        return Response(s.errors, status=400)


class PaymentByOrder(APIView):
    """GET /payments/order/<order_id>/"""
    def get(self, request, order_id):
        try:
            p = Payment.objects.get(order_id=order_id)
            return Response(PaymentSerializer(p).data)
        except Payment.DoesNotExist:
            return Response({'error': 'Not found'}, status=404)
