from django.db.models import Q
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from .models import Product, Rating
from .serializers import ProductSerializer, ProductCreateSerializer, ProductUpdateSerializer, RatingSerializer, RatingCreateSerializer
from .auth import MockJWTAuthentication
from .permissions import IsAdmin
from .ai_client import rag_recommend


class HealthView(APIView):
    permission_classes = []

    def get(self, request):
        return Response({'status': 'ok'})


class ProductsListCreateView(APIView):
    def get(self, request):
        qs = Product.objects.all().order_by('-id')

        category = request.query_params.get('category')
        min_price = request.query_params.get('min_price')
        max_price = request.query_params.get('max_price')
        if category:
            try:
                cid = int(category)
                qs = qs.filter(category__id=cid)
            except Exception:
                qs = qs.filter(category__name__iexact=category)
        if min_price:
            try:
                qs = qs.filter(price__gte=float(min_price))
            except ValueError:
                pass
        if max_price:
            try:
                qs = qs.filter(price__lte=float(max_price))
            except ValueError:
                pass

        # Return direct array for consistency with legacy endpoints
        serializer = ProductSerializer(qs, many=True)
        return Response(serializer.data)

    def post(self, request):
        auth = MockJWTAuthentication()
        user_auth = auth.authenticate(request)
        if user_auth is None:
            return Response({'detail': 'Authentication credentials were not provided.'}, status=status.HTTP_401_UNAUTHORIZED)
        request.user = user_auth[0]
        perm = IsAdmin()
        if not perm.has_permission(request, self):
            return Response({'detail': 'You do not have permission to perform this action.'}, status=status.HTTP_403_FORBIDDEN)

        serializer = ProductCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        product = serializer.save()
        return Response(ProductSerializer(product).data, status=status.HTTP_201_CREATED)


class ProductDetailView(APIView):
    def get_object(self, id):
        try:
            return Product.objects.get(id=id)
        except Product.DoesNotExist:
            return None

    def get(self, request, id):
        p = self.get_object(id)
        if not p:
            return Response(status=status.HTTP_404_NOT_FOUND)
        data = ProductSerializer(p).data

        try:
            query = f"{p.name} {p.description}"
            recommendations = rag_recommend(query)
            data['recommendations'] = recommendations
        except Exception:
            pass

        return Response(data)

    def put(self, request, id):
        auth = MockJWTAuthentication()
        user_auth = auth.authenticate(request)
        if user_auth is None:
            return Response({'detail': 'Authentication credentials were not provided.'}, status=status.HTTP_401_UNAUTHORIZED)
        request.user = user_auth[0]
        perm = IsAdmin()
        if not perm.has_permission(request, self):
            return Response({'detail': 'You do not have permission to perform this action.'}, status=status.HTTP_403_FORBIDDEN)

        p = self.get_object(id)
        if not p:
            return Response(status=status.HTTP_404_NOT_FOUND)
        serializer = ProductUpdateSerializer(p, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        product = serializer.save()
        return Response(ProductSerializer(product).data)

    def delete(self, request, id):
        auth = MockJWTAuthentication()
        user_auth = auth.authenticate(request)
        if user_auth is None:
            return Response({'detail': 'Authentication credentials were not provided.'}, status=status.HTTP_401_UNAUTHORIZED)
        request.user = user_auth[0]
        perm = IsAdmin()
        if not perm.has_permission(request, self):
            return Response({'detail': 'You do not have permission to perform this action.'}, status=status.HTTP_403_FORBIDDEN)

        p = self.get_object(id)
        if not p:
            return Response(status=status.HTTP_404_NOT_FOUND)
        p.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class ProductSearchView(APIView):
    def get(self, request):
        q = request.query_params.get('q', '')
        if not q:
            return Response({'items': [], 'total': 0})

        qs = Product.objects.filter(
            Q(name__icontains=q) | Q(description__icontains=q)
        ).order_by('-id')

        try:
            page = int(request.query_params.get('page', 1))
            if page < 1:
                page = 1
        except ValueError:
            page = 1
        try:
            limit = int(request.query_params.get('limit', 10))
            if limit < 1:
                limit = 10
        except ValueError:
            limit = 10

        total = qs.count()
        start = (page - 1) * limit
        end = start + limit
        items = qs[start:end]
        serializer = ProductSerializer(items, many=True)
        return Response({'items': serializer.data, 'page': page, 'limit': limit, 'total': total})


class ProductSuggestView(APIView):
    def get(self, request):
        q = request.query_params.get('q', '')
        try:
            recommendations = rag_recommend(q)
            return Response({'recommendations': recommendations})
        except Exception:
            return Response({'recommendations': []})


# ============================================================
# Rating Views (replaces comment-service)
# ============================================================

class RatingsListCreateView(APIView):
    """GET /ratings/ - list ratings for a product, POST /ratings/ - create rating"""
    permission_classes = []

    def get(self, request):
        product_id = request.query_params.get('product_id')
        if not product_id:
            return Response({'error': 'product_id is required'}, status=400)
        try:
            product_id = int(product_id)
        except ValueError:
            return Response({'error': 'Invalid product_id'}, status=400)

        ratings = Rating.objects.filter(product_id=product_id).order_by('-created_at')
        return Response(RatingSerializer(ratings, many=True).data)

    def post(self, request):
        serializer = RatingCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        # Check if rating already exists
        existing = Rating.objects.filter(
            customer_id=data['customer_id'],
            product_id=data['product_id']
        ).first()
        if existing:
            existing.rating = data['rating']
            existing.comment = data.get('comment', '')
            existing.save()
            return Response(RatingSerializer(existing).data)

        rating = Rating.objects.create(
            customer_id=data['customer_id'],
            product_id=data['product_id'],
            rating=data['rating'],
            comment=data.get('comment', '')
        )
        return Response(RatingSerializer(rating).data, status=201)


class RatingDetailView(APIView):
    """GET/PUT/DELETE /ratings/<id>/"""
    permission_classes = []

    def get_object(self, pk):
        try:
            return Rating.objects.get(pk=pk)
        except Rating.DoesNotExist:
            return None

    def get(self, request, pk):
        r = self.get_object(pk)
        if not r:
            return Response(status=404)
        return Response(RatingSerializer(r).data)

    def put(self, request, pk):
        r = self.get_object(pk)
        if not r:
            return Response(status=404)
        serializer = RatingSerializer(r, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(RatingSerializer(r).data)

    def delete(self, request, pk):
        r = self.get_object(pk)
        if not r:
            return Response(status=404)
        r.delete()
        return Response(status=204)
