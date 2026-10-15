from rest_framework.permissions import BasePermission


class HasMatterAccess(BasePermission):
    def has_object_permission(self, request, view, obj):
        user = request.user
        if user.role == user.Role.SUPER_ADMIN:
            return True
        if user.role == user.Role.INTERNAL_ASSOCIATE:
            return obj.assignments.filter(associate=user).exists()
        if user.role == user.Role.CLIENT:
            return obj.client == user
        return False