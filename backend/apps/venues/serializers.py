from rest_framework import serializers

from .models import Amenity, BlockedDate, EventType, Venue, VenuePhoto


class EventTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = EventType
        fields = ["slug", "name"]


class AmenitySerializer(serializers.ModelSerializer):
    class Meta:
        model = Amenity
        fields = ["slug", "name"]


class VenuePhotoSerializer(serializers.ModelSerializer):
    class Meta:
        model = VenuePhoto
        fields = ["id", "image", "caption", "order", "width", "height"]
        read_only_fields = ["id", "width", "height"]


class VenueListSerializer(serializers.ModelSerializer):
    cover_photo = serializers.SerializerMethodField()
    event_types = EventTypeSerializer(many=True, read_only=True)

    class Meta:
        model = Venue
        fields = [
            "id", "slug", "name", "tagline", "city", "area",
            "capacity_min", "capacity_max", "price_per_day",
            "rating_avg", "rating_count", "latitude", "longitude",
            "cover_photo", "event_types",
        ]

    def get_cover_photo(self, venue):
        # photos are prefetched, so use the cache instead of a new query
        photos = list(venue.photos.all())
        if not photos:
            return None
        request = self.context.get("request")
        url = photos[0].image.url
        return request.build_absolute_uri(url) if request else url


class VenueDetailSerializer(VenueListSerializer):
    photos = VenuePhotoSerializer(many=True, read_only=True)
    amenities = AmenitySerializer(many=True, read_only=True)
    owner_name = serializers.CharField(source="owner.get_full_name", read_only=True)

    class Meta(VenueListSerializer.Meta):
        fields = VenueListSerializer.Meta.fields + [
            "description", "address", "rental_policies", "amenities", "photos", "owner_name",
        ]


class VenueWriteSerializer(serializers.ModelSerializer):
    """Used by owners to create/update their own venues."""

    event_types = serializers.SlugRelatedField(
        slug_field="slug", queryset=EventType.objects.all(), many=True, required=False
    )
    amenities = serializers.SlugRelatedField(
        slug_field="slug", queryset=Amenity.objects.all(), many=True, required=False
    )
    photos = VenuePhotoSerializer(many=True, read_only=True)

    class Meta:
        model = Venue
        fields = [
            "id", "slug", "name", "tagline", "description", "city", "area", "address",
            "latitude", "longitude", "capacity_min", "capacity_max", "price_per_day",
            "event_types", "amenities", "rental_policies", "is_published",
            "rating_avg", "rating_count", "photos", "created_at",
        ]
        read_only_fields = ["id", "slug", "rating_avg", "rating_count", "created_at"]

    def validate(self, attrs):
        lo = attrs.get("capacity_min", getattr(self.instance, "capacity_min", 1))
        hi = attrs.get("capacity_max", getattr(self.instance, "capacity_max", None))
        if hi is not None and lo > hi:
            raise serializers.ValidationError(
                {"capacity_max": "Maximum capacity must be at least the minimum."}
            )
        return attrs


class BlockedDateSerializer(serializers.ModelSerializer):
    class Meta:
        model = BlockedDate
        fields = ["id", "venue", "date", "reason"]

    def validate_venue(self, venue):
        if venue.owner_id != self.context["request"].user.id:
            raise serializers.ValidationError("Not your venue.")
        return venue

    def validate(self, attrs):
        venue, date = attrs.get("venue"), attrs.get("date")
        if venue and date and venue.bookings.filter(event_date=date, status="accepted").exists():
            raise serializers.ValidationError(
                {"date": "There is a confirmed booking on this date."}
            )
        return attrs


class PhotoUploadSerializer(serializers.Serializer):
    venue = serializers.PrimaryKeyRelatedField(queryset=Venue.objects.all())
    images = serializers.ListField(child=serializers.ImageField(), allow_empty=False, max_length=20)

    def validate_venue(self, venue):
        if venue.owner_id != self.context["request"].user.id:
            raise serializers.ValidationError("Not your venue.")
        return venue
