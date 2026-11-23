from django.shortcuts import get_object_or_404
from drf_spectacular.utils import extend_schema
from rest_framework import generics, mixins, permissions, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from apps.accounts.permissions import IsVenueOwner
from apps.venues.models import Venue

from .models import Review
from .serializers import OwnerReplySerializer, ReviewSerializer


class VenueReviewList(generics.ListAPIView):
    """Public reviews for one venue: /api/venues/<slug>/reviews/"""

    serializer_class = ReviewSerializer
    permission_classes = [permissions.AllowAny]
    ordering_fields = ["created_at", "rating"]

    def get_queryset(self):
        venue = get_object_or_404(Venue, slug=self.kwargs["slug"], is_published=True)
        return venue.reviews.select_related("author", "booking", "venue")


class MyReviewViewSet(
    mixins.CreateModelMixin,
    mixins.ListModelMixin,
    mixins.UpdateModelMixin,
    mixins.DestroyModelMixin,
    viewsets.GenericViewSet,
):
    """Reviews written by the signed-in guest."""

    serializer_class = ReviewSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Review.objects.filter(author=self.request.user).select_related("author", "booking", "venue")


class OwnerReviewViewSet(mixins.ListModelMixin, viewsets.GenericViewSet):
    """Reviews on the owner's venues, with the ability to reply publicly."""

    serializer_class = ReviewSerializer
    permission_classes = [IsVenueOwner]
    filterset_fields = ["venue"]

    def get_queryset(self):
        return Review.objects.filter(venue__owner=self.request.user).select_related(
            "author", "booking", "venue"
        )

    @extend_schema(request=OwnerReplySerializer)
    @action(detail=True, methods=["post"])
    def reply(self, request, pk=None):
        review = self.get_object()
        data = OwnerReplySerializer(data=request.data)
        data.is_valid(raise_exception=True)
        review.owner_reply = data.validated_data["owner_reply"]
        review.save(update_fields=["owner_reply", "updated_at"])
        return Response(ReviewSerializer(review, context={"request": request}).data)
