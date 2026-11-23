from rest_framework import serializers

from apps.bookings.models import Booking

from .models import Review


class ReviewSerializer(serializers.ModelSerializer):
    author_name = serializers.SerializerMethodField()
    venue = serializers.SlugRelatedField(slug_field="slug", read_only=True)
    booking = serializers.PrimaryKeyRelatedField(queryset=Booking.objects.all())
    event_date = serializers.DateField(source="booking.event_date", read_only=True)

    class Meta:
        model = Review
        fields = [
            "id", "booking", "venue", "author_name", "rating", "comment",
            "owner_reply", "event_date", "created_at",
        ]
        read_only_fields = ["id", "venue", "owner_reply", "created_at"]

    def get_author_name(self, review):
        # Show "Abebe K." rather than full names publicly.
        u = review.author
        if not u.first_name:
            return u.email.split("@")[0]
        return f"{u.first_name} {u.last_name[0]}." if u.last_name else u.first_name

    def validate_booking(self, booking):
        if self.instance:  # booking can't be changed on edit
            return self.instance.booking
        if booking.guest_id != self.context["request"].user.id:
            raise serializers.ValidationError("You can only review your own bookings.")
        if not booking.can_review:
            raise serializers.ValidationError(
                "You can review a venue after your confirmed event has taken place."
            )
        return booking

    def create(self, validated_data):
        booking = validated_data["booking"]
        return Review.objects.create(venue=booking.venue, author=booking.guest, **validated_data)


class OwnerReplySerializer(serializers.Serializer):
    owner_reply = serializers.CharField(max_length=2000, allow_blank=True)
