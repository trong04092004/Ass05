from rest_framework.permissions import BasePermission, SAFE_METHODS

ADMIN_ROLES = ('staff', 'manager')


def _token_payload(request):
    token = request.auth
    if hasattr(token, 'payload'):
        return token.payload
    if isinstance(token, dict):
        return token
    return {}


def get_role(request):
    return _token_payload(request).get('role')


def get_customer_id(request):
    customer_id = _token_payload(request).get('customer_id')
    return str(customer_id) if customer_id is not None else None


def is_admin(request):
    return get_role(request) in ADMIN_ROLES


def is_customer(request):
    return get_role(request) == 'customer'


def is_owner_or_admin(request, owner_customer_id):
    return is_admin(request) or get_customer_id(request) == str(owner_customer_id)


class IsStaffManager(BasePermission):
    def has_permission(self, request, view):
        return is_admin(request)


class IsStaffManagerOrReadOnly(BasePermission):
    def has_permission(self, request, view):
        if request.method in SAFE_METHODS:
            return True
        return is_admin(request)


class IsCustomer(BasePermission):
    def has_permission(self, request, view):
        return is_customer(request)