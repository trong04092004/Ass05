from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .models import Rating
from .serializers import RatingSerializer


class RatingListCreate(APIView):
    """POST /ratings/ - tao danh gia | GET /ratings/ - tat ca"""
    def get(self, request):
        qs = Rating.objects.all().order_by('-created_at')
        return Response(RatingSerializer(qs, many=True).data)

    def post(self, request):
        s = RatingSerializer(data=request.data)
        if s.is_valid():
            s.save()
            return Response(s.data, status=201)
        return Response(s.errors, status=400)


class RatingList(APIView):
    """GET /ratings/list/?book_id=X - danh gia theo sach"""
    def get(self, request):
        book_id = request.query_params.get('book_id')
        qs = Rating.objects.filter(book_id=book_id).order_by('-created_at') if book_id else Rating.objects.none()
        return Response(RatingSerializer(qs, many=True).data)
