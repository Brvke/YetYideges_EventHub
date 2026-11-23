from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework import serializers

from apps.venues.models import EventType, Venue

from .models import Booking


class BookingVenueSerializer(serializers.ModelSerializer):
    cover_photo = serializers.SerializerMethodField()

    class Meta:
        model = Venue
        fields = ["id", "slug", "name", "city", "area", "cover_photo"]

    def get_cover_photo(self, venue):
        photo = venue.photos.first()
        if not photo:
            return None
        request = self.context.get("request")
        return request.build_absolute_uri(photo.image.url) if request else photo.image.url


class BookingGuestSerializer(serializers.Serializer):
    name = serializers.CharField(source="get_full_name")
    email = serializers.EmailField()
    phone = serializers.CharField()


class BookingSerializer(serializers.ModelSerializer):
    venue = BookingVenueSerializer(read_only=True)
    guest = BookingGuestSerializer(read_only=True)
    event_type = serializers.SlugRelatedField(slug_field="slug", read_only=True)
    can_review = serializers.BooleanField(read_only=True)
    review_id = serializers.SerializerMethodField()

    class Meta:
        model = Booking
        fields = [
            "id", "venue", "guest", "event_date", "guest_count", "event_type", "message",
            "status", "owner_note", "quoted_price", "created_at", "responded_at",
            "can_review", "review_id",
        ]

    def get_review_id(self, booking):
        review = getattr(booking, "review", None)
        return review.id if review else None


class BookingCreateSerializer(serializers.ModelSerializer):
    venue = serializers.SlugRelatedField(
        slug_field="slug", queryset=Venue.objects.filter(is_published=True)
    )
    event_type = serializers.SlugRelatedField(
        slug_field="slug", queryset=EventType.objects.all(), required=False, allow_null=True
    )

    class Meta:
        model = Booking
        fields = ["id", "venue", "event_date", "guest_count", "event_type", "message"]

    def validate(self, attrs):
        user = self.context["request"].user
        venue = attrs["venue"]
        if venue.owner_id == user.id:
            raise serializers.ValidationError("You can't book your own venue.")
        if Booking.objects.filter(
            venue=venue, guest=user, event_date=attrs["event_date"], status__in=Booking.ACTIVE
        ).exists():
            raise serializers.ValidationError(
                {"event_date": "You already have a request for this date."}
            )
        booking = Booking(guest=user, quoted_price=venue.price_per_day, **attrs)
        try:
            booking.clean()
        except DjangoValidationError as exc:
            raise serializers.ValidationError(exc.message_dict)
        return attrs

    def create(self, validated_data):
        validated_data["quoted_price"] = validated_data["venue"].price_per_day
        return super().create(validated_data)

    def to_representation(self, instance):
        return BookingSerializer(instance, context=self.context).data


class OwnerDecisionSerializer(serializers.Serializer):
    note = serializers.CharField(max_length=300, required=False, allow_blank=True)
