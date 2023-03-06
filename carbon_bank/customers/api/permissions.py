from rest_framework.permissions import BasePermission


class IsOwner(BasePermission):
    def has_permission(self, request, view):
        # her tetiklendiğinde çalışır, önceliklidir.
        # this has priority. this run every trigger.
        return request.user and request.user.is_authenticated

    message = "You must be the owner of this object"

    def has_object_permission(self, request, view, obj):
        # sadece delete işlemi yapıldığında çalışır
        # this is called just in delete process
        return obj.owner.user == request.user
