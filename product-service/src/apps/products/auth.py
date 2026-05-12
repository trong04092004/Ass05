import jwt
from rest_framework.authentication import BaseAuthentication


class MockUser:
    def __init__(self, user_id, username, role):
        self.id = user_id
        self.username = username
        self.role = role
        self.is_authenticated = True


class MockJWTAuthentication(BaseAuthentication):
    def authenticate(self, request):
        auth_header = request.META.get('HTTP_AUTHORIZATION', '')
        if not auth_header.startswith('Bearer '):
            return None
        token = auth_header.split(' ')[1]

        if token == 'admin-token':
            return (MockUser('admin', 'admin', 'admin'), None)
        elif token == 'user-token':
            return (MockUser('user1', 'user1', 'user'), None)

        try:
            payload = jwt.decode(token, options={"verify_signature": False})
            user_id = payload.get('user_id', payload.get('sub', 'unknown'))
            username = payload.get('username', 'user')
            role = payload.get('role', 'user')
            return (MockUser(user_id, username, role), None)
        except Exception:
            return None
