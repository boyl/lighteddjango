from rest_framework import viewsets, authentication, permissions, filters
from rest_framework.pagination import PageNumberPagination
from django.contrib.auth import get_user_model
import django_filters
from django_filters.rest_framework import DjangoFilterBackend

from .models import Sprint, Task
from .serializers import SprintSerializer, TaskSerializer, UserSerializer

# Create your views here.

User = get_user_model()


class NullFilter(django_filters.BooleanFilter):
    """Filter on a field set as null or not."""

    def filter(self, qs, value):
        if value is not None:
            return qs.filter(**{'%s__isnull' % self.field_name: value})
        return qs


class TaskFilter(django_filters.FilterSet):

    backlog = NullFilter(field_name='sprint')

    class Meta:
        model = Task
        fields = ('sprint', 'status', 'assigned', 'backlog',)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.filters['assigned'].extra.update({'to_field_name': User.USERNAME_FIELD})


class SprintFilter(django_filters.FilterSet):

    end_min = django_filters.DateFilter(field_name='end', lookup_expr='gte')
    end_max = django_filters.DateFilter(field_name='end', lookup_expr='lte')

    class Meta:
        model = Sprint
        fields = ('end_min', 'end_max',)


class StandardResultsSetPagination(PageNumberPagination):
    """
    Setting pagination for standard results.
    """
    page_size = 25
    page_size_query_param = 'page_size'
    max_page_size = 100


class DefaultsMixin(object):
    """
    Default settings for view authentication, permissions,
    filtering and pagination.
    """

    authentication_classes = (
        authentication.BasicAuthentication,
        authentication.TokenAuthentication,
        # authentication.SessionAuthentication,
    )
    permission_classes = (
        permissions.IsAuthenticated,
    )
    pagination_class = StandardResultsSetPagination
    filter_backends = (
        filters.SearchFilter,
        filters.OrderingFilter,
        DjangoFilterBackend,
    )


class SprintViewSet(DefaultsMixin, viewsets.ModelViewSet):
    """API endpoint for listing and creating sprints."""

    queryset = Sprint.objects.order_by('end')
    serializer_class = SprintSerializer
    filter_class = SprintFilter
    search_fields = ('name',)
    ordering_fields = ('end', 'name', )


class TaskViewSet(DefaultsMixin, viewsets.ModelViewSet):
    """API endpoint for listing and creating tasks."""

    queryset = Task.objects.all()
    serializer_class = TaskSerializer
    filter_class = TaskFilter
    search_fields = ('name', 'description',)
    ordering_fields = ('name', 'order', 'started', 'due', 'completed',)


class UserViewSet(DefaultsMixin, viewsets.ReadOnlyModelViewSet):
    """API endpoint for listing users."""

    lookup_field = User.USERNAME_FIELD
    queryset = User.objects.order_by(User.USERNAME_FIELD)
    serializer_class = UserSerializer
    search_fields = (User.USERNAME_FIELD,)
