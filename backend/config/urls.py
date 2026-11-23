from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from apps.accounts.views import MeView, RegisterView
from apps.bookings.views import GuestBookingViewSet, OwnerBookingViewSet, OwnerStatsView
from apps.reviews.views import MyReviewViewSet, OwnerReviewViewSet, VenueReviewList
from apps.venues.views import (
    AmenityList,
    CityList,
    EventTypeList,
    OwnerBlockedDateViewSet,
    OwnerPhotoViewSet,
    OwnerVenueViewSet,
    VenueViewSet,
)

router = DefaultRouter()
router.register("venues", VenueViewSet, basename="venue")
router.register("bookings", GuestBookingViewSet, basename="booking")
router.register("reviews", MyReviewViewSet, basename="review")
router.register("owner/venues", OwnerVenueViewSet, basename="owner-venue")
router.register("owner/photos", OwnerPhotoViewSet, basename="owner-photo")
router.register("owner/blocked-dates", OwnerBlockedDateViewSet, basename="owner-blocked-date")
router.register("owner/bookings", OwnerBookingViewSet, basename="owner-booking")
router.register("owner/reviews", OwnerReviewViewSet, basename="owner-review")

api = [
    path("auth/register/", RegisterView.as_view(), name="register"),
    path("auth/token/", TokenObtainPairView.as_view(), name="token"),
    path("auth/token/refresh/", TokenRefreshView.as_view(), name="token-refresh"),
    path("auth/me/", MeView.as_view(), name="me"),
    path("event-types/", EventTypeList.as_view(), name="event-types"),
    path("amenities/", AmenityList.as_view(), name="amenities"),
    path("cities/", CityList.as_view(), name="cities"),
    path("venues/<slug:slug>/reviews/", VenueReviewList.as_view(), name="venue-reviews"),
    path("owner/stats/", OwnerStatsView.as_view(), name="owner-stats"),
    path("", include(router.urls)),
    path("schema/", SpectacularAPIView.as_view(), name="schema"),
    path("docs/", SpectacularSwaggerView.as_view(url_name="schema"), name="docs"),
]

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/", include(api)),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
