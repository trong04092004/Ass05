from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.decorators import api_view, permission_classes
from django.contrib.auth.models import User
from django.contrib.auth import authenticate
from django.conf import settings
from rest_framework_simplejwt.tokens import RefreshToken
from .models import Customer
import requests
import os
import hashlib

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
        'token': str(access),
        'access': str(access),
        'refresh': str(refresh),
        'customer_id': customer.id,
        'name': customer.name,
        'email': email,
        'role': role,
    }


def _create_user_with_customer(name, email, password, role):
    user = User.objects.create_user(username=email, email=email, password=password)
    if role in ADMIN_ROLES:
        user.is_staff = True
        if role == 'manager':
            user.is_superuser = True
        user.save()

    customer = Customer.objects.create(user=user, name=name, email=email, role=role)
    return user, customer


def _create_cart_for_customer(customer_id):
    cart_id = None
    try:
        cart_resp = requests.post(
            f"{CART_SERVICE_URL}/carts/",
            json={"customer_id": customer_id},
            timeout=5,
        )
        if cart_resp.status_code in (200, 201):
            cart_id = cart_resp.json().get('id')
    except requests.exceptions.RequestException as exc:
        print(f"[auth-service] Warning: could not create cart: {exc}")
    return cart_id


@api_view(['GET'])
@permission_classes([AllowAny])
def security_health(request):
    signing_key = settings.SIMPLE_JWT.get('SIGNING_KEY', '')
    fingerprint = hashlib.sha256(signing_key.encode()).hexdigest()[:12] if signing_key else ''
    auth_classes = settings.REST_FRAMEWORK.get('DEFAULT_AUTHENTICATION_CLASSES', [])
    return Response({
        'service': 'auth-service',
        'jwt_algorithm': settings.SIMPLE_JWT.get('ALGORITHM', 'HS256'),
        'auth_class': auth_classes[0] if auth_classes else '',
        'jwt_key_fingerprint': fingerprint,
    })


class Register(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        name = request.data.get('name', '').strip()
        email = request.data.get('email', '').strip()
        password = request.data.get('password', '')
        role = 'customer'

        if not name or not email or not password:
            return Response(
                {'error': 'name, email va password la bat buoc'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if User.objects.filter(username=email).exists():
            return Response({'error': 'Email da duoc dang ky'}, status=status.HTTP_400_BAD_REQUEST)

        user, customer = _create_user_with_customer(name, email, password, role)
        cart_id = _create_cart_for_customer(customer.id)

        payload = _issue_jwt_payload(user, customer, email, role)
        payload['cart_id'] = cart_id
        return Response(payload, status=status.HTTP_201_CREATED)


class AdminRegister(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        name = request.data.get('name', '').strip()
        email = request.data.get('email', '').strip()
        password = request.data.get('password', '')
        role = request.data.get('role', 'staff')

        if not name or not email or not password:
            return Response(
                {'error': 'name, email va password la bat buoc'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if role not in ADMIN_ROLES:
            return Response({'error': 'role phai la staff hoac manager'}, status=status.HTTP_400_BAD_REQUEST)

        if User.objects.filter(username=email).exists():
            return Response({'error': 'Email da duoc dang ky'}, status=status.HTTP_400_BAD_REQUEST)

        user, customer = _create_user_with_customer(name, email, password, role)
        payload = _issue_jwt_payload(user, customer, email, role)
        payload['cart_id'] = None
        return Response(payload, status=status.HTTP_201_CREATED)


class Login(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        email = request.data.get('email', '').strip()
        password = request.data.get('password', '')

        if not email or not password:
            return Response(
                {'error': 'email va password la bat buoc'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        user = authenticate(username=email, password=password)
        if not user:
            return Response({'error': 'Email hoac mat khau khong dung'}, status=status.HTTP_401_UNAUTHORIZED)

        customer = Customer.objects.filter(user=user).first()
        role = customer.role if customer else 'customer'
        if role != 'customer':
            return Response(
                {'error': 'Tai khoan staff/manager vui long dang nhap o cong admin'},
                status=status.HTTP_403_FORBIDDEN,
            )

        return Response(_issue_jwt_payload(user, customer, email, role), status=status.HTTP_200_OK)


class AdminLogin(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        email = request.data.get('email', '').strip()
        password = request.data.get('password', '')

        if not email or not password:
            return Response(
                {'error': 'email va password la bat buoc'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        user = authenticate(username=email, password=password)
        if not user:
            return Response({'error': 'Email hoac mat khau khong dung'}, status=status.HTTP_401_UNAUTHORIZED)

        customer = Customer.objects.filter(user=user).first()
        role = customer.role if customer else 'customer'
        if role not in ADMIN_ROLES:
            return Response(
                {'error': 'Tai khoan customer vui long dang nhap o cong khach hang'},
                status=status.HTTP_403_FORBIDDEN,
            )

        return Response(_issue_jwt_payload(user, customer, email, role), status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes([AllowAny])
def logout(request):
    # Stateless JWT service: accept logout request for compatibility.
    # Gateway is responsible for clearing session and browser cookies.
    return Response({'success': True, 'message': 'Logged out'}, status=status.HTTP_200_OK)
