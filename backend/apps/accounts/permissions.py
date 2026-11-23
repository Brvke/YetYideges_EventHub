from rest_framework.permissions import BasePermission


class IsVenueOwner(BasePermission):
    """User has the 'owner' role (can list venues and manage bookings)."""

    message = "Only venue owners can do this. Switch your account to a host account first."

    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and request.user.is_owner)
