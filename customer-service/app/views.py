from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.decorators import api_view, permission_classes
from django.contrib.auth.models import User
from django.contrib.auth import authenticate
from django.conf import settings
from rest_framework_simplejwt.tokens import RefreshToken
from .models import Customer, Address
from .serializers import CustomerSerializer, AddressSerializer
import requests
import os
import hashlib
from .security import get_customer_id, is_admin

CART_SERVICE_URL = os.environ.get('CART_SERVICE_URL', 'http://localhost:18003')
ADMIN_ROLES = ('staff', 'manager')


def _issue_jwt_payload(user, customer, email, role):
    refresh = RefreshToken.for_user(user)
    refresh['role'] = role
    refresh['customer_id'] = customer.id
    access = refresh.access_token
    access['role'] = role
    access['customer_id'] = customer.id

    return {
        # Keep `token` for backward compatibility at gateway/UI layer.
        'token': str(access),
        'access': str(access),
        'refresh': str(refresh),
        'customer_id': customer.id,
        'name': customer.name,
        'email': email,
        'role': role,
    }


def _create_user_with_customer(name, email, password, role):
    # Tạo Django User
    user = User.objects.create_user(
        username=email, email=email, password=password
    )
    # Nếu là staff/manager, đặt is_staff=True trong Django User
    if role in ADMIN_ROLES:
        user.is_staff = True
        if role == 'manager':
            user.is_superuser = True
        user.save()

    # Tạo Customer profile
    customer = Customer.objects.create(
        user=user, name=name, email=email, role=role
    )
    return user, customer


def _create_cart_for_customer(customer_id):
    cart_id = None
    try:
        cart_resp = requests.post(
            f"{CART_SERVICE_URL}/carts/",
            json={"customer_id": customer_id},
            timeout=5
        )
        if cart_resp.status_code in (200, 201):
            cart_id = cart_resp.json().get("id")
    except requests.exceptions.RequestException as e:
        print(f"[customer-service] Warning: could not create cart: {e}")
    return cart_id


@api_view(['GET'])
@permission_classes([AllowAny])
def security_health(request):
    signing_key = settings.SIMPLE_JWT.get('SIGNING_KEY', '')
    fingerprint = hashlib.sha256(signing_key.encode()).hexdigest()[:12] if signing_key else ''
    auth_classes = settings.REST_FRAMEWORK.get('DEFAULT_AUTHENTICATION_CLASSES', [])
    return Response({
        'service': 'customer-service',
        'jwt_algorithm': settings.SIMPLE_JWT.get('ALGORITHM', 'HS256'),
        'auth_class': auth_classes[0] if auth_classes else '',
        'jwt_key_fingerprint': fingerprint,
    })


class Register(APIView):
    """
    POST /auth/register/
    Body: { name, email, password }
    Returns: { token, access, refresh, customer_id, role, name, email }
    """
    permission_classes = [AllowAny]

    def post(self, request):
        name = request.data.get('name', '').strip()
        email = request.data.get('email', '').strip()
        password = request.data.get('password', '')
        role = 'customer'

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

        user, customer = _create_user_with_customer(name, email, password, role)
        cart_id = _create_cart_for_customer(customer.id)

        payload = _issue_jwt_payload(user, customer, email, role)
        payload['cart_id'] = cart_id
        return Response(payload, status=status.HTTP_201_CREATED)


class AdminRegister(APIView):
    """
    POST /auth/admin/register/
    Body: { name, email, password, role(staff|manager) }
    Returns: { token, access, refresh, customer_id, role, name, email }
    """
    permission_classes = [AllowAny]

    def post(self, request):
        name = request.data.get('name', '').strip()
        email = request.data.get('email', '').strip()
        password = request.data.get('password', '')
        role = request.data.get('role', 'staff')

        if not name or not email or not password:
            return Response(
                {'error': 'name, email và password là bắt buộc'},
                status=status.HTTP_400_BAD_REQUEST
            )

        if role not in ADMIN_ROLES:
            return Response(
                {'error': 'role phải là staff hoặc manager'},
                status=status.HTTP_400_BAD_REQUEST
            )

        if User.objects.filter(username=email).exists():
            return Response(
                {'error': 'Email đã được đăng ký'},
                status=status.HTTP_400_BAD_REQUEST
            )

        user, customer = _create_user_with_customer(name, email, password, role)
        payload = _issue_jwt_payload(user, customer, email, role)
        payload['cart_id'] = None
        return Response(payload, status=status.HTTP_201_CREATED)


class Login(APIView):
    """
    POST /auth/login/
    Body: { email, password }
    Returns: { token, access, refresh, customer_id, name, email, role }
    """
    permission_classes = [AllowAny]

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
        role = customer.role if customer else 'customer'
        if role != 'customer':
            return Response(
                {'error': 'Tài khoản staff/manager vui lòng đăng nhập ở cổng admin'},
                status=status.HTTP_403_FORBIDDEN
            )

        return Response(
            _issue_jwt_payload(user, customer, email, role),
            status=status.HTTP_200_OK
        )


class AdminLogin(APIView):
    """
    POST /auth/admin/login/
    Body: { email, password }
    Returns: { token, access, refresh, customer_id, name, email, role }
    """
    permission_classes = [AllowAny]

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
        role = customer.role if customer else 'customer'
        if role not in ADMIN_ROLES:
            return Response(
                {'error': 'Tài khoản customer vui lòng đăng nhập ở cổng khách hàng'},
                status=status.HTTP_403_FORBIDDEN
            )

        return Response(
            _issue_jwt_payload(user, customer, email, role),
            status=status.HTTP_200_OK
        )


class CustomerListCreate(APIView):
    """GET /customers/ - danh sách | POST /customers/ - tạo mới"""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        if not is_admin(request):
            return Response({'error': 'Staff or manager role required'}, status=403)
        role_filter = request.query_params.get('role')
        qs = Customer.objects.all()
        if role_filter:
            qs = qs.filter(role=role_filter)
        serializer = CustomerSerializer(qs, many=True)
        return Response(serializer.data)

    def post(self, request):
        if not is_admin(request):
            return Response({'error': 'Staff or manager role required'}, status=403)
        serializer = CustomerSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class CustomerDetail(APIView):
    """GET/PUT /customers/<id>/"""
    permission_classes = [IsAuthenticated]

    def _get(self, pk):
        try:
            return Customer.objects.get(pk=pk)
        except Customer.DoesNotExist:
            return None

    def get(self, request, pk):
        c = self._get(pk)
        if not c:
            return Response({'error': 'Not found'}, status=404)
        if not is_admin(request) and get_customer_id(request) != str(pk):
            return Response({'error': 'Forbidden'}, status=403)
        return Response(CustomerSerializer(c).data)

    def put(self, request, pk):
        c = self._get(pk)
        if not c:
            return Response({'error': 'Not found'}, status=404)
        if not is_admin(request) and get_customer_id(request) != str(pk):
            return Response({'error': 'Forbidden'}, status=403)
        serializer = CustomerSerializer(c, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=400)


class AddressListCreate(APIView):
    """GET /customers/<customer_id>/addresses/ | POST"""
    permission_classes = [IsAuthenticated]

    def get(self, request, customer_id):
        if not is_admin(request) and get_customer_id(request) != str(customer_id):
            return Response({'error': 'Forbidden'}, status=403)
        addresses = Address.objects.filter(customer_id=customer_id)
        return Response(AddressSerializer(addresses, many=True).data)

    def post(self, request, customer_id):
        if not is_admin(request) and get_customer_id(request) != str(customer_id):
            return Response({'error': 'Forbidden'}, status=403)
        data = {**request.data, 'customer': customer_id}
        serializer = AddressSerializer(data=data)
        if serializer.is_valid():
            # Nếu is_default=True, bỏ default ở địa chỉ khác
            if data.get('is_default'):
                Address.objects.filter(customer_id=customer_id).update(is_default=False)
            serializer.save()
            return Response(serializer.data, status=201)
        return Response(serializer.errors, status=400)