from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.contrib.auth.models import User
from django.contrib.auth import authenticate
from rest_framework.authtoken.models import Token
from .models import Customer, Address
from .serializers import CustomerSerializer, AddressSerializer
import requests
import os

CART_SERVICE_URL = os.environ.get('CART_SERVICE_URL', 'http://localhost:18003')


class Register(APIView):
    """
    POST /auth/register/
    Body: { name, email, password, role? }
    Returns: { token, customer_id, role, name, email }
    """
    def post(self, request):
        name = request.data.get('name', '').strip()
        email = request.data.get('email', '').strip()
        password = request.data.get('password', '')
        role = request.data.get('role', 'customer')

        if not name or not email or not password:
            return Response(
                {'error': 'name, email và password là bắt buộc'},
                status=status.HTTP_400_BAD_REQUEST
            )

        if User.objects.filter(username=email).exists():
            return Response(
                {'error': 'Email đã được đăng ký'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Tạo Django User
        user = User.objects.create_user(
            username=email, email=email, password=password
        )
        # Nếu là staff/manager, đặt is_staff=True trong Django User
        if role in ('staff', 'manager'):
            user.is_staff = True
            if role == 'manager':
                user.is_superuser = True
            user.save()

        # Tạo Customer profile
        customer = Customer.objects.create(
            user=user, name=name, email=email, role=role
        )

        # Auto tạo giỏ hàng (chỉ với customer)
        cart_id = None
        if role == 'customer':
            try:
                cart_resp = requests.post(
                    f"{CART_SERVICE_URL}/carts/",
                    json={"customer_id": customer.id},
                    timeout=5
                )
                if cart_resp.status_code in (200, 201):
                    cart_id = cart_resp.json().get("id")
            except requests.exceptions.RequestException as e:
                print(f"[customer-service] Warning: could not create cart: {e}")

        token, _ = Token.objects.get_or_create(user=user)
        return Response({
            'token': token.key,
            'customer_id': customer.id,
            'cart_id': cart_id,
            'name': name,
            'email': email,
            'role': role,
        }, status=status.HTTP_201_CREATED)


class Login(APIView):
    """
    POST /auth/login/
    Body: { email, password }
    Returns: { token, customer_id, name, email, role }
    """
    def post(self, request):
        email = request.data.get('email', '').strip()
        password = request.data.get('password', '')

        if not email or not password:
            return Response(
                {'error': 'email và password là bắt buộc'},
                status=status.HTTP_400_BAD_REQUEST
            )

        user = authenticate(username=email, password=password)
        if not user:
            return Response(
                {'error': 'Email hoặc mật khẩu không đúng'},
                status=status.HTTP_401_UNAUTHORIZED
            )

        customer = Customer.objects.filter(user=user).first()
        token, _ = Token.objects.get_or_create(user=user)

        return Response({
            'token': token.key,
            'customer_id': customer.id if customer else None,
            'name': customer.name if customer else user.get_full_name(),
            'email': email,
            'role': customer.role if customer else 'customer',
        }, status=status.HTTP_200_OK)


class CustomerListCreate(APIView):
    """GET /customers/ - danh sách | POST /customers/ - tạo mới"""
    def get(self, request):
        role_filter = request.query_params.get('role')
        qs = Customer.objects.all()
        if role_filter:
            qs = qs.filter(role=role_filter)
        serializer = CustomerSerializer(qs, many=True)
        return Response(serializer.data)

    def post(self, request):
        serializer = CustomerSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class CustomerDetail(APIView):
    """GET/PUT /customers/<id>/"""
    def _get(self, pk):
        try:
            return Customer.objects.get(pk=pk)
        except Customer.DoesNotExist:
            return None

    def get(self, request, pk):
        c = self._get(pk)
        if not c:
            return Response({'error': 'Not found'}, status=404)
        return Response(CustomerSerializer(c).data)

    def put(self, request, pk):
        c = self._get(pk)
        if not c:
            return Response({'error': 'Not found'}, status=404)
        serializer = CustomerSerializer(c, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=400)


class AddressListCreate(APIView):
    """GET /customers/<customer_id>/addresses/ | POST"""
    def get(self, request, customer_id):
        addresses = Address.objects.filter(customer_id=customer_id)
        return Response(AddressSerializer(addresses, many=True).data)

    def post(self, request, customer_id):
        data = {**request.data, 'customer': customer_id}
        serializer = AddressSerializer(data=data)
        if serializer.is_valid():
            # Nếu is_default=True, bỏ default ở địa chỉ khác
            if data.get('is_default'):
                Address.objects.filter(customer_id=customer_id).update(is_default=False)
            serializer.save()
            return Response(serializer.data, status=201)
        return Response(serializer.errors, status=400)