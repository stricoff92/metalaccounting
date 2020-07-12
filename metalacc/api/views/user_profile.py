
from rest_framework import status, viewsets, mixins, serializers
from rest_framework.permissions import IsAuthenticated

from api.models import UserProfile



class UserProfileSerializer(serializers.ModelSerializer):

    slug = serializers.ReadOnlyField()
    object_limit_companies = serializers.ReadOnlyField()
    object_limit_periods_per_company = serializers.ReadOnlyField()
    object_limit_entries_per_period = serializers.ReadOnlyField()

    class Meta:
        model = UserProfile
        fields = (
            "slug",
            "use_nightmode",
            "object_limit_companies",
            "object_limit_periods_per_company",
            "object_limit_entries_per_period",
        )


class UserProfileViewSet(viewsets.GenericViewSet,
                        mixins.UpdateModelMixin):
    
    queryset = UserProfile.objects.all()
    lookup_field = 'slug'
    permission_classes = (IsAuthenticated,)
    serializer_class = UserProfileSerializer

    def get_queryset(self):
        return super().get_queryset().filter(user=self.request.user)
