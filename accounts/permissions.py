from rest_framework import permissions


class IsOwnerOrReadOnly(permissions.BasePermission):
    """
    Custom permission: only the owner of an object can edit it.
    
    Read permissions are allowed for any authenticated request.
    Write permissions require the requesting user to match the
    object's owner, identified by a `usuario` or `user` attribute.
    """

    def has_object_permission(self, request, view, obj):
        # Read permissions are granted to any authenticated request
        if request.method in permissions.SAFE_METHODS:
            return True

        # Write permissions: only the owner
        owner = getattr(obj, 'usuario', None) or getattr(obj, 'user', None)
        return owner == request.user
