from rest_framework.permissions import BasePermission


class IsAdmin(BasePermission):
    def has_permission(self, request, view):
        user = getattr(request, 'user', None)
        return bool(getattr(user, 'is_authenticated', False) and getattr(user, 'role', None) == 'admin')
